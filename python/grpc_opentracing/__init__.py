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


@enum.unique
class ClientRequestAttribute(enum.Enum):
  """Optional tracing tags available on the client-side.

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


@enum.unique
class ServerRequestAttribute(enum.Enum):
  """Optional tracing tags available on the server-side.

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


def open_tracing_client_interceptor(tracer,
                                    active_span_source=None,
                                    log_payloads=False,
                                    traced_attributes=None):
  """Creates a client-side interceptor that can be use with gRPC to add
         OpenTracing information.

    Args:
      tracer: An object implmenting the opentracing.Tracer interface.
      active_span_source: An optional ActiveSpanSource to customize how the
        active span is determined.
      log_payloads: Indicates whether requests should be logged.

    Returns:
      A client-side interceptor object.
    """
  from grpc_opentracing import _client
  if traced_attributes is None:
    traced_attributes = set()
  else:
    traced_attributes = set(traced_attributes)
  return _client.OpenTracingClientInterceptor(tracer, active_span_source,
                                              log_payloads, traced_attributes)


def open_tracing_server_interceptor(tracer,
                                    log_payloads=False,
                                    traced_attributes=None):
  """Creates a server-side interceptor that can be use with gRPC to add
         OpenTracing information.

    Args:
      tracer: An object implmenting the opentracing.Tracer interface.
      log_payloads: Indicates whether requests should be logged.

    Returns:
      A server-side interceptor object.
    """
  from grpc_opentracing import _server
  if traced_attributes is None:
    traced_attributes = set()
  else:
    traced_attributes = set(traced_attributes)
  return _server.OpenTracingServerInterceptor(tracer, log_payloads,
                                              traced_attributes)


###################################  __all__  #################################

__all__ = ('ActiveSpanSource', 'ClientRequestAttribute',
           'ServerRequestAttribute', 'open_tracing_client_interceptor',
           'open_tracing_server_interceptor',)
