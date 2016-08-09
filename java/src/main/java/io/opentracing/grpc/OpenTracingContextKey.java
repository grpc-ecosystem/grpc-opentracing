package io.opentracing.contrib.grpc;

import io.grpc.Context;

import io.opentracing.Span;

/**
 * A {@link io.grpc.Context} key for the current OpenTracing trace state.
 * 
 * Can be used to get the active span, or to set the active span for a scoped unit of work. 
 * See the <a href="../../../../../../README.rst">grpc-java OpenTracing docs</a> for use cases and examples.
 */
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