package io.opentracing.contrib.grpc;

import io.grpc.Context;
import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import io.grpc.ForwardingServerCallListener;

import io.opentracing.contrib.grpc.OpenTracingContextKey;
import io.opentracing.propagation.Format;
import io.opentracing.propagation.TextMapExtractAdapter;
import io.opentracing.Span;
import io.opentracing.SpanContext;
import io.opentracing.Tracer;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

public class ServerTracingInterceptor implements ServerInterceptor {
    
    private final Tracer tracer;
    // options for server tracing:
    //  Custom server name
    //  headers.toString()
    //  call.attributes()
    //  call.getMethodDescriptor()

    public ServerTracingInterceptor(Tracer tracer) {
        this.tracer = tracer;
    }
    
    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
        ServerCall<ReqT, RespT> call, 
        Metadata headers, 
        ServerCallHandler<ReqT, RespT> next
    ) {
        System.out.println("intercepting server call");
        System.out.println("Context in server: " + Context.current().toString());
        Span testSpan = tracer.buildSpan("test-span").start();
        testSpan.finish();

        Map<String, String> headerMap = new HashMap<String, String>();
        for (String key : headers.keys()) {
            String value = headers.get(Metadata.Key.of(key, Metadata.ASCII_STRING_MARSHALLER));
            headerMap.put(key, value);
        }

        System.out.println("Headers: " + headerMap.toString());

        String operationName = call.getMethodDescriptor().getFullMethodName();

        System.out.println("operation name: " + operationName);

        final Span span = getSpanFromHeaders(headerMap, operationName);

        span.setTag("server at:", System.currentTimeMillis()); 

        // Context.CancellableContext withSpan = Context.current().withValue(OpenTracingContextKey.getKey(), span).withCancellation();
        // withSpan.attach();

        // ServerCallHandler<ReqT, RespT> nextWithTracing = new TracedServerCallHandler<ReqT, RespT>(next, span);

        return new ForwardingServerCallListener.SimpleForwardingServerCallListener<ReqT>(next.startCall(call, headers)) {

            @Override
            public void onMessage(ReqT message) {
                System.out.println("server received message");
                // Context withSpan = Context.current().withValue(OpenTracingContextKey.getKey(), span);
                // withSpan.attach();
                // System.out.println("Context withSpan " + withSpan.toString());
                delegate().onMessage(message);
            }

            @Override
            public void onCancel() {
                System.out.println("cancelling server call");
                span.finish();
                delegate().onCancel();
            }

            @Override
            public void onComplete() {
                System.out.println("completing server call");
                span.finish();
                delegate().onComplete();
            }
        }; 
    }

    private Span getSpanFromHeaders(Map<String, String> headers, String operationName) {
        String EXTRACT_FAIL_MSG = "Extract failed and an IllegalArgumentException was thrown";
        Span span;
        try {
            SpanContext parentSpanCtx = tracer.extract(Format.Builtin.HTTP_HEADERS, new TextMapExtractAdapter(headers));
            if (parentSpanCtx == null) {
                System.out.println("span created w null parent");
                span = tracer.buildSpan(operationName).start();
            } else {
                System.out.println("span created from parent");
                span = tracer.buildSpan(operationName).asChildOf(parentSpanCtx).start();
            }
        } catch (IllegalArgumentException iae){
            System.out.println("Span created no parent (error)");
            span = tracer.buildSpan(operationName).withTag("Error", EXTRACT_FAIL_MSG).start();
        }
        return span;  
    }
}



class TracedServerCallHandler<ReqT, RespT> implements ServerCallHandler<ReqT, RespT> {

    private final ServerCallHandler untracedHandler;
    private final Span span;

    public TracedServerCallHandler(ServerCallHandler handler, Span span) {
        this.untracedHandler = handler;
        this.span = span;
    }

    @Override
    public ServerCall.Listener<ReqT> startCall(
        ServerCall<ReqT, RespT> call,
        Metadata headers
    ) {
        Context withSpan = Context.current().withValue(OpenTracingContextKey.getKey(), span);
        Context previousCtx = withSpan.attach();
        ServerCall.Listener<ReqT> listener;
        try {
            listener = untracedHandler.startCall(call, headers);
        } finally {
            withSpan.detach(previousCtx);
        }
        return listener;
    }
}

// Server interceptor is created once for the server -- initialized with a tracer
// interceptCall is called everytime there is a new call; this is where we can create a span
//      create in beginning of function (final Span = getSpanFromHeaders())
//      log things like messageSend etc
//      onComplete / onCancel= finish span
//      


// Note on streaming requests/responses:
// Unary request/response - start span on Listener.onMessage, end span on Listener.onComplete/onCancel
// Streaming request/single response - start span for first request, end on the last response
// Single request/streaming response - start span on Listener.onMessage, end span on 
