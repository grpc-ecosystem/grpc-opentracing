import unittest

import grpc

from _service import Service, ErroringHandler
from _tracer import Tracer, SpanRelationship
from grpc_opentracing import open_tracing_client_interceptor, open_tracing_server_interceptor


class OpenTracingTest(unittest.TestCase):
  """Test that tracers create the correct spans when RPC calls are invoked."""

  def setUp(self):
    self._tracer = Tracer()
    self._service = Service([open_tracing_client_interceptor(self._tracer)],
                            [open_tracing_server_interceptor(self._tracer)])

  def testUnaryUnaryOpenTracing(self):
    multi_callable = self._service.unary_unary_multi_callable
    request = b'\x01'
    expected_response = self._service.handler.handle_unary_unary(request, None)
    response = multi_callable(request)

    self.assertEqual(response, expected_response)

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertEqual(span0.get_tag('span.kind'), 'client')

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertEqual(span1.get_tag('span.kind'), 'server')

    self.assertEqual(
        self._tracer.get_relationship(0, 1), SpanRelationship.CHILD_OF)

  def testUnaryUnaryOpenTracingWithCall(self):
    multi_callable = self._service.unary_unary_multi_callable
    request = b'\x01'
    expected_response = self._service.handler.handle_unary_unary(request, None)
    response, call = multi_callable.with_call(request)

    self.assertEqual(response, expected_response)
    self.assertIs(grpc.StatusCode.OK, call.code())

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertEqual(span0.get_tag('span.kind'), 'client')

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertEqual(span1.get_tag('span.kind'), 'server')

    self.assertEqual(
        self._tracer.get_relationship(0, 1), SpanRelationship.CHILD_OF)

  def testUnaryStreamOpenTracing(self):
    multi_callable = self._service.unary_stream_multi_callable
    request = b'\x01'
    expected_response = self._service.handler.handle_unary_stream(request, None)
    response = multi_callable(request)

    self.assertEqual(list(response), list(expected_response))

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertEqual(span0.get_tag('span.kind'), 'client')

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertEqual(span1.get_tag('span.kind'), 'server')

    self.assertEqual(
        self._tracer.get_relationship(0, 1), SpanRelationship.CHILD_OF)

  def testStreamUnaryOpenTracing(self):
    multi_callable = self._service.stream_unary_multi_callable
    requests = [b'\x01', b'\x02']
    expected_response = self._service.handler.handle_stream_unary(
        iter(requests), None)
    response = multi_callable(iter(requests))

    self.assertEqual(response, expected_response)

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertEqual(span0.get_tag('span.kind'), 'client')

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertEqual(span1.get_tag('span.kind'), 'server')

    self.assertEqual(
        self._tracer.get_relationship(0, 1), SpanRelationship.CHILD_OF)

  def testStreamUnaryOpenTracingWithCall(self):
    multi_callable = self._service.stream_unary_multi_callable
    requests = [b'\x01', b'\x02']
    expected_response = self._service.handler.handle_stream_unary(
        iter(requests), None)
    response, call = multi_callable.with_call(iter(requests))

    self.assertEqual(response, expected_response)
    self.assertIs(grpc.StatusCode.OK, call.code())

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertEqual(span0.get_tag('span.kind'), 'client')

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertEqual(span1.get_tag('span.kind'), 'server')

    self.assertEqual(
        self._tracer.get_relationship(0, 1), SpanRelationship.CHILD_OF)

  def testStreamStreamOpenTracing(self):
    multi_callable = self._service.stream_stream_multi_callable
    requests = [b'\x01', b'\x02']
    expected_response = self._service.handler.handle_stream_unary(
        iter(requests), None)
    response = multi_callable(iter(requests))

    self.assertEqual(list(response), list(expected_response))

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertEqual(span0.get_tag('span.kind'), 'client')

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertEqual(span1.get_tag('span.kind'), 'server')

    self.assertEqual(
        self._tracer.get_relationship(0, 1), SpanRelationship.CHILD_OF)


class OpenTracingErroringTest(unittest.TestCase):
  """Test that tracer spans set the error tag when erroring RPC are invoked."""

  def setUp(self):
    self._tracer = Tracer()
    self._service = Service([open_tracing_client_interceptor(self._tracer)],
                            [open_tracing_server_interceptor(self._tracer)],
                            ErroringHandler())

  def testUnaryUnaryOpenTracing(self):
    multi_callable = self._service.unary_unary_multi_callable
    request = b'\x01'
    self.assertRaises(grpc.RpcError, multi_callable, request)

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertTrue(span0.get_tag('error'))

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertTrue(span1.get_tag('error'))

  def testUnaryUnaryOpenTracingWithCall(self):
    multi_callable = self._service.unary_unary_multi_callable
    request = b'\x01'
    self.assertRaises(grpc.RpcError, multi_callable.with_call, request)

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertTrue(span0.get_tag('error'))

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertTrue(span1.get_tag('error'))

  def testUnaryStreamOpenTracing(self):
    multi_callable = self._service.unary_stream_multi_callable
    request = b'\x01'
    response = multi_callable(request)
    self.assertRaises(grpc.RpcError, list, response)

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertTrue(span0.get_tag('error'))

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertTrue(span1.get_tag('error'))

  def testStreamUnaryOpenTracing(self):
    multi_callable = self._service.stream_unary_multi_callable
    requests = [b'\x01', b'\x02']
    self.assertRaises(grpc.RpcError, multi_callable, iter(requests))

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertTrue(span0.get_tag('error'))

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertTrue(span1.get_tag('error'))

  def testStreamUnaryOpenTracingWithCall(self):
    multi_callable = self._service.stream_unary_multi_callable
    requests = [b'\x01', b'\x02']
    self.assertRaises(grpc.RpcError, multi_callable.with_call, iter(requests))

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertTrue(span0.get_tag('error'))

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertTrue(span1.get_tag('error'))

  def testStreamStreamOpenTracing(self):
    multi_callable = self._service.stream_stream_multi_callable
    requests = [b'\x01', b'\x02']
    response = multi_callable(iter(requests))
    self.assertRaises(grpc.RpcError, list, response)

    span0 = self._tracer.get_span(0)
    self.assertIsNotNone(span0)
    self.assertTrue(span0.get_tag('error'))

    span1 = self._tracer.get_span(1)
    self.assertIsNotNone(span1)
    self.assertTrue(span1.get_tag('error'))
