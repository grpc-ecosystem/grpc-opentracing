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
    
    // TODO: use builder to make configurable

    private final Tracer tracer;

    public ServerTracingInterceptor(Tracer tracer) {
        System.out.println("creating ServerTracingInterceptor");
        this.tracer = tracer;
    }
    
    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
        ServerCall<ReqT, RespT> call, 
        Metadata headers, 
        ServerCallHandler<ReqT, RespT> next
    ) {
        System.out.println("intercepting server call");
        String EXTRACT_FAIL_MSG = "Extract failed and an IllegalArgumentException was thrown";
        String ERROR = "Error";

        Map<String, String> headerMap = new HashMap<String, String>();
        for (String key : headers.keys()) {
            String value = headers.get(Metadata.Key.of(key, Metadata.ASCII_STRING_MARSHALLER));
            headerMap.put(key, value);
        }
        System.out.println("headers: " + headerMap.toString());
        String operationName = call.getMethodDescriptor().getFullMethodName();

        return new ForwardingServerCallListener.SimpleForwardingServerCallListener<ReqT>(next.startCall(call, headers)) {

            private Context previousCtx = Context.ROOT;

            @Override
            public void onMessage(ReqT message) {
                System.out.println("server running onMessage");
                Span span;

                try {
                    SpanContext parentSpanCtx = tracer.extract(Format.Builtin.HTTP_HEADERS, new TextMapExtractAdapter(headerMap));
                    if (parentSpanCtx == null) {
                        span = tracer.buildSpan(operationName).start();
                    } else {
                        span = tracer.buildSpan(operationName).asChildOf(parentSpanCtx).start();
                    }
                } catch (IllegalArgumentException iae){
                    span = tracer.buildSpan(operationName).withTag(ERROR, EXTRACT_FAIL_MSG).start();
                }    
                span.setTag("server at:", System.currentTimeMillis());    

                OpenTracingContextKey.activeSpan().get();        

                // System.out.println("Current context (before)");
                // System.out.println(Context.current());

                Context ctxWithSpan = Context.current().withValue(OpenTracingContextKey.activeSpan(), span);

                // System.out.println("Current context (after, should be same)");
                // System.out.println(Context.current());
                // System.out.println("ctxWithSpan, should be different?");
                // System.out.println(ctxWithSpan);

                // this.previousCtx = ctxWithSpan.attach();

                // System.out.println("previous ctx (Should be like first 2)");
                // System.out.println(previousCtx);
                // System.out.println("current context now (Should be like 3rd)");
                // System.out.println(Context.current());

                delegate().onMessage(message);

                System.out.println("finished onMessage");
            }

            @Override
            public void onCancel() {
                System.out.println("Server running onCancel");
                System.out.println("context: " + Context.current().toString());
                OpenTracingContextKey.activeSpan().get().finish();
                // Context.current().detach(this.previousCtx);
                delegate().onCancel();
                System.out.println("finished onCancel");
            }

            @Override
            public void onComplete() {
                System.out.println("server running onComplete");
                System.out.println("context: " + Context.current().toString());
                try {
                    OpenTracingContextKey.activeSpan().get();
                } catch (NullPointerException npe) {
                    System.out.println("there was no server span to finish :(");
                }
                // Context.current().detach(this.previousCtx);
                delegate().onComplete();
                System.out.println("finished onComplete");
            }
        };


        // return next.startCall(new SimpleForwardingServerCall<ReqT, RespT>(call) {
        //     @Override
        //     public void close(Status status, Metadata trailers) {
        //         span.finish();
        //         delegate().close(status, trailers);
        //     }
        // }, headers);


        // return new ServerCallHandler<RequestT, ResponseT>() {
        //     @Override
        //     ServerCall.Listener<RequestT> startCall(ServerCall<RequestT, ResponseT> call, Metadata headers) {
        //         return new ServerCall.Listener<ReqT> {
        //             @Override
        //             public void onCancel() {

        //             }
        //         }
        //     }
        // }


        // System.out.println("Contexts in interceptor");
        // System.out.println(OpenTracingContextKey.get().get());

        // ServerCall.Listener<ReqT> listener = next.startCall(call, headers);


        // System.out.println("call was started");
        // try {
        //     Thread.sleep(1000);
        // } catch (Exception e) {
        //     System.out.println("Thread did not sleep");
        // }
        // ctxWithSpan.detach(previousCtx);

        // System.out.println("context was detached");
        // span.finish(); 
    }
}


// Note on streaming requests/responses:
// Unary request/response - start span on Listener.onMessage, end span on Listener.onComplete/onCancel
// Streaming request/single response - start span for first request, end on the last response
// Single request/streaming response - start span on Listener.onMessage, end span on 
