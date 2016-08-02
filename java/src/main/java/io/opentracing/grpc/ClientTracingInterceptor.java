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


public class ClientTracingInterceptor implements ClientInterceptor {
    
    private final Tracer tracer;

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
        String operationName = method.getFullMethodName();
        System.out.println("context: " + Context.current().toString());

        return new ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {

            @Override
            public void start(Listener<RespT> responseListener, Metadata headers) {
                System.out.println("Starting SimpleForwardingClientCall");
                Span tempSpan;
                System.out.println("context: " + Context.current().toString());
                try {
                    Span parentSpan = OpenTracingContextKey.activeSpan().get();
                    if (parentSpan == null) {
                        tempSpan = tracer.buildSpan(operationName).start();
                        System.out.println("parent was null");
                    } else {
                        tempSpan = tracer.buildSpan(operationName).asChildOf(parentSpan).start();
                        System.out.println("parent was not null");
                    }
                } catch (Exception e) {
                    System.out.println(e.getClass());
                    tempSpan = tracer.buildSpan(operationName).start();
                    System.out.println("parent was null (See error above)");
                }
                final Span span = tempSpan;
                span.setTag("client at: ", System.currentTimeMillis());

                Listener<RespT> tracingResponseListener = new ForwardingClientCallListener.SimpleForwardingClientCallListener<RespT>(responseListener) {
                    @Override 
                    public void onClose(Status status, Metadata trailers) {
                        System.out.println("running client onClose");
                        span.finish();
                        delegate().onClose(status, trailers);
                        System.out.println("finished client onClose");
                    }
                };

                System.out.println("Finished starting SimpleForwardingClientCall, moving onto delegate method");

                delegate().start(tracingResponseListener, headers);
            }
        };
    } 



}
