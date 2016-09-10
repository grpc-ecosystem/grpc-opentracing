# OpenTracing support for gRPC in Go

The `otgrpc` package makes it easy to add OpenTracing support to gRPC-based
systems in Go.

## Installation

```
go get github.com/grpc-ecosystem/grpc-opentracing/go/otgrpc
```

## Usage on the client

Wherever you call `grpc.Dial`:

```
// You must have some sort of OpenTracing Tracer instance on hand.
var tracer opentracing.Tracer = ...
...

// Set up a connection to the server peer.
conn, err := grpc.Dial(
    address,
    ... // other options
    grpc.WithUnaryInterceptor(
        otgrpc.OpenTracingClientInterceptor(tracer)))

// All future RPC activity involving `conn` will be automatically traced.
```

## Usage on the server

Wherever you call `grpc.NewServer`:

```
// You must have some sort of OpenTracing Tracer instance on hand.
var tracer opentracing.Tracer = ...
...

// Initialize the gRPC server.
s := grpc.NewServer(
    ... // other options
    grpc.UnaryInterceptor(
        otgrpc.OpenTracingServerInterceptor(tracer)))

// All future RPC activity involving `s` will be automatically traced.
```

