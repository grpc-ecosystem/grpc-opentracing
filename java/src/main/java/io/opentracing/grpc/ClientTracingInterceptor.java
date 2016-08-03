package io.opentracing.contrib.grpc;

import io.grpc.ClientInterceptor;
import io.grpc.ClientCall;
import io.grpc.MethodDescriptor;
import io.grpc.CallOptions;
import io.grpc.Channel;
import io.grpc.ForwardingClientCall;
import io.grpc.ForwardingClientCallListener;
import io.grpc.ClientCall.Listener;
import io.grpc.Metadata;
import io.grpc.Status;
import io.grpc.Context;

import io.opentracing.contrib.grpc.OpenTracingContextKey;
import io.opentracing.Tracer;
import io.opentracing.Span;
import io.opentracing.propagation.TextMap;
import io.opentracing.propagation.Format;

import java.util.Iterator;
import java.util.Map;

public class ClientTracingInterceptor implements ClientInterceptor {
    
    private final Tracer tracer;
    // options for Client Tracing:
    //  method.getType (unary, streaming, etc)
    //  method.getFullMethodName
    //  callOptions.getDeadline
    //  callOptions.getCompressor
    //  callOptions.getAffinity
    //  callOptions.getAuthority
    //  or just callOptions.toString()
    //  headers.toString()
    //  withLoggingOfStreaming
    //  set method name manually

    public ClientTracingInterceptor(Tracer tracer) {
        this.tracer = tracer;
        System.out.println("ClientTracingInterceptor created");
    }

    @Override
    public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
        MethodDescriptor<ReqT, RespT> method, 
        CallOptions callOptions, 
        Channel next
    ) {
        System.out.println("Intercepting client call");
        final String operationName = method.getFullMethodName();
        System.out.println("operation name: " + operationName);

        return new ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {

            @Override
            public void start(Listener<RespT> responseListener, Metadata headers) {
                System.out.println("Starting SimpleForwardingClientCall");

                Span activeSpan = OpenTracingContextKey.activeSpan();
                final Span span  = createSpanFromParent(activeSpan, operationName);
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

                span.setTag("client at: ", System.currentTimeMillis());
                System.out.println("span is " + span.toString());

                Listener<RespT> tracingResponseListener = new ForwardingClientCallListener.SimpleForwardingClientCallListener<RespT>(responseListener) {
                    @Override 
                    public void onClose(Status status, Metadata trailers) {
                        System.out.println("running client onClose");
                        span.finish();
                        System.out.println("finished " + span.toString());
                        delegate().onClose(status, trailers);
                    }
                };

                delegate().start(tracingResponseListener, headers);
            }
        };
    } 
    private Span createSpanFromParent(Span span, String operationName) {
        if (span == null) {
            return tracer.buildSpan(operationName).start();
        } else {
            return tracer.buildSpan(operationName).asChildOf(span).start();
        }
    }
}
