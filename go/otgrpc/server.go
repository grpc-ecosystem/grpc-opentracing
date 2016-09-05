package otgrpc

import (
	opentracing "github.com/opentracing/opentracing-go"
	"github.com/opentracing/opentracing-go/ext"
	"golang.org/x/net/context"
	"google.golang.org/grpc"
	"google.golang.org/grpc/metadata"
)

// OpenTracingServerInterceptor returns a grpc.UnaryServerInterceptor suitable
// for use in a grpc.NewServer call.
//
// For example:
//
//     s := grpc.NewServer(
//         ...,  // (existing ServerOptions)
//         grpc.UnaryInterceptor(otgrpc.OpenTracingServerInterceptor(tracer)))
//
// All gRPC server spans will look for an OpenTracing SpanContext in the gRPC
// metadata; if found, the server span will act as the ChildOf that RPC
// SpanContext.
//
// Root or not, the server Span will be embedded in the context.Context for the
// application-specific gRPC handler(s) to access.
func OpenTracingServerInterceptor(tracer opentracing.Tracer, optFuncs ...Option) grpc.UnaryServerInterceptor {
	otgrpcOpts := newOptions()
	otgrpcOpts.apply(optFuncs...)
	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (resp interface{}, err error) {
		md, ok := metadata.FromContext(ctx)
		if !ok {
			md = metadata.New(nil)
		}
		spanContext, err := tracer.Extract(opentracing.TextMap, metadataReaderWriter{md})
		if err != nil && err != opentracing.ErrSpanContextNotFound {
			// TODO: establish some sort of error reporting mechanism here. We
			// don't know where to put such an error and must rely on Tracer
			// implementations to do something appropriate for the time being.
		}
		span := tracer.StartSpan(
			info.FullMethod,
			ext.RPCServerOption(spanContext),
			gRPCComponentTag,
		)
		defer span.Finish()

		ctx = opentracing.ContextWithSpan(ctx, span)
		if otgrpcOpts.logPayloads {
			span.LogEventWithPayload("gRPC request", req)
		}
		resp, err = handler(ctx, req)
		if err == nil {
			if otgrpcOpts.logPayloads {
				span.LogEventWithPayload("gRPC response", resp)
			}
		} else {
			ext.Error.Set(span, true)
			span.LogEventWithPayload("gRPC error", err)
		}
		return resp, err
	}
}
