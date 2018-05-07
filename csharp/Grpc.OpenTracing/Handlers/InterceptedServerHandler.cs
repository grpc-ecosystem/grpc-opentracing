using System;
using System.Linq;
using System.Threading.Tasks;
using Grpc.Core;
using Grpc.OpenTracing.Propagation;
using Grpc.OpenTracing.Streaming;
using OpenTracing;
using OpenTracing.Propagation;
using OpenTracing.Tag;

namespace Grpc.OpenTracing.Handlers
{
    internal class InterceptedServerHandler<TRequest, TResponse>
        where TRequest : class
        where TResponse : class
    {
        private readonly GrpcTraceLogger<TRequest, TResponse> _logger;
        private readonly ServerCallContext _context;

        public InterceptedServerHandler(ITracer tracer, ServerCallContext context)
        {
            _context = context;

            var span = GetSpanFromContext(tracer);
            _logger = new GrpcTraceLogger<TRequest, TResponse>(span);
        }

        private ISpan GetSpanFromContext(ITracer tracer)
        {
            return GetSpanBuilderFromHeaders(tracer, _context.RequestHeaders, $"Server {_context.Method}")
                .WithTag(Tags.Component, Constants.TAGS_COMPONENT)
                .WithTag(Tags.SpanKind, Tags.SpanKindServer)
                .WithTag("peer.address", _context.Peer)
                .WithTag("grpc.method_name", _context.Method)
                .WithTag("grpc.headers", GetGrpcHeaders())
                .StartActive(false).Span;
        }

        private string GetGrpcHeaders()
        {
            return string.Join("; ", _context.RequestHeaders.Select(e => $"{e.Key} = {e.Value}"));
        }

        private ISpanBuilder GetSpanBuilderFromHeaders(ITracer tracer, Metadata metadata, string operationName)
        {
            var parentSpanCtx = tracer.Extract(BuiltinFormats.HttpHeaders, new MetadataCarrier(metadata));
            var spanBuilder = tracer.BuildSpan(operationName);
            if (parentSpanCtx != null)
            {
                spanBuilder = spanBuilder.AsChildOf(parentSpanCtx);
            }
            return spanBuilder;
        }

        public async Task<TResponse> UnaryServerHandler(TRequest request, UnaryServerMethod<TRequest, TResponse> continuation)
        {
            try
            {
                _logger.Request(request);
                var response = await continuation(request, _context).ConfigureAwait(false);
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

        public async Task<TResponse> ClientStreamingServerHandler(IAsyncStreamReader<TRequest> requestStream, ClientStreamingServerMethod<TRequest, TResponse> continuation)
        {
            try
            {
                var tracingRequestStream = new TracingAsyncStreamReader<TRequest>(requestStream, _logger.Request);
                var response = await continuation(tracingRequestStream, _context).ConfigureAwait(false);
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

        public async Task ServerStreamingServerHandler(TRequest request, IServerStreamWriter<TResponse> responseStream, ServerStreamingServerMethod<TRequest, TResponse> continuation)
        {
            try
            {
                var tracingResponseStream = new TracingServerStreamWriter<TResponse>(responseStream, _logger.Response);
                _logger.Request(request);
                await continuation(request, tracingResponseStream, _context).ConfigureAwait(false);
                _logger.FinishSuccess();
            }
            catch (Exception ex)
            {
                _logger.FinishException(ex);
                throw;
            }
        }

        public async Task DuplexStreamingServerHandler(IAsyncStreamReader<TRequest> requestStream, IServerStreamWriter<TResponse> responseStream, DuplexStreamingServerMethod<TRequest, TResponse> continuation)
        {
            try
            {
                var tracingRequestStream = new TracingAsyncStreamReader<TRequest>(requestStream, _logger.Request);
                var tracingResponseStream = new TracingServerStreamWriter<TResponse>(responseStream, _logger.Response);
                await continuation(tracingRequestStream, tracingResponseStream, _context).ConfigureAwait(false);
                _logger.FinishSuccess();
            }
            catch (Exception ex)
            {
                _logger.FinishException(ex);
                throw;
            }
        }
    }
}