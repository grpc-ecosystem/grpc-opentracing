package io.opentracing.contrib.grpc;

import io.grpc.Context;
import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;

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
    
    // TODO: use builder to make configurable

    private final Tracer tracer;

    public ServerTracingInterceptor(Tracer tracer) {
        this.tracer = tracer;
    }
    
    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
        ServerCall<ReqT, RespT> call, 
        Metadata headers, 
        ServerCallHandler<ReqT, RespT> next
    ) {
        String EXTRACT_FAIL_MSG = "Extract failed and an IllegalArgumentException was thrown";
        String ERROR = "Error";

        Map<String, String> headerMap = new HashMap<String, String>();
        for (String key : headers.keys()) {
            String value = headers.get(Metadata.Key.of(key, Metadata.ASCII_STRING_MARSHALLER));
            headerMap.put(key, value);
        }

        String operationName = call.getMethodDescriptor().getFullMethodName();

        Span span;
        System.out.println("Tracer: " + tracer.toString());
        System.out.println("Header map: " + headerMap.toString());
        try {
            SpanContext parentSpanCtx = this.tracer.extract(Format.Builtin.HTTP_HEADERS, new TextMapExtractAdapter(headerMap));
            if (parentSpanCtx == null) {
                span = this.tracer.buildSpan(operationName).start();
            } else {
                span = this.tracer.buildSpan(operationName).asChildOf(parentSpanCtx).start();
            }
        } catch (IllegalArgumentException iae){
            span = this.tracer.buildSpan(operationName).withTag(ERROR, EXTRACT_FAIL_MSG).start();
        }

        Context ctxWithSpan = Context.current().withValue(OpenTracingContextKey.get(), span);
        Context previousCtx = ctxWithSpan.attach();

        System.out.println("Contexts in interceptor");
        System.out.println(OpenTracingContextKey.get());
        System.out.println(OpenTracingContextKey.get().get());

        ServerCall.Listener<ReqT> listener = next.startCall(call, headers);

        System.out.println("call was started");
        try {
            Thread.sleep(1000);
        } catch (Exception e) {
            System.out.println("Thread did not sleep");
        }
        ctxWithSpan.detach(previousCtx);

        System.out.println("context was detached");
        span.finish(); 

        return listener;
    }
}

