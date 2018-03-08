using System;
using Grpc.Core;
using Grpc.Core.Interceptors;
using GrpcOpenTracing.Propagation;
using GrpcOpenTracing.Streaming;
using OpenTracing;
using OpenTracing.Propagation;
using OpenTracing.Tag;

namespace GrpcOpenTracing.Handlers
{
    internal class InterceptedClientHandler<TRequest, TResponse> 
        where TRequest : class 
        where TResponse : class
    {
        private readonly GrpcTraceLogger<TRequest, TResponse> logger;
        private readonly ClientInterceptorContext<TRequest, TResponse> context;

        public InterceptedClientHandler(ITracer tracer, ClientInterceptorContext<TRequest, TResponse> context)
        {
            this.context = context;
            if (context.Options.Headers == null)
            {
                this.context = new ClientInterceptorContext<TRequest, TResponse>(context.Method, context.Host, 
                    context.Options.WithHeaders(new Metadata())); // Add empty metadata to options
            }

            var span = InitializeSpanWithHeaders(tracer);
            this.logger = new GrpcTraceLogger<TRequest, TResponse>(span);
            tracer.Inject(span.Context, BuiltinFormats.HttpHeaders, new MetadataCarrier(this.context.Options.Headers));
        }

        private ISpan InitializeSpanWithHeaders(ITracer tracer)
        {
            return CreateSpanFromParent(tracer, $"Client {context.Method.FullName}")
                .SetTag(Tags.Component, Constants.TAGS_COMPONENT)
                .SetTag(Tags.SpanKind, Tags.SpanKindClient)
                .SetTag("grpc.method_name", context.Method.FullName);
            //.SetTag("peer.address", this.context.Host)
            //.SetTag("grpc.headers", string.Join("; ", this.context.Options.Headers.Select(e => $"{e.Key} = {e.Value}")));
        }

        private ISpan CreateSpanFromParent(ITracer tracer, string operationName)
        {
            ISpan span;
            try
            {
                var spanBuilder = tracer.BuildSpan(operationName);
                if (tracer.ActiveSpan != null)
                {
                    spanBuilder = spanBuilder.AsChildOf(tracer.ActiveSpan.Context);
                }
                span = spanBuilder.Start();
            }
            catch (Exception ex)
            {
                span = tracer.BuildSpan(operationName)
                    .WithException(ex)
                    .Start();
            }
            return span;
        }

        public TResponse BlockingUnaryCall(TRequest request, Interceptor.BlockingUnaryCallContinuation<TRequest, TResponse> continuation)
        {
            try
            {
                this.logger.Request(request);
                var response = continuation(request, this.context);
                this.logger.Response(response);
                this.logger.FinishSuccess();
                return response;
            }
            catch (Exception ex)
            {
                this.logger.FinishException(ex);
                throw;
            }
        }

        public AsyncUnaryCall<TResponse> AsyncUnaryCall(TRequest request, Interceptor.AsyncUnaryCallContinuation<TRequest, TResponse> continuation)
        {
            this.logger.Request(request);
            var rspCnt = continuation(request, this.context);
            var rspAsync = rspCnt.ResponseAsync.ContinueWith(rspTask =>
            {
                try
                {
                    var response = rspTask.Result;
                    this.logger.Response(response);
                    this.logger.FinishSuccess();
                    return response;
                }
                catch (AggregateException ex)
                {
                    this.logger.FinishException(ex.InnerException);
                    throw ex.InnerException;
                }
            });
            return new AsyncUnaryCall<TResponse>(rspAsync, rspCnt.ResponseHeadersAsync, rspCnt.GetStatus, rspCnt.GetTrailers, rspCnt.Dispose);
        }

        public AsyncServerStreamingCall<TResponse> AsyncServerStreamingCall(TRequest request, Interceptor.AsyncServerStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            this.logger.Request(request);
            var rspCnt = continuation(request, this.context);
            var tracingResponseStream = new TracingAsyncStreamReader<TResponse>(rspCnt.ResponseStream, this.logger.Response, this.logger.FinishSuccess, this.logger.FinishException);
            return new AsyncServerStreamingCall<TResponse>(tracingResponseStream, rspCnt.ResponseHeadersAsync, rspCnt.GetStatus, rspCnt.GetTrailers, rspCnt.Dispose);
        }

        public AsyncClientStreamingCall<TRequest, TResponse> AsyncClientStreamingCall(Interceptor.AsyncClientStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            var rspCnt = continuation(this.context);
            var tracingRequestStream = new TracingClientStreamWriter<TRequest>(rspCnt.RequestStream, this.logger.Request);
            var rspAsync = rspCnt.ResponseAsync.ContinueWith(rspTask =>
            {
                try
                {
                    var response = rspTask.Result;
                    this.logger.Response(response);
                    this.logger.FinishSuccess();
                    return response;
                }
                catch (AggregateException ex)
                {
                    this.logger.FinishException(ex.InnerException);
                    throw ex.InnerException;
                }
            });
            return new AsyncClientStreamingCall<TRequest, TResponse>(tracingRequestStream, rspAsync, rspCnt.ResponseHeadersAsync, rspCnt.GetStatus, rspCnt.GetTrailers, rspCnt.Dispose);
        }

        public AsyncDuplexStreamingCall<TRequest, TResponse> AsyncDuplexStreamingCall(Interceptor.AsyncDuplexStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            var rspCnt = continuation(this.context);
            var tracingRequestStream = new TracingClientStreamWriter<TRequest>(rspCnt.RequestStream, this.logger.Request);
            var tracingResponseStream = new TracingAsyncStreamReader<TResponse>(rspCnt.ResponseStream, this.logger.Response, this.logger.FinishSuccess, this.logger.FinishException);
            return new AsyncDuplexStreamingCall<TRequest, TResponse>(tracingRequestStream, tracingResponseStream, rspCnt.ResponseHeadersAsync, rspCnt.GetStatus, rspCnt.GetTrailers, rspCnt.Dispose);
        }
    }
}