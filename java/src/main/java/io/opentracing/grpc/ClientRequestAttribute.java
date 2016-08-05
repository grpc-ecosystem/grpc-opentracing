package io.opentracing.contrib.grpc;

/**
 * List of client request attributes available to be traced.
 */
public enum ClientRequestAttribute {
    METHOD_TYPE,
    METHOD_NAME,
    DEADLINE,
    COMPRESSOR,
    AFFINITY,
    AUTHORITY,
    ALL_CALL_OPTIONS,
    HEADERS
}