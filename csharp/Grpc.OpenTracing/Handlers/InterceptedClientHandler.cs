using System;
using Grpc.Core;
using Grpc.Core.Interceptors;
using Grpc.OpenTracing.Propagation;
using Grpc.OpenTracing.Streaming;
using OpenTracing;
using OpenTracing.Propagation;
using OpenTracing.Tag;

namespace Grpc.OpenTracing.Handlers
{
    internal class InterceptedClientHandler<TRequest, TResponse> 
        where TRequest : class 
        where TResponse : class
    {
        private readonly GrpcTraceLogger<TRequest, TResponse> _logger;
        private readonly ClientInterceptorContext<TRequest, TResponse> _context;

        public InterceptedClientHandler(ITracer tracer, ClientInterceptorContext<TRequest, TResponse> context)
        {
            _context = context;
            if (context.Options.Headers == null)
            {
                _context = new ClientInterceptorContext<TRequest, TResponse>(context.Method, context.Host, 
                    context.Options.WithHeaders(new Metadata())); // Add empty metadata to options
            }

            var span = InitializeSpanWithHeaders(tracer);
            _logger = new GrpcTraceLogger<TRequest, TResponse>(span);
            tracer.Inject(span.Context, BuiltinFormats.HttpHeaders, new MetadataCarrier(_context.Options.Headers));
        }

        private ISpan InitializeSpanWithHeaders(ITracer tracer)
        {
            return tracer.BuildSpan($"Client {_context.Method.FullName}")
                .WithTag(Tags.Component, Constants.TAGS_COMPONENT)
                .WithTag(Tags.SpanKind, Tags.SpanKindClient)
                .WithTag("grpc.method_name", _context.Method.FullName)
                //.WithTag("peer.address", this.context.Host)
                //.WithTag("grpc.headers", string.Join("; ", this.context.Options.Headers.Select(e => $"{e.Key} = {e.Value}")))
                .Start();
        }

        public TResponse BlockingUnaryCall(TRequest request, Interceptor.BlockingUnaryCallContinuation<TRequest, TResponse> continuation)
        {
            try
            {
                _logger.Request(request);
                var response = continuation(request, _context);
                _logger.Response(response);
                _logger.FinishSuccess();
                return response;
            }
            catch (Exception ex)
            {
                _logger.FinishException(ex);
                throw;
            }
        }

        public AsyncUnaryCall<TResponse> AsyncUnaryCall(TRequest request, Interceptor.AsyncUnaryCallContinuation<TRequest, TResponse> continuation)
        {
            _logger.Request(request);
            var rspCnt = continuation(request, _context);
            var rspAsync = rspCnt.ResponseAsync.ContinueWith(rspTask =>
            {
                try
                {
                    var response = rspTask.Result;
                    _logger.Response(response);
                    _logger.FinishSuccess();
                    return response;
                }
                catch (AggregateException ex)
                {
                    _logger.FinishException(ex.InnerException);
                    throw ex.InnerException;
                }
            });
            return new AsyncUnaryCall<TResponse>(rspAsync, rspCnt.ResponseHeadersAsync, rspCnt.GetStatus, rspCnt.GetTrailers, rspCnt.Dispose);
        }

        public AsyncServerStreamingCall<TResponse> AsyncServerStreamingCall(TRequest request, Interceptor.AsyncServerStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            _logger.Request(request);
            var rspCnt = continuation(request, _context);
            var tracingResponseStream = new TracingAsyncStreamReader<TResponse>(rspCnt.ResponseStream, _logger.Response, _logger.FinishSuccess, _logger.FinishException);
            return new AsyncServerStreamingCall<TResponse>(tracingResponseStream, rspCnt.ResponseHeadersAsync, rspCnt.GetStatus, rspCnt.GetTrailers, rspCnt.Dispose);
        }

        public AsyncClientStreamingCall<TRequest, TResponse> AsyncClientStreamingCall(Interceptor.AsyncClientStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            var rspCnt = continuation(_context);
            var tracingRequestStream = new TracingClientStreamWriter<TRequest>(rspCnt.RequestStream, _logger.Request);
            var rspAsync = rspCnt.ResponseAsync.ContinueWith(rspTask =>
            {
                try
                {
                    var response = rspTask.Result;
                    _logger.Response(response);
                    _logger.FinishSuccess();
                    return response;
                }
                catch (AggregateException ex)
                {
                    _logger.FinishException(ex.InnerException);
                    throw ex.InnerException;
                }
            });
            return new AsyncClientStreamingCall<TRequest, TResponse>(tracingRequestStream, rspAsync, rspCnt.ResponseHeadersAsync, rspCnt.GetStatus, rspCnt.GetTrailers, rspCnt.Dispose);
        }

        public AsyncDuplexStreamingCall<TRequest, TResponse> AsyncDuplexStreamingCall(Interceptor.AsyncDuplexStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            var rspCnt = continuation(_context);
            var tracingRequestStream = new TracingClientStreamWriter<TRequest>(rspCnt.RequestStream, _logger.Request);
            var tracingResponseStream = new TracingAsyncStreamReader<TResponse>(rspCnt.ResponseStream, _logger.Response, _logger.FinishSuccess, _logger.FinishException);
            return new AsyncDuplexStreamingCall<TRequest, TResponse>(tracingRequestStream, tracingResponseStream, rspCnt.ResponseHeadersAsync, rspCnt.GetStatus, rspCnt.GetTrailers, rspCnt.Dispose);
        }
    }
}