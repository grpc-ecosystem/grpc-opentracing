package io.opentracing.contrib;

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

import io.opentracing.contrib.OpenTracingContextKey;
import io.opentracing.contrib.OperationNameConstructor;
import io.opentracing.propagation.Format;
import io.opentracing.propagation.TextMapExtractAdapter;
import io.opentracing.Span;
import io.opentracing.SpanContext;
import io.opentracing.Tracer;

import java.util.HashMap;
import java.util.Map;
import java.util.HashSet;
import java.util.Set;
import java.util.Arrays;

/**
 * An intercepter that applies tracing via OpenTracing to all requests 
 * to the server.
 */
public class ServerTracingInterceptor implements ServerInterceptor {
    
    private final Tracer tracer;
    private final OperationNameConstructor operationNameConstructor;
    private final boolean streaming;
    private final boolean verbose;
    private final Set<ServerRequestAttribute> tracedAttributes;

    /**
     * use spi mechanism to get tracer implementation.
     *
     * @see TracerLoader
     */
    public ServerTracingInterceptor(){
        this(TracerLoader.load());
    }

    /**
     * @param tracer used to trace requests
     */
    public ServerTracingInterceptor(Tracer tracer) {
        this.tracer = tracer;
        this.operationNameConstructor = OperationNameConstructor.DEFAULT;
        this.streaming = false;
        this.verbose = false;
        this.tracedAttributes = new HashSet<ServerRequestAttribute>();
    }

    private ServerTracingInterceptor(Tracer tracer, OperationNameConstructor operationNameConstructor, boolean streaming,
        boolean verbose, Set<ServerRequestAttribute> tracedAttributes) {
        this.tracer = tracer;
        this.operationNameConstructor = operationNameConstructor;
        this.streaming = streaming;
        this.verbose = verbose;
        this.tracedAttributes = tracedAttributes;
    }

    /**
     * Add tracing to all requests made to this service.
     * @param serviceDef of the service to intercept
     * @return the serviceDef with a tracing interceptor
     */
    public ServerServiceDefinition intercept(ServerServiceDefinition serviceDef) {
        return ServerInterceptors.intercept(serviceDef, this);
    }

    /**
     * Add tracing to all requests made to this service.
     * @param bindableService to intercept
     * @return the serviceDef with a tracing interceptor
     */
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

        final String operationName = operationNameConstructor.constructOperationName(call.getMethodDescriptor());
        final Span span = getSpanFromHeaders(headerMap, operationName);

        for (ServerRequestAttribute attr : this.tracedAttributes) {
            switch (attr) {
                case METHOD_TYPE:
                    span.setTag("grpc.method_type", call.getMethodDescriptor().getType().toString());
                    break;
                case METHOD_NAME:
                    span.setTag("grpc.method_name", call.getMethodDescriptor().getFullMethodName());
                    break;
                case CALL_ATTRIBUTES:
                    span.setTag("grpc.call_attributes", call.attributes().toString());
                    break;
                case HEADERS:
                    span.setTag("grpc.headers", headers.toString());
                    break;
            }
        }

        Context ctxWithSpan = Context.current().withValue(OpenTracingContextKey.getKey(), span);
        ServerCall.Listener<ReqT> listenerWithContext = Contexts
            .interceptCall(ctxWithSpan, call, headers, next);

        ServerCall.Listener<ReqT> tracingListenerWithContext = 
            new ForwardingServerCallListener.SimpleForwardingServerCallListener<ReqT>(listenerWithContext) {

            @Override
            public void onMessage(ReqT message) {
                if (streaming || verbose) { span.log("Message received", message); }
                delegate().onMessage(message);
            }

            @Override 
            public void onHalfClose() {
                if (streaming) { span.log("Client finished sending messages", null); }
                delegate().onHalfClose();
            }

            @Override
            public void onCancel() {
                span.log("Call cancelled", null);
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
            SpanContext parentSpanCtx = tracer.extract(Format.Builtin.HTTP_HEADERS, 
                new TextMapExtractAdapter(headers));
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

    /**
     * Builds the configuration of a ServerTracingInterceptor.
     */
    public static class Builder {
        private final Tracer tracer;
        private OperationNameConstructor operationNameConstructor;
        private boolean streaming;
        private boolean verbose;
        private Set<ServerRequestAttribute> tracedAttributes;

        /**
         * Creates a Builder with default configuration and auto tracer loader with spi mechanism
         *
         * @see TracerLoader
         */
        public Builder() {
            this(TracerLoader.load());
        }

        /**
         * @param tracer to use for this intercepter
         * Creates a Builder with default configuration
         */
        public Builder(Tracer tracer) {
            this.tracer = tracer;
            this.operationNameConstructor = OperationNameConstructor.DEFAULT;
            this.streaming = false;
            this.verbose = false;
            this.tracedAttributes = new HashSet<ServerRequestAttribute>();
        }

        /**
         * @param operationNameConstructor for all spans created by this intercepter
         * @return this Builder with configured operation name
         */
        public Builder withOperationName(OperationNameConstructor operationNameConstructor) {
            this.operationNameConstructor = operationNameConstructor;
            return this;
        }

        /**
         * @param attributes to set as tags on server spans
         *  created by this intercepter
         * @return this Builder configured to trace request attributes
         */
        public Builder withTracedAttributes(ServerRequestAttribute... attributes) {
            this.tracedAttributes = new HashSet<ServerRequestAttribute>(Arrays.asList(attributes));
            return this;
        }

        /**
         * Logs streaming events to server spans.
         * @return this Builder configured to log streaming events
         */
        public Builder withStreaming() {
            this.streaming = true;
            return this;
        }

        /**
         * Logs all request life-cycle events to server spans.
         * @return this Builder configured to be verbose
         */
        public Builder withVerbosity() {
            this.verbose = true;
            return this;
        }

        /**
         * @return a ServerTracingInterceptor with this Builder's configuration
         */
        public ServerTracingInterceptor build() {
            return new ServerTracingInterceptor(this.tracer, this.operationNameConstructor, 
                this.streaming, this.verbose, this.tracedAttributes);
        }
    }

    enum ServerRequestAttribute {
        HEADERS,
        METHOD_TYPE,
        METHOD_NAME,
        CALL_ATTRIBUTES
    }
}    
