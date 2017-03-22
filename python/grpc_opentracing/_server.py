"""Implementation of the service-side open-tracing interceptor."""

import sys
import logging
import re

import grpc
from grpc_opentracing import grpcext, ActiveSpanSource, ServerRequestAttribute
from grpc_opentracing._utilities import get_method_type, get_deadline_millis,\
    log_or_wrap_request_or_iterator
import opentracing


class _OpenTracingServicerContext(grpc.ServicerContext, ActiveSpanSource):

    def __init__(self, servicer_context, active_span):
        self._servicer_context = servicer_context
        self._active_span = active_span
        self.code = grpc.StatusCode.OK
        self.details = None

    def is_active(self, *args, **kwargs):
        return self._servicer_context.is_active(*args, **kwargs)

    def time_remaining(self, *args, **kwargs):
        return self._servicer_context.time_remaining(*args, **kwargs)

    def cancel(self, *args, **kwargs):
        return self._servicer_context.cancel(*args, **kwargs)

    def add_callback(self, *args, **kwargs):
        return self._servicer_context.add_callback(*args, **kwargs)

    def invocation_metadata(self, *args, **kwargs):
        return self._servicer_context.invocation_metadata(*args, **kwargs)

    def peer(self, *args, **kwargs):
        return self._servicer_context.peer(*args, **kwargs)

    def send_initial_metadata(self, *args, **kwargs):
        return self._servicer_context.send_initial_metadata(*args, **kwargs)

    def set_trailing_metadata(self, *args, **kwargs):
        return self._servicer_context.set_trailing_metadata(*args, **kwargs)

    def set_code(self, code):
        self.code = code
        return self._servicer_context.set_code(code)

    def set_details(self, details):
        self.details = details
        return self._servicer_context.set_details(details)

    def get_active_span(self):
        return self._active_span


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
    logging.warning('Unrecognized peer: \"%s\"', peer_str)


# On the service-side, errors can be signaled either by exceptions or by calling
# `set_code` on the `servicer_context`. This function checks for the latter and
# updates the span accordingly.
def _check_error_code(span, servicer_context):
    if servicer_context.code != grpc.StatusCode.OK:
        span.set_tag('error', True)
        error_log = {'event': 'error', 'error.kind': str(servicer_context.code)}
        if servicer_context.details is not None:
            error_log['message'] = servicer_context.details
        span.log_kv(error_log)


class OpenTracingServerInterceptor(grpcext.UnaryServerInterceptor,
                                   grpcext.StreamServerInterceptor):

    def __init__(self, tracer, log_payloads, traced_attributes):
        self._tracer = tracer
        self._log_payloads = log_payloads
        self._traced_attributes = traced_attributes

    def _start_span(self, servicer_context, method, is_client_stream,
                    is_server_stream):
        span_context = None
        error = None
        metadata = servicer_context.invocation_metadata()
        try:
            if metadata:
                span_context = self._tracer.extract(
                    opentracing.Format.HTTP_HEADERS, dict(metadata))
        except (opentracing.UnsupportedFormatException,
                opentracing.InvalidCarrierException,
                opentracing.SpanContextCorruptedException) as e:
            logging.exception('tracer.extract() failed')
            error = e
        tags = {'component': 'grpc', 'span.kind': 'server'}
        _add_peer_tags(servicer_context.peer(), tags)
        for traced_attribute in self._traced_attributes:
            if traced_attribute == ServerRequestAttribute.HEADERS:
                tags['grpc.headers'] = str(metadata)
            elif traced_attribute == ServerRequestAttribute.METHOD_TYPE:
                tags['grpc.method_type'] = get_method_type(is_client_stream,
                                                           is_server_stream)
            elif traced_attribute == ServerRequestAttribute.METHOD_NAME:
                tags['grpc.method_name'] = method
            elif traced_attribute == ServerRequestAttribute.DEADLINE:
                tags['grpc.deadline_millis'] = get_deadline_millis(
                    servicer_context.time_remaining())
            else:
                logging.warning('OpenTracing Attribute \"%s\" is not supported',
                                str(traced_attribute))
        span = self._tracer.start_span(
            operation_name=method, child_of=span_context, tags=tags)
        if error is not None:
            span.log_kv({'event': 'error', 'error.object': error})
        return span

    def intercept_unary(self, request, servicer_context, server_info, handler):
        with self._start_span(servicer_context, server_info.full_method, False,
                              False) as span:
            if self._log_payloads:
                span.log_kv({'request': request})
            servicer_context = _OpenTracingServicerContext(servicer_context,
                                                           span)
            try:
                response = handler(request, servicer_context)
            except:
                e = sys.exc_info()[0]
                span.set_tag('error', True)
                span.log_kv({'event': 'error', 'error.object': e})
                raise
            if self._log_payloads:
                span.log_kv({'response': response})
            _check_error_code(span, servicer_context)
            return response

    # For RPCs that stream responses, the result can be a generator. To record
    # the span across the generated responses and detect any errors, we wrap the
    # result in a new generator that yields the response values.
    def _intercept_server_stream(self, request_or_iterator, servicer_context,
                                 server_info, handler):
        with self._start_span(servicer_context, server_info.full_method,
                              server_info.is_client_stream, True) as span:
            servicer_context = _OpenTracingServicerContext(servicer_context,
                                                           span)
            if self._log_payloads:
                request_or_iterator = log_or_wrap_request_or_iterator(
                    span, server_info.is_client_stream, request_or_iterator)
            try:
                result = handler(request_or_iterator, servicer_context)
                for response in result:
                    if self._log_payloads:
                        span.log_kv({'response': response})
                    yield response
            except:
                e = sys.exc_info()[0]
                span.set_tag('error', True)
                span.log_kv({'event': 'error', 'error.object': e})
                raise
            _check_error_code(span, servicer_context)

    def intercept_stream(self, request_or_iterator, servicer_context,
                         server_info, handler):
        if server_info.is_server_stream:
            return self._intercept_server_stream(
                request_or_iterator, servicer_context, server_info, handler)
        with self._start_span(servicer_context, server_info.full_method,
                              server_info.is_client_stream, False) as span:
            servicer_context = _OpenTracingServicerContext(servicer_context,
                                                           span)
            if self._log_payloads:
                request_or_iterator = log_or_wrap_request_or_iterator(
                    span, server_info.is_client_stream, request_or_iterator)
            try:
                response = handler(request_or_iterator, servicer_context)
            except:
                e = sys.exc_info()[0]
                span.set_tag('error', True)
                span.log_kv({'event': 'error', 'error.object': e})
                raise
            if self._log_payloads:
                span.log_kv({'response': response})
            _check_error_code(span, servicer_context)
            return response
