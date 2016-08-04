package io.opentracing.contrib.grpc;

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