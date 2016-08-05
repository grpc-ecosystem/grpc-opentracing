package io.opentracing.contrib.grpc;

import io.grpc.Context;

import io.opentracing.Span;

public class OpenTracingContextKey {
    
    private static final Context.Key<Span> key = Context.key("ot-active-span");

    /**
     * @return the active span for the current request
     */ 
    public static Span activeSpan() {
        return key.get();
    }

    /**
     * @return the OpenTracing context key
     */
    public static Context.Key<Span> getKey() {
        return key;
    }
}