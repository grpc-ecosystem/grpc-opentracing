package io.opentracing.contrib;

import io.opentracing.NoopTracerFactory;
import io.opentracing.Tracer;

import java.util.Iterator;
import java.util.ServiceLoader;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Tracer Implementation Loader.
 * <p>
 * The loader uses {@link java.util.ServiceLoader} to get {@link Tracer} implemetation.
 * <p>
 * The loader make sure in the classpath, there is only one implementation,
 * if exist more than one,
 * loader will use {@link io.opentracing.NoopTracer} instead, to avoid implicit choice.
 * <p>
 *
 * Created by wusheng on 2016/12/21.
 */
public class TracerLoader {
    private static final Logger LOGGER = Logger.getLogger(TracerLoader.class.getName());

    /**
     * Use ServiceLoader to get a tracer instance.
     * The mechanism comes from many rpc framework and globalTracer-java,
     * if more than one implementations of tracer, would not choose any of them.
     *
     * @return
     */
    static Tracer load() {
        Iterator<Tracer> tracerIterator = ServiceLoader.load(Tracer.class).iterator();
        Tracer tracer;
        if (tracerIterator.hasNext()) {
            tracer = tracerIterator.next();
            if (tracerIterator.hasNext()) {
                LOGGER.log(Level.WARNING, "More than one Tracer service implementation found. " + "Falling back to NoopTracer implementation.");
                tracer = NoopTracerFactory.create();
            }
        } else {
            tracer = NoopTracerFactory.create();
        }
        return tracer;
    }
}
