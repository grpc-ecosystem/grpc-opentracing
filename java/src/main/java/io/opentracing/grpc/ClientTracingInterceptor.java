package io.opentracing.contrib.grpc;

import io.grpc.ClientInterceptor;

public class ClientTracingInterceptor implements ClientInterceptor {
    
    private final Tracer tracer;

    public ClientTracingInterceptor(Tracer tracer) {
        this.tracer = tracer;
    }

    @Override
    <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
        MethodDescriptor<ReqT, RespT> method, 
        CallOptions callOptions, 
        Channel next
    ) {
        String operationName = method.getFullMethodName();
        // Span parentSpan = OpenTracingContextKey.get();

        return new SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {

            @Override
            public void start(Listener<RespT> responseListener, Metadata headers) {
                Span span = tracer.buildSpan(operationName).start();
                Listener<RespT> tracingResponseListener = new SimpleForwardingClientCallListener<RespT>(responseListener) {
                    @Override 
                    public void onClose(Status status, Metadata trailers) {
                        span.finish();
                    }
                }
                delegate().start(tracingResponseListener, headers);
            }
        };
    } 



}
