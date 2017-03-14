import abc

import six


class UnaryClientInfo(six.with_metaclass(abc.ABCMeta)):
  """Consists of various information about a unary RPC on the client-side.

  Attributes:
    full_method: A string of the full RPC method, i.e., /package.service/method.
    timeout: The length of time in seconds to wait for the computation to
      terminate or be cancelled, or None if this method should block until
      the computation is terminated or is cancelled no matter how long that
      takes.
  """


class UnaryClientInterceptor(six.with_metaclass(abc.ABCMeta)):
  """Invokes custom code when a client-side, unary-unary RPC method is called.
  """

  @abc.abstractmethod
  def intercept_unary(self, request, metadata, client_info, invoker):
    """A function to be called when a client-side, unary-unary RPC method is
          invoked.

    Args:
      request: The request value for the RPC.
      metadata: Optional :term:`metadata` to be transmitted to the
        service-side of the RPC.
      client_info: A UnaryClientInfo containing various information about
        the RPC.
      invoker: The handler to complete the RPC on the client. It is the
        interceptor's responsibility to call it.

    Returns:
      The result from calling invoker(request, metadata).
    """
    raise NotImplementedError()


class StreamClientInfo(six.with_metaclass(abc.ABCMeta)):
  """Consists of various information about a stream RPC on the client-side.

  Attributes:
    full_method: A string of the full RPC method, i.e., /package.service/method.
    is_client_stream: Indicates whether the RPC is client-streaming.
    is_server_stream: Indicates whether the RPC is server-streaming.
    timeout: The length of time in seconds to wait for the computation to
      terminate or be cancelled, or None if this method should block until
      the computation is terminated or is cancelled no matter how long that
      takes.
  """


class StreamClientInterceptor(six.with_metaclass(abc.ABCMeta)):
  """Invokes custom code when a client-side, unary-stream, stream-unary, or
      stream-stream RPC method is called.
  """

  @abc.abstractmethod
  def intercept_stream(self, metadata, client_info, invoker):
    """A function to be called when a client-side, unary-stream,
          stream-unary, or stream-stream RPC method is invoked.

    Args:
      metadata: Optional :term:`metadata` to be transmitted to the service-side
        of the RPC.
      client_info: A StreamClientInfo containing various information about
        the RPC.
      invoker:  The handler to complete the RPC on the client. It is the
        interceptor's responsibility to call it.

      Returns:
        The result from calling invoker(metadata).
    """
    raise NotImplementedError()


def intercept_channel(channel, *interceptors):
  """Creates a new Channel that invokes the given interceptors if their
    targeted RPC types are called.

  Args:
    channel: A Channel.
    interceptors: Zero or more UnaryClientInterceptors or
      StreamClientInterceptors

  Returns:
    A Channel.

  Raises:
    TypeError: If an interceptor derives from neither UnaryClientInterceptor
      nor StreamClientInterceptor.
  """
  from grpc_opentracing.grpcext import _interceptor
  return _interceptor.intercept_channel(channel, *interceptors)


class UnaryServerInfo(six.with_metaclass(abc.ABCMeta)):
  """Consists of various information about a unary RPC on the server-side.

  Attributes:
    full_method: A string of the full RPC method, i.e., /package.service/method.
  """


class StreamServerInfo(six.with_metaclass(abc.ABCMeta)):
  """Consists of various information about a stream RPC on the server-side.

  Attributes:
    full_method: A string of the full RPC method, i.e., /package.service/method.
    is_client_stream: Indicates whether the RPC is client-streaming.
    is_server_stream: Indicates whether the RPC is server-streaming.
  """


class UnaryServerInterceptor(six.with_metaclass(abc.ABCMeta)):
  """Invokes custom code when a server-side, unary-unary RPC method is called.
  """

  @abc.abstractmethod
  def intercept_unary(self, request, servicer_context, server_info, handler):
    """A function to be called when a server-side, unary-unary RPC method is
          invoked.

    Args:
      request: The request value for the RPC.
      servicer_context: A ServicerContext.
      server_info: A UnaryServerInfo containing various information about
        the RPC.
      handler:  The handler to complete the RPC on the server. It is the
        interceptor's responsibility to call it.

    Returns:
      The result from calling handler(request, servicer_context).
    """
    raise NotImplementedError()


class StreamServerInterceptor(six.with_metaclass(abc.ABCMeta)):
  """Invokes custom code when a server-side, unary-stream, stream-unary, or
      stream-stream, RPC method is called.
  """

  @abc.abstractmethod
  def intercept_stream(self, servicer_context, server_info, handler):
    """A function to be called when a server-side, unary-stream,
      stream-unary, or stream-stream RPC method is invoked.

    Args:
      servicer_context: A ServicerContext.
      server_info: A StreamServerInfo containing various information about
        the RPC.
      handler:  The handler to complete the RPC on the server. It is the
        interceptor's responsibility to call it.

      Returns:
        The result from calling handler(servicer_context).
    """
    raise NotImplementedError()


def intercept_server(server, *interceptors):
  """Creates a new Channel that invokes the given interceptors if their
    targeted RPC types are called.

  Args:
    server: A Server.
    interceptors: Zero or more UnaryServerInterceptors or
      StreamServerInterceptors

  Returns:
    A Server.

  Raises:
    TypeError: If an interceptor derives from neither UnaryServerInterceptor
      nor StreamServerInterceptor.
  """
  from grpc_opentracing.grpcext import _interceptor
  return _interceptor.intercept_server(server, *interceptors)


###################################  __all__  #################################

__all__ = ('UnaryClientInterceptor', 'StreamClientInfo',
           'StreamClientInterceptor', 'UnaryServerInfo', 'StreamServerInfo',
           'UnaryServerInterceptor', 'StreamServerInterceptor',
           'intercept_channel', 'intercept_server',)
