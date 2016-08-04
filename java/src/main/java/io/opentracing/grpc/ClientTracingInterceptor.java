package io.opentracing.contrib.grpc;

import io.grpc.CallOptions;
import io.grpc.Channel;
import io.grpc.ClientCall;
import io.grpc.ClientCall.Listener;
import io.grpc.ClientInterceptor;
import io.grpc.ClientInterceptors;
import io.grpc.Context;
import io.grpc.ForwardingClientCall;
import io.grpc.ForwardingClientCallListener;
import io.grpc.Metadata;
import io.grpc.MethodDescriptor;
import io.grpc.Status;

import io.opentracing.contrib.grpc.OpenTracingContextKey;
import io.opentracing.contrib.grpc.ClientRequestAttribute;
import io.opentracing.Tracer;
import io.opentracing.Span;
import io.opentracing.propagation.TextMap;
import io.opentracing.propagation.Format;

import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;
import java.util.Arrays;
import javax.annotation.Nullable;

public class ClientTracingInterceptor implements ClientInterceptor {
    
    private final Tracer tracer;
    private final String operationName;
    private final boolean streaming;
    private final boolean verbose;
    private final Set<ClientRequestAttribute> tracedAttributes;

    public ClientTracingInterceptor(Tracer tracer) {
        this.tracer = tracer;
        this.operationName = "";
        this.streaming = false;
        this.verbose = false;
        this.tracedAttributes = new HashSet<ClientRequestAttribute>();
    }

    private ClientTracingInterceptor(Tracer tracer, String operationName, boolean streaming, boolean verbose, Set<ClientRequestAttribute> tracedAttributes) {
        this.tracer = tracer;
        this.operationName = operationName;
        this.streaming = streaming;
        this.verbose = verbose;
        this.tracedAttributes = tracedAttributes;
    }

    public Channel intercept(Channel channel) {
        return ClientInterceptors.intercept(channel, this);
    }

    @Override
    public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
        MethodDescriptor<ReqT, RespT> method, 
        CallOptions callOptions, 
        Channel next
    ) {
        final String operationName;
        if (this.operationName.equals("")) {
            operationName = method.getFullMethodName();
        } else {
            operationName = this.operationName;
        }

        Span activeSpan = OpenTracingContextKey.activeSpan();
        final Span span = createSpanFromParent(activeSpan, operationName);
        System.out.println("Started span " + span.toString());

        for (ClientRequestAttribute attr : this.tracedAttributes) {
            switch (attr) {
                case AFFINITY:
                    if (callOptions.getAffinity() == null) {
                        span.setTag("Affinity", "null");
                    } else {
                        span.setTag("Affinity", callOptions.getAffinity().toString());
                    }  
                    break;
                case ALL_CALL_OPTIONS:
                    span.setTag("Call Options", callOptions.toString());
                    break;
                case AUTHORITY:
                    if (callOptions.getAuthority() == null) {
                        span.setTag("Authority", "null");
                    } else {
                        span.setTag("Authority", callOptions.getAuthority());                        
                    }
                    break;
                case COMPRESSOR:
                    if (callOptions.getCompressor() == null) {
                        span.setTag("Compressor", "null");
                    } else {
                        span.setTag("Compressor", callOptions.getCompressor());
                    }
                    break;
                case DEADLINE:
                    if (callOptions.getDeadline() == null) {
                        span.setTag("Deadline", "null");
                    } else {
                        span.setTag("Deadline", callOptions.getDeadline().toString());
                    }
                    break;
                case METHOD_NAME:
                    span.setTag("Method Name", method.getFullMethodName());
                    break;
                case METHOD_TYPE:
                    if (method.getType() == null) {
                        span.setTag("Method Type", "null");
                    } else {
                        span.setTag("Method Type", method.getType().toString());
                    }
                    break;
            }
        }

        return new ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {
            @Override
            public void start(Listener<RespT> responseListener, Metadata headers) {
                if (verbose) { span.log("Started call", null); }
                if (tracedAttributes.contains(ClientRequestAttribute.HEADERS)) { span.setTag("Headers", headers.toString()); }

                tracer.inject(span.context(), Format.Builtin.HTTP_HEADERS, new TextMap() {
                    @Override
                    public Iterator<Map.Entry<String, String>> getEntries() {
                        throw new UnsupportedOperationException(
                            "TextMapInjectAdapter should only be used with Tracer.inject()");
                    }
                    @Override
                    public void put(String key, String value) {
                        Metadata.Key<String> headerKey = Metadata.Key.of(key, Metadata.ASCII_STRING_MARSHALLER);
                        headers.put(headerKey, value);
                    }
                });                    
                Listener<RespT> tracingResponseListener = new ForwardingClientCallListener.SimpleForwardingClientCallListener<RespT>(responseListener) {
                    @Override
                    public void onHeaders(Metadata headers) {
                        if (verbose) { span.log("Response headers received", headers.toString()); }
                    }

                    @Override
                    public void onMessage(RespT message) {
                        if (verbose) { span.log("Response received", null); }
                        delegate().onMessage(message);
                    }

                    @Override 
                    public void onClose(Status status, Metadata trailers) {
                        if (verbose) { 
                            if (status.getCode().value() == 0) { span.log("Call closed", null); }
                            else { span.log("Call failed", status.getDescription()); }
                        }
                        span.finish();
                        delegate().onClose(status, trailers);
                    }
                };
                delegate().start(tracingResponseListener, headers);
            }

            @Override 
            public void cancel(@Nullable String message, @Nullable Throwable cause) {
                // if (verbose) { 
                    String errorMessage;
                    if (message == null) {
                        errorMessage = "Error";
                    } else {
                        errorMessage = message;
                    }
                    if (cause == null) {
                        span.log(errorMessage, null);
                    } else {
                        span.log(errorMessage, cause.getMessage());
                    }
                // }
                delegate().cancel(message, cause);
            }

            @Override
            public void halfClose() {
                if (verbose) { span.log("Finished sending messages", null); }
                delegate().halfClose();
            }

            @Override
            public void sendMessage(ReqT message) {
                if (streaming) { span.log("Message sent", null); }
                delegate().sendMessage(message);
            }
        };
    }
    
    private Span createSpanFromParent(Span parentSpan, String operationName) {
        if (parentSpan == null) {
            return tracer.buildSpan(operationName).start();
        } else {
            return tracer.buildSpan(operationName).asChildOf(parentSpan).start();
        }
    }

    public static class Builder {

        private Tracer tracer;
        private String operationName;
        private boolean streaming;
        private boolean verbose;
        private Set<ClientRequestAttribute> tracedAttributes;  

        public Builder(Tracer tracer) {
            this.tracer = tracer;
            this.operationName = "";
            this.streaming = false;
            this.verbose = false;
            this.tracedAttributes = new HashSet<ClientRequestAttribute>();
        } 

        public Builder withOperationName(String operationName) {
            this.operationName = operationName;
            return this;
        } 

        public Builder withStreaming() {
            this.streaming = true;
            return this;
        }

        public Builder withTracedAttributes(ClientRequestAttribute... tracedAttributes) {
            this.tracedAttributes = new HashSet<ClientRequestAttribute>(Arrays.asList(tracedAttributes));
            return this;
        }

        public Builder withVerbosity() {
            this.verbose = true;
            return this;
        }

        public ClientTracingInterceptor build() {
            return new ClientTracingInterceptor(this.tracer, this.operationName, this.streaming, this.verbose, this.tracedAttributes);
        }
    
    }
}
