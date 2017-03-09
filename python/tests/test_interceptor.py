import unittest

import grpc
from grpc_opentracing import grpcext

from service import Service


class ClientInterceptor(grpcext.UnaryClientInterceptor,
                        grpcext.StreamClientInterceptor):

  def __init__(self):
    self.intercepted = False

  def intercept_unary(self, method, request, metadata, invoker):
    self.intercepted = True
    return invoker(request, metadata)

  def intercept_stream(self, metadata, client_info, invoker):
    self.intercepted = True
    return invoker(metadata)


class ServerInterceptor(grpcext.UnaryServerInterceptor,
                        grpcext.StreamServerInterceptor):

  def __init__(self):
    self.intercepted = False

  def intercept_unary(self, request, servicer_context, server_info, handler):
    self.intercepted = True
    return handler(request)

  def intercept_stream(self, servicer_context, server_info, handler):
    self.intercepted = True
    return handler()


class InterceptorTest(unittest.TestCase):

  def setUp(self):
    self._client_interceptor = ClientInterceptor()
    self._server_interceptor = ServerInterceptor()
    self._service = Service([self._client_interceptor],
                            [self._server_interceptor])

  def _clear(self):
    self._client_interceptor.intercepted = False
    self._server_interceptor.intercepted = False

  def testUnaryUnaryInterception(self):
    self._clear()
    multi_callable = self._service.unary_unary_multi_callable
    request = b'\x01'
    expected_response = self._service.handler.handle_unary_unary(request, None)
    response = multi_callable(request)

    self.assertEqual(response, expected_response)
    self.assertTrue(self._client_interceptor.intercepted)
    self.assertTrue(self._server_interceptor.intercepted)

  def testUnaryUnaryInterceptionWithCall(self):
    self._clear()
    multi_callable = self._service.unary_unary_multi_callable
    request = b'\x01'
    expected_response = self._service.handler.handle_unary_unary(request, None)
    response, call = multi_callable.with_call(request)

    self.assertEqual(response, expected_response)
    self.assertIs(grpc.StatusCode.OK, call.code())
    self.assertTrue(self._client_interceptor.intercepted)
    self.assertTrue(self._server_interceptor.intercepted)

  def testUnaryUnaryInterceptionFuture(self):
    self._clear()
    multi_callable = self._service.unary_unary_multi_callable
    request = b'\x01'
    expected_response = self._service.handler.handle_unary_unary(request, None)
    response = multi_callable.future(request).result()

    self.assertEqual(response, expected_response)
    self.assertTrue(self._client_interceptor.intercepted)
    self.assertTrue(self._server_interceptor.intercepted)

  def testUnaryStreamInterception(self):
    self._clear()
    multi_callable = self._service.unary_stream_multi_callable
    request = b'\x01'
    expected_response = self._service.handler.handle_unary_stream(request, None)
    response = multi_callable(request)

    self.assertEqual(list(response), list(expected_response))
    self.assertTrue(self._client_interceptor.intercepted)
    self.assertTrue(self._server_interceptor.intercepted)

  def testStreamUnaryInterception(self):
    self._clear()
    multi_callable = self._service.stream_unary_multi_callable
    requests = [b'\x01', b'\x02']
    expected_response = self._service.handler.handle_stream_unary(
        iter(requests), None)
    response = multi_callable(iter(requests))

    self.assertEqual(response, expected_response)
    self.assertTrue(self._client_interceptor.intercepted)
    self.assertTrue(self._server_interceptor.intercepted)

  def testStreamUnaryInterceptionWithCall(self):
    self._clear()
    multi_callable = self._service.stream_unary_multi_callable
    requests = [b'\x01', b'\x02']
    expected_response = self._service.handler.handle_stream_unary(
        iter(requests), None)
    response, call = multi_callable.with_call(iter(requests))

    self.assertEqual(response, expected_response)
    self.assertIs(grpc.StatusCode.OK, call.code())
    self.assertTrue(self._client_interceptor.intercepted)
    self.assertTrue(self._server_interceptor.intercepted)

  def testStreamUnaryInterceptionFuture(self):
    self._clear()
    multi_callable = self._service.stream_unary_multi_callable
    requests = [b'\x01', b'\x02']
    expected_response = self._service.handler.handle_stream_unary(
        iter(requests), None)
    response = multi_callable.future(iter(requests)).result()

    self.assertEqual(response, expected_response)
    self.assertTrue(self._client_interceptor.intercepted)
    self.assertTrue(self._server_interceptor.intercepted)

  def testStreamStreamInterception(self):
    self._clear()
    multi_callable = self._service.stream_stream_multi_callable
    requests = [b'\x01', b'\x02']
    expected_response = self._service.handler.handle_stream_unary(
        iter(requests), None)
    response = multi_callable(iter(requests))

    self.assertEqual(list(response), list(expected_response))
    self.assertTrue(self._client_interceptor.intercepted)
    self.assertTrue(self._server_interceptor.intercepted)


class InterceptorTest(unittest.TestCase):

  def setUp(self):
    self._client_interceptors = [ClientInterceptor(), ClientInterceptor()]
    self._server_interceptors = [ServerInterceptor(), ServerInterceptor()]
    self._service = Service(self._client_interceptors,
                            self._server_interceptors)

  def _clear(self):
    for client_interceptor in self._client_interceptors:
      client_interceptor.intercepted = False

    for server_interceptor in self._server_interceptors:
      server_interceptor.intercepted = False

  def testUnaryUnaryMultiInterception(self):
    self._clear()
    multi_callable = self._service.unary_unary_multi_callable
    request = b'\x01'
    expected_response = self._service.handler.handle_unary_unary(request, None)
    response = multi_callable(request)

    self.assertEqual(response, expected_response)
    for client_interceptor in self._client_interceptors:
      self.assertTrue(client_interceptor.intercepted)
    for server_interceptor in self._server_interceptors:
      self.assertTrue(server_interceptor.intercepted)
