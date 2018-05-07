﻿using System.Threading.Tasks;
using Grpc.Core;
using Grpc.Core.Interceptors;
using Grpc.Core.Utils;
using Grpc.OpenTracing.Handlers;
using OpenTracing;

namespace Grpc.OpenTracing
{
    public class TracingInterceptor : Interceptor
    {
        private readonly ITracer _tracer;

        public TracingInterceptor(ITracer tracer)
        {
            GrpcPreconditions.CheckNotNull(tracer, nameof(tracer));
            _tracer = tracer;
        }

        public override Task<TResponse> UnaryServerHandler<TRequest, TResponse>(TRequest request, ServerCallContext context, UnaryServerMethod<TRequest, TResponse> continuation)
        {
            return new InterceptedServerHandler<TRequest, TResponse>(_tracer, context)
                .UnaryServerHandler(request, continuation);
        }

        public override Task<TResponse> ClientStreamingServerHandler<TRequest, TResponse>(IAsyncStreamReader<TRequest> requestStream, ServerCallContext context, ClientStreamingServerMethod<TRequest, TResponse> continuation)
        {
            return new InterceptedServerHandler<TRequest, TResponse>(_tracer, context)
                .ClientStreamingServerHandler(requestStream, continuation);
        }

        public override Task ServerStreamingServerHandler<TRequest, TResponse>(TRequest request, IServerStreamWriter<TResponse> responseStream, ServerCallContext context, ServerStreamingServerMethod<TRequest, TResponse> continuation)
        {
            return new InterceptedServerHandler<TRequest, TResponse>(_tracer, context)
                .ServerStreamingServerHandler(request, responseStream, continuation);
        }

        public override Task DuplexStreamingServerHandler<TRequest, TResponse>(IAsyncStreamReader<TRequest> requestStream, IServerStreamWriter<TResponse> responseStream, ServerCallContext context, DuplexStreamingServerMethod<TRequest, TResponse> continuation)
        {
            return new InterceptedServerHandler<TRequest, TResponse>(_tracer, context)
                .DuplexStreamingServerHandler(requestStream, responseStream, continuation);
        }

        public override TResponse BlockingUnaryCall<TRequest, TResponse>(TRequest request, ClientInterceptorContext<TRequest, TResponse> context, BlockingUnaryCallContinuation<TRequest, TResponse> continuation)
        {
            return new InterceptedClientHandler<TRequest, TResponse>(_tracer, context)
                .BlockingUnaryCall(request, continuation);
        }

        public override AsyncUnaryCall<TResponse> AsyncUnaryCall<TRequest, TResponse>(TRequest request, ClientInterceptorContext<TRequest, TResponse> context, AsyncUnaryCallContinuation<TRequest, TResponse> continuation)
        {
            return new InterceptedClientHandler<TRequest, TResponse>(_tracer, context)
                .AsyncUnaryCall(request, continuation);
        }

        public override AsyncServerStreamingCall<TResponse> AsyncServerStreamingCall<TRequest, TResponse>(TRequest request, ClientInterceptorContext<TRequest, TResponse> context,
            AsyncServerStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            return new InterceptedClientHandler<TRequest, TResponse>(_tracer, context)
                .AsyncServerStreamingCall(request, continuation);
        }

        public override AsyncClientStreamingCall<TRequest, TResponse> AsyncClientStreamingCall<TRequest, TResponse>(ClientInterceptorContext<TRequest, TResponse> context, AsyncClientStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            return new InterceptedClientHandler<TRequest, TResponse>(_tracer, context)
                .AsyncClientStreamingCall(continuation);
        }

        public override AsyncDuplexStreamingCall<TRequest, TResponse> AsyncDuplexStreamingCall<TRequest, TResponse>(ClientInterceptorContext<TRequest, TResponse> context, AsyncDuplexStreamingCallContinuation<TRequest, TResponse> continuation)
        {
            return new InterceptedClientHandler<TRequest, TResponse>(_tracer, context)
                .AsyncDuplexStreamingCall(continuation);
        }
    }
}
