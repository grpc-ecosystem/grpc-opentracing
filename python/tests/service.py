"""Creates a simple service on top of gRPC for testing."""

import grpc
from grpc.framework.foundation import logging_pool
from otgrpc import grpcext

_SERIALIZE_REQUEST = lambda bytestring: bytestring
_DESERIALIZE_REQUEST = lambda bytestring: bytestring
_SERIALIZE_RESPONSE = lambda bytestring: bytestring
_DESERIALIZE_RESPONSE = lambda bytestring: bytestring

UNARY_UNARY = '/test/UnaryUnary'
UNARY_STREAM = '/test/UnaryStream'
STREAM_UNARY = '/test/StreamUnary'
STREAM_STREAM = '/test/StreamStream'

_STREAM_LENGTH = 5


class _MethodHandler(grpc.RpcMethodHandler):

  def __init__(self,
               request_streaming=False,
               response_streaming=False,
               unary_unary=None,
               unary_stream=None,
               stream_unary=None,
               stream_stream=None):
    self.request_streaming = request_streaming
    self.response_streaming = response_streaming
    self.request_deserializer = _DESERIALIZE_REQUEST
    self.response_serializer = _SERIALIZE_RESPONSE
    self.unary_unary = unary_unary
    self.unary_stream = unary_stream
    self.stream_unary = stream_unary
    self.stream_stream = stream_stream


class _Handler(object):

  def handle_unary_unary(self, request, servicer_context):
    return request

  def handle_unary_stream(self, request, servicer_context):
    for _ in xrange(_STREAM_LENGTH):
      yield request

  def handle_stream_unary(self, request_iterator, servicer_context):
    return b''.join(list(request_iterator))

  def handle_stream_stream(self, request_iterator, servicer_context):
    for request in request_iterator:
      yield request


class _GenericHandler(grpc.GenericRpcHandler):

  def __init__(self, handler):
    self._handler = handler

  def service(self, handler_call_details):
    print 'servicing: ', handler_call_details.method
    method = handler_call_details.method
    if method == UNARY_UNARY:
      return _MethodHandler(unary_unary=self._handler.handle_unary_unary)
    elif method == UNARY_STREAM:
      return _MethodHandler(
          response_streaming=True,
          unary_stream=self._handler.handle_unary_stream)
    elif method == STREAM_UNARY:
      return _MethodHandler(
          request_streaming=True,
          stream_unary=self._handler.handle_stream_unary)
    elif method == STREAM_STREAM:
      return _MethodHandler(
          request_streaming=True,
          response_streaming=True,
          stream_stream=self._handler.handle_stream_stream)
    else:
      return None


class Service(object):

  def __init__(self, client_interceptors, server_interceptors):
    self.handler = _Handler()
    self._server_pool = logging_pool.pool(2)
    self._server = grpcext.intercept_server(
        grpc.server(self._server_pool), *server_interceptors)
    port = self._server.add_insecure_port('[::]:0')
    self._server.add_generic_rpc_handlers((_GenericHandler(self.handler),))
    self._server.start()
    self.channel = grpcext.intercept_channel(
        grpc.insecure_channel('localhost:%d' % port), *client_interceptors)

  @property
  def unary_unary_multi_callable(self):
    return self.channel.unary_unary(UNARY_UNARY)

  @property
  def unary_stream_multi_callable(self):
    return self.channel.unary_stream(
        UNARY_STREAM,
        request_serializer=_SERIALIZE_REQUEST,
        response_deserializer=_DESERIALIZE_RESPONSE)

  @property
  def stream_unary_multi_callable(self):
    return self.channel.stream_unary(
        STREAM_UNARY,
        request_serializer=_SERIALIZE_REQUEST,
        response_deserializer=_DESERIALIZE_RESPONSE)

  @property
  def stream_stream_multi_callable(self):
    return self.channel.stream_stream(
        STREAM_STREAM,
        request_serializer=_SERIALIZE_REQUEST,
        response_deserializer=_DESERIALIZE_RESPONSE)
