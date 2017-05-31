import abc
import enum

import six

import grpc


class ActiveSpanSource(six.with_metaclass(abc.ABCMeta)):
    """Provides a way to access an the active span."""

    @abc.abstractmethod
    def get_active_span(self):
        """Identifies the active span.

    Returns:
      An object that implements the opentracing.Span interface.
    """
        raise NotImplementedError()


class RpcInfo(six.with_metaclass(abc.ABCMeta)):
    """Provides information for an RPC call.

  Attributes:
    full_method: A string of the full RPC method, i.e., /package.service/method.
    metadata: The initial :term:`metadata`.
    timeout: The length of time in seconds to wait for the computation to
      terminate or be cancelled.
    request: The RPC request or None for request-streaming RPCs.
    response: The RPC response or None for response-streaming or erroring RPCs.
    error: The RPC error or None for successful RPCs.
  """


class SpanDecorator(six.with_metaclass(abc.ABCMeta)):
    """Provides a mechanism to add arbitrary tags/logs/etc to the
    opentracing.Span associated with client and/or server RPCs."""

    @abc.abstractmethod
    def __call__(self, span, rpc_info):
        """Customizes an RPC span.

    Args:
      span: The client-side or server-side opentracing.Span for the RPC.
      rpc_info: An RpcInfo describing the RPC.
    """
        raise NotImplementedError()


@enum.unique
class ServerRequestAttribute(enum.Enum):
    """Optional tracing tags available on the service-side.  
  Attributes:
    HEADERS: The initial :term:`metadata`.
    METHOD_TYPE: Type of the method invoked.
    METHOD_NAME: Name of the method invoked.
    DEADLINE: The length of time in seconds to wait for the computation to
      terminate or be cancelled.
  """
    HEADERS = 0
    METHOD_TYPE = 1
    METHOD_NAME = 2
    DEADLINE = 3


def open_tracing_client_interceptor(tracer,
                                    active_span_source=None,
                                    log_payloads=False,
                                    span_decorator=None):
    """Creates an invocation-side interceptor that can be use with gRPC to add
    OpenTracing information.

  Args:
    tracer: An object implmenting the opentracing.Tracer interface.
    active_span_source: An optional ActiveSpanSource to customize how the
      active span is determined.
    log_payloads: Indicates whether requests should be logged.
    span_decorator: An optional SpanDecorator

  Returns:
    An invocation-side interceptor object.
  """
    from grpc_opentracing import _client
    return _client.OpenTracingClientInterceptor(tracer, active_span_source,
                                                log_payloads, span_decorator)


def open_tracing_server_interceptor(tracer,
                                    log_payloads=False,
                                    traced_attributes=None):
    """Creates a service-side interceptor that can be use with gRPC to add
    OpenTracing information.

  Args:
    tracer: An object implmenting the opentracing.Tracer interface.
    log_payloads: Indicates whether requests should be logged.
    traced_attributes: An optional list of ServerRequestAttributes specifying
      additional tags to set on server spans.

  Returns:
    A service-side interceptor object.
  """
    from grpc_opentracing import _server
    if traced_attributes is None:
        traced_attributes = set()
    else:
        traced_attributes = set(traced_attributes)
    return _server.OpenTracingServerInterceptor(tracer, log_payloads,
                                                traced_attributes)


###################################  __all__  #################################

__all__ = ('ActiveSpanSource', 'ServerRequestAttribute',
           'open_tracing_client_interceptor',
           'open_tracing_server_interceptor',)
