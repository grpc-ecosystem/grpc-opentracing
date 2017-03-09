"""Implementation of the server-side open-tracing interceptor."""

import sys
import logging
import re

from grpc_opentracing import grpcext
import opentracing


def _add_peer_tags(peer_str, tags):
  ipv4_re = r"ipv4:(?P<address>.+):(?P<port>\d+)"
  match = re.match(ipv4_re, peer_str)
  if match:
    tags['peer.ipv4'] = match.group('address')
    tags['peer.port'] = match.group('port')
    return
  ipv6_re = r"ipv6:\[(?P<address>.+)\]:(?P<port>\d+)"
  match = re.match(ipv6_re, peer_str)
  if match:
    tags['peer.ipv6'] = match.group('address')
    tags['peer.port'] = match.group('port')
    return
  logging.warning('unrecognized peer: %s', peer_str)


def _start_server_span(tracer, servicer_context, method):
  span_context = None
  error = None
  metadata = servicer_context.invocation_metadata()
  try:
    if metadata:
      span_context = tracer.extract(opentracing.Format.HTTP_HEADERS,
                                    dict(metadata))
  except (opentracing.UnsupportedFormatException,
          opentracing.InvalidCarrierException,
          opentracing.SpanContextCorruptedException) as e:
    logging.exception('tracer.extract() failed')
    error = e
  tags = {'component': 'grpc', 'span.kind': 'server'}
  _add_peer_tags(servicer_context.peer(), tags)
  span = tracer.start_span(
      operation_name=method, child_of=span_context, tags=tags)
  if error is not None:
    span.log_kv({'event': 'error', 'error.object': error})
  return span


class OpenTracingServerInterceptor(grpcext.UnaryServerInterceptor,
                                   grpcext.StreamServerInterceptor):

  def __init__(self, tracer, log_payloads):
    self._tracer = tracer
    self._log_payloads = log_payloads

  def intercept_unary(self, request, servicer_context, server_info, handler):
    with _start_server_span(self._tracer, servicer_context,
                            server_info.full_method) as span:
      response = None
      if self._log_payloads:
        span.log_kv({'request': request})
      try:
        response = handler(request)
      except:
        e = sys.exc_info()[0]
        span.set_tag('error', True)
        span.log_kv({'event': 'error', 'error.object': e})
        raise
      if self._log_payloads:
        span.log_kv({'response': response})
      return response

  # For RPCs that stream responses, the result can be a generator. To record
  # the span across the generated responses and detect any errors, we wrap the
  # result in a new generator that yields the response values.
  def _intercept_server_stream(self, servicer_context, server_info, handler):
    with _start_server_span(self._tracer, servicer_context,
                            server_info.full_method) as span:
      try:
        result = handler()
        for response in result:
          yield response
      except:
        e = sys.exc_info()[0]
        span.set_tag('error', True)
        span.log_kv({'event': 'error', 'error.object': e})
        raise

  def intercept_stream(self, servicer_context, server_info, handler):
    if server_info.is_server_stream:
      return self._intercept_server_stream(servicer_context, server_info,
                                           handler)
    with _start_server_span(self._tracer, servicer_context,
                            server_info.full_method) as span:
      try:
        return handler()
      except:
        e = sys.exc_info()[0]
        span.set_tag('error', True)
        span.log_kv({'event': 'error', 'error.object': e})
        raise
