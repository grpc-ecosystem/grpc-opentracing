import abc

import six


class ActiveSpanSource(six.with_metaclass(abc.ABCMeta)):
  """Provides a way to customize how the active span is determined."""

  @abc.abstractmethod
  def get_active_span(self):
    """Identifies the active span.

        Returns:
          An object that implements the opentracing.Span interface.
        """


def open_tracing_client_interceptor(tracer,
                                    active_span_source=None,
                                    log_payloads=False):
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
  from otgrpc import _client
  return _client.OpenTracingClientInterceptor(tracer, active_span_source,
                                              log_payloads)


def open_tracing_server_interceptor(tracer, log_payloads=False):
  """Creates a server-side interceptor that can be use with gRPC to add
         OpenTracing information.

    Args:
      tracer: An object implmenting the opentracing.Tracer interface.
      log_payloads: Indicates whether requests should be logged.

    Returns:
      A server-side interceptor object.
    """
  from otgrpc import _server
  return _server.OpenTracingServerInterceptor(tracer, log_payloads)


###################################  __all__  #################################

__all__ = ('ActiveSpanSource', 'open_tracing_client_interceptor',
           'open_tracing_server_interceptor',)
