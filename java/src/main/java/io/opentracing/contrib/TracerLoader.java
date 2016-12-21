package io.opentracing.contrib;

import io.opentracing.NoopTracerFactory;
import io.opentracing.Tracer;

import java.util.Iterator;
import java.util.ServiceLoader;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
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
        Tracer tracer = null;
        if (tracerIterator.hasNext()) {
            tracer = tracerIterator.next();
            if (tracerIterator.hasNext()) {
                LOGGER.log(Level.WARNING, "More than one Tracer service implementation found. " + "Falling back to NoopTracer implementation.");
                tracer = NoopTracerFactory.create();
            }
        } else {
            tracer =  NoopTracerFactory.create();
        }
        return tracer;
    }
}
