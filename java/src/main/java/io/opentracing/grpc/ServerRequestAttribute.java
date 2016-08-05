package io.opentracing.contrib.grpc;

/**
 * List of server request attributes available to be traced.
 */
public enum ServerRequestAttribute {
    HEADERS,
    METHOD_TYPE,
    METHOD_NAME,
    CALL_ATTRIBUTES
}