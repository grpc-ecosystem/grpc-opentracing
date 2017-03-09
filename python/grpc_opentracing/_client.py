"""Implementation of the client-side open-tracing interceptor."""

import sys
import logging

from six import iteritems

import grpc
from grpc_opentracing import grpcext
import opentracing


def _inject_span_context(tracer, span, metadata):
  headers = {}
  try:
    tracer.inject(span.context, opentracing.Format.HTTP_HEADERS, headers)
  except (opentracing.UnsupportedFormatException,
          opentracing.InvalidCarrierException,
          opentracing.SpanContextCorruptedException) as e:
    logging.exception('tracer.inject() failed')
    span.log_kv({'event': 'error', 'error.object': e})
    return metadata
  metadata = () if metadata is None else tuple(metadata)
  return metadata + tuple(iteritems(headers))


class OpenTracingClientInterceptor(grpcext.UnaryClientInterceptor,
                                   grpcext.StreamClientInterceptor):

  def __init__(self, tracer, active_span_source, log_payloads):
    self._tracer = tracer
    self._active_span_source = active_span_source
    self._log_payloads = log_payloads

  def _start_span(self, method):
    active_span_context = None
    if self._active_span_source is not None:
      active_span = self._active_span_source.get_active_span()
      if active_span is not None:
        active_span_context = active_span.context
    # TODO: add peer.hostname, peer.ipv4, and other RPC fields that are
    # mentioned on
    # https://github.com/opentracing/specification/blob/master/semantic_conventions.md
    tags = {'component': 'grpc', 'span.kind': 'client'}
    return self._tracer.start_span(
        operation_name=method, child_of=active_span_context, tags=tags)

  def intercept_unary(self, method, request, metadata, invoker):
    with self._start_span(method) as span:
      metadata = _inject_span_context(self._tracer, span, metadata)
      if self._log_payloads:
        span.log_kv({'request': request})
      try:
        result = invoker(request, metadata)
      except:
        e = sys.exc_info()[0]
        span.set_tag('error', True)
        span.log_kv({'event': 'error', 'error.object': e})
        raise
      # If the RPC is called asynchronously, don't log responses.
      if self._log_payloads and not isinstance(result, grpc.Future):
        response = result
        # Handle the case when the RPC is initiated via the with_call
        # method and the result is a tuple with the first element as the
        # response.
        # http://www.grpc.io/grpc/python/grpc.html#grpc.UnaryUnaryMultiCallable.with_call
        if isinstance(result, tuple):
          response = result[0]
        span.log_kv({'response': response})
      return result

  # For RPCs that stream responses, the result can be a generator. To record
  # the span across the generated responses and detect any errors, we wrap the
  # result in a new generator that yields the response values.
  def _intercept_server_stream(self, metadata, client_info, invoker):
    with self._start_span(client_info.full_method) as span:
      metadata = _inject_span_context(self._tracer, span, metadata)
      try:
        result = invoker(metadata)
        for response in result:
          yield response
      except:
        e = sys.exc_info()[0]
        span.set_tag('error', True)
        span.log_kv({'event': 'error', 'error.object': e})
        raise

  def intercept_stream(self, metadata, client_info, invoker):
    if client_info.is_server_stream:
      return self._intercept_server_stream(metadata, client_info, invoker)
    with self._start_span(client_info.full_method) as span:
      metadata = _inject_span_context(self._tracer, span, metadata)
      try:
        return invoker(metadata)
      except:
        e = sys.exc_info()[0]
        span.set_tag('error', True)
        span.log_kv({'event': 'error', 'error.object': e})
        raise
