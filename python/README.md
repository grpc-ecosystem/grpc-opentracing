# OpenTracing support for gRPC in Python

The `grpcio-opentracing` package makes it easy to add OpenTracing support to 
gRPC-based systems in Python.

## Installation

```
pip install grpcio-opentracing
```

## Getting started

See the below code for basic usage or [store](examples/store) for a complete 
example.

### Client-side usage example

```python
tracer = # some OpenTracing Tracer instance
channel = # the grpc.Channel you created to invoke RPCs
channel = intercept_channel(channel, OpenTracingClientInterceptor(tracer))

# All future RPC activity involving `channel` will be automatically traced.
```

### Server-side usage example

```python
tracer = # some OpenTracing Tracer instance
server = # the grpc.Server you created to receive RPCs
server = intercept_server(server, OpenTracingServerInterceptor(tracer))

# All future RPC activity involving `server` will be automatically traced.
```

### Integrating with other OpenTracing code.
