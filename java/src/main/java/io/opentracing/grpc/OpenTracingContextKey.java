package io.opentracing.contrib.grpc;

import io.grpc.Context;

import io.opentracing.Span;

public class OpenTracingContextKey {
    
    private static final Context.Key<Span> key = Context.key("ot-active-span");

    public static Span activeSpan() {
        return key.get();
    }

    public static Context.Key<Span> getKey() {
        return key;
    }
}