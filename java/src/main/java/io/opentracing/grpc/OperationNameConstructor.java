package io.opentracing.contrib.grpc;

public interface OperationNameConstructor {

    public static OperationNameConstructor NOOP = new OperationNameConstructor() {
        @Override
        public String constructOperationName(String extractedName) {
            return extractedName;
        }
    };

    public String constructOperationName(String extractedName);
}