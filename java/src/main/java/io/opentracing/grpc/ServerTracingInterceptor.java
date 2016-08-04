package io.opentracing.contrib.grpc;

import io.grpc.BindableService;
import io.grpc.Context;
import io.grpc.Contexts;
import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import io.grpc.ServerInterceptors;
import io.grpc.ServerServiceDefinition;
import io.grpc.ForwardingServerCallListener;

import io.opentracing.contrib.grpc.OpenTracingContextKey;
import io.opentracing.contrib.grpc.ServerAttribute;
import io.opentracing.propagation.Format;
import io.opentracing.propagation.TextMapExtractAdapter;
import io.opentracing.Span;
import io.opentracing.SpanContext;
import io.opentracing.Tracer;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.HashSet;
import java.util.Set;
import java.util.Arrays;

public class ServerTracingInterceptor implements ServerInterceptor {
    
    private final Tracer tracer;
    private final String operationName;
    private final boolean streaming;
    private final boolean verbose;
    private final Set<ServerAttribute> tracedAttributes; 
    // options for server tracing:
    //  Custom server name
    //  headers.toString()
    //  call.attributes()
    //  call.getMethodDescriptor()

    public ServerTracingInterceptor(Tracer tracer) {
        this.tracer = tracer;
        this.operationName = "";
        this.streaming = false;
        this.verbose = false;
        this.tracedAttributes = new HashSet<ServerAttribute>();
    }

    private ServerTracingInterceptor(Tracer tracer, String operationName, boolean streaming, boolean verbose, Set<ServerAttribute> tracedAttributes) {
        this.tracer = tracer;
        this.operationName = operationName;
        this.streaming = streaming;
        this.verbose = verbose;
        this.tracedAttributes = tracedAttributes;
    }

    public ServerServiceDefinition intercept(ServerServiceDefinition serviceDef) {
        return ServerInterceptors.intercept(serviceDef, this);
    }

    public ServerServiceDefinition intercept(BindableService bindableService) {
        return ServerInterceptors.intercept(bindableService, this);
    }
    
    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
        ServerCall<ReqT, RespT> call, 
        Metadata headers, 
        ServerCallHandler<ReqT, RespT> next
    ) {
        Map<String, String> headerMap = new HashMap<String, String>();
        for (String key : headers.keys()) {
            String value = headers.get(Metadata.Key.of(key, Metadata.ASCII_STRING_MARSHALLER));
            headerMap.put(key, value);
        }
        String operationName = call.getMethodDescriptor().getFullMethodName();
        final Span span = getSpanFromHeaders(headerMap, operationName);

        Context ctxWithSpan = Context.current().withValue(OpenTracingContextKey.getKey(), span);
        ServerCall.Listener<ReqT> listenerWithContext = Contexts.interceptCall(ctxWithSpan, call, headers, next);

        ServerCall.Listener<ReqT> tracingListenerWithContext = 
            new ForwardingServerCallListener.SimpleForwardingServerCallListener<ReqT>(listenerWithContext) {

            @Override
            public void onMessage(ReqT message) {
                if (streaming) { span.log("Message received", message); }
                delegate().onMessage(message);
            }

            // TODO: should these be optional?
            @Override 
            public void onHalfClose() {
                if (verbose) { span.log("Message sending complete", null); }
                delegate().onHalfClose();
            }

            @Override
            public void onCancel() {
                if (verbose) { span.log("Call cancelled", null); }
                span.finish();
                delegate().onCancel();
            }

            @Override
            public void onComplete() {
                if (verbose) { span.log("Call completed", null); }
                span.finish();
                delegate().onComplete();
            }
        };

        return tracingListenerWithContext; 
    }

    private Span getSpanFromHeaders(Map<String, String> headers, String operationName) {
        Span span;
        try {
            SpanContext parentSpanCtx = tracer.extract(Format.Builtin.HTTP_HEADERS, new TextMapExtractAdapter(headers));
            if (parentSpanCtx == null) {
                span = tracer.buildSpan(operationName).start();
            } else {
                span = tracer.buildSpan(operationName).asChildOf(parentSpanCtx).start();
            }
        } catch (IllegalArgumentException iae){
            span = tracer.buildSpan(operationName)
                .withTag("Error", "Extract failed and an IllegalArgumentException was thrown")
                .start();
        }
        return span;  
    }

    public static class Builder {
        private final Tracer tracer;
        private String operationName;
        private boolean streaming;
        private boolean verbose;
        private Set<ServerAttribute> tracedAttributes;

        public Builder(Tracer tracer) {
            this.tracer = tracer;
            this.operationName = "";
            this.streaming = false;
            this.verbose = false;
            this.tracedAttributes = new HashSet<ServerAttribute>();
        }

        public Builder withOperationName(String operationName) {
            this.operationName = operationName;
            return this;
        }

        public Builder withTracedAttributes(ServerAttribute... attributes) {
            this.tracedAttributes = new HashSet<ServerAttribute>(Arrays.asList(attributes));
            return this;
        }

        public Builder withStreaming() {
            this.streaming = true;
            return this;
        }

        public Builder withVerbosity() {
            this.verbose = true;
            return this;
        }

        public ServerTracingInterceptor build() {
            return new ServerTracingInterceptor(this.tracer, this.operationName, this.streaming, this.verbose, this.tracedAttributes);
        }
    }
}    
