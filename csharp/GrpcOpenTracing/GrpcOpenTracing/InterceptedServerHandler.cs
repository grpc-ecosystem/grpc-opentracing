using System;
using System.Linq;
using System.Threading.Tasks;
using Grpc.Core;
using OpenTracing;
using OpenTracing.Propagation;

namespace GrpcOpenTracing
{
    internal class InterceptedServerHandler<TRequest, TResponse>
        where TRequest : class
        where TResponse : class
    {
        private readonly GrpcTraceLogger<TRequest, TResponse> logger;
        private readonly ServerCallContext context;

        public InterceptedServerHandler(ITracer tracer, ServerCallContext context)
        {
            this.context = context;

            ISpan span = GetSpanFromContext(tracer);
            this.logger = new GrpcTraceLogger<TRequest, TResponse>(span);
        }

        private ISpan GetSpanFromContext(ITracer tracer)
        {
            return GetSpanFromHeaders(tracer, context.RequestHeaders, this.context.Method)
                .SetTag("component", "grpc")
                .SetTag("span.kind", "server")
                .SetTag("peer.address", this.context.Peer)
                .SetTag("grpc.method_name", this.context.Method)
                .SetTag("grpc.headers", string.Join("; ", this.context.RequestHeaders.Select(e => $"{e.Key} = {e.Value}")));
        }

        private ISpan GetSpanFromHeaders(ITracer tracer, Metadata metadata, string operationName)
        {
            ISpan span;
            try
            {
                ISpanContext parentSpanCtx = tracer.Extract(BuiltinFormats.HttpHeaders, new MetadataCarrier(metadata));
                var spanBuilder = tracer.BuildSpan(operationName);
                if (parentSpanCtx != null)
                {
                    spanBuilder = spanBuilder.AsChildOf(parentSpanCtx);
                }
                span = spanBuilder.Start();
                tracer.ScopeManager.Activate(span, false);
            }
            catch (Exception ex)
            {
                span = tracer.BuildSpan(operationName)
                    .WithException(ex)
                    .Start();
            }
            return span;
        }

        public async Task<TResponse> UnaryServerHandler(TRequest request, UnaryServerMethod<TRequest, TResponse> continuation)
        {
            try
            {
                this.logger.Request(request);
                var response = await continuation(request, this.context).ConfigureAwait(false);
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

        public async Task<TResponse> ClientStreamingServerHandler(IAsyncStreamReader<TRequest> requestStream, ClientStreamingServerMethod<TRequest, TResponse> continuation)
        {
            try
            {
                var tracingRequestStream = new TracingAsyncStreamReader<TRequest>(requestStream, this.logger.Request);
                var response = await continuation(tracingRequestStream, this.context).ConfigureAwait(false);
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

        public async Task ServerStreamingServerHandler(TRequest request, IServerStreamWriter<TResponse> responseStream, ServerStreamingServerMethod<TRequest, TResponse> continuation)
        {
            try
            {
                var tracingResponseStream = new TracingServerStreamWriter<TResponse>(responseStream, this.logger.Response);
                this.logger.Request(request);
                await continuation(request, tracingResponseStream, this.context).ConfigureAwait(false);
                this.logger.FinishSuccess();
            }
            catch (Exception ex)
            {
                this.logger.FinishException(ex);
                throw;
            }
        }

        public async Task DuplexStreamingServerHandler(IAsyncStreamReader<TRequest> requestStream, IServerStreamWriter<TResponse> responseStream, DuplexStreamingServerMethod<TRequest, TResponse> continuation)
        {
            try
            {
                var tracingRequestStream = new TracingAsyncStreamReader<TRequest>(requestStream, this.logger.Request);
                var tracingResponseStream = new TracingServerStreamWriter<TResponse>(responseStream, this.logger.Response);
                await continuation(tracingRequestStream, tracingResponseStream, this.context).ConfigureAwait(false);
                this.logger.FinishSuccess();
            }
            catch (Exception ex)
            {
                this.logger.FinishException(ex);
                throw;
            }
        }
    }
}