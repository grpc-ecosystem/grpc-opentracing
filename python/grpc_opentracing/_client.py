"""Implementation of the invocation-side open-tracing interceptor."""

import sys
import logging
import time

from six import iteritems

import grpc
from grpc_opentracing import grpcext, ClientRequestAttribute
from grpc_opentracing._utilities import get_method_type, get_deadline_millis,\
    log_or_wrap_request_or_iterator
import opentracing
from opentracing.ext import tags as ot_tags


class _GuardedSpan(object):

    def __init__(self, span):
        self.span = span
        self._engaged = True

    def __enter__(self):
        self.span.__enter__()
        return self

    def __exit__(self, *args, **kwargs):
        if self._engaged:
            return self.span.__exit__(*args, **kwargs)
        else:
            return False

    def release(self):
        self._engaged = False
        return self.span


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


def _make_future_done_callback(span, log_payloads):

    def callback(response_future):
        with span:
            code = response_future.code()
            if code != grpc.StatusCode.OK:
                span.set_tag('error', True)
                error_log = {'event': 'error', 'error.kind': str(code)}
                details = response_future.details()
                if details is not None:
                    error_log['message'] = details
                span.log_kv(error_log)
            elif log_payloads:
                response = response_future.result()
                span.log_kv({'response': response})

    return callback


def _trace_result(guarded_span, log_payloads, result):
    # If the RPC is called asynchronously, release the guard and add a callback
    # so that the span can be finished once the future is done.
    if isinstance(result, grpc.Future):
        result.add_done_callback(
            _make_future_done_callback(guarded_span.release(), log_payloads))
        return result
    elif log_payloads:
        response = result
        # Handle the case when the RPC is initiated via the with_call
        # method and the result is a tuple with the first element as the
        # response.
        # http://www.grpc.io/grpc/python/grpc.html#grpc.UnaryUnaryMultiCallable.with_call
        if isinstance(result, tuple):
            response = result[0]
        guarded_span.span.log_kv({'response': response})
    return result


class OpenTracingClientInterceptor(grpcext.UnaryClientInterceptor,
                                   grpcext.StreamClientInterceptor):

    def __init__(self, tracer, active_span_source, log_payloads,
                 traced_attributes):
        self._tracer = tracer
        self._active_span_source = active_span_source
        self._log_payloads = log_payloads
        self._traced_attributes = traced_attributes

    def _start_span(self, method, metadata, is_client_stream, is_server_stream,
                    timeout):
        active_span_context = None
        if self._active_span_source is not None:
            active_span = self._active_span_source.get_active_span()
            if active_span is not None:
                active_span_context = active_span.context
        tags = {
            ot_tags.COMPONENT: 'grpc',
            ot_tags.SPAN_KIND: ot_tags.SPAN_KIND_RPC_CLIENT
        }
        for traced_attribute in self._traced_attributes:
            if traced_attribute == ClientRequestAttribute.HEADERS:
                tags['grpc.headers'] = str(metadata)
            elif traced_attribute == ClientRequestAttribute.METHOD_TYPE:
                tags['grpc.method_type'] = get_method_type(is_client_stream,
                                                           is_server_stream)
            elif traced_attribute == ClientRequestAttribute.METHOD_NAME:
                tags['grpc.method_name'] = method
            elif traced_attribute == ClientRequestAttribute.DEADLINE:
                tags['grpc.deadline_millis'] = get_deadline_millis(timeout)
            else:
                logging.warning('OpenTracing Attribute \"%s\" is not supported',
                                str(traced_attribute))
        return self._tracer.start_span(
            operation_name=method, child_of=active_span_context, tags=tags)

    def _start_guarded_span(self, *args, **kwargs):
        return _GuardedSpan(self._start_span(*args, **kwargs))

    def intercept_unary(self, request, metadata, client_info, invoker):
        with self._start_guarded_span(client_info.full_method, metadata, False,
                                      False,
                                      client_info.timeout) as guarded_span:
            metadata = _inject_span_context(self._tracer, guarded_span.span,
                                            metadata)
            if self._log_payloads:
                guarded_span.span.log_kv({'request': request})
            try:
                result = invoker(request, metadata)
            except:
                e = sys.exc_info()[0]
                guarded_span.span.set_tag('error', True)
                guarded_span.span.log_kv({'event': 'error', 'error.object': e})
                raise
            return _trace_result(guarded_span, self._log_payloads, result)

    # For RPCs that stream responses, the result can be a generator. To record
    # the span across the generated responses and detect any errors, we wrap the
    # result in a new generator that yields the response values.
    def _intercept_server_stream(self, request_or_iterator, metadata,
                                 client_info, invoker):
        with self._start_span(client_info.full_method, metadata,
                              client_info.is_client_stream, True,
                              client_info.timeout) as span:
            metadata = _inject_span_context(self._tracer, span, metadata)
            if self._log_payloads:
                request_or_iterator = log_or_wrap_request_or_iterator(
                    span, client_info.is_client_stream, request_or_iterator)
            try:
                result = invoker(request_or_iterator, metadata)
                for response in result:
                    if self._log_payloads:
                        span.log_kv({'response': response})
                    yield response
            except:
                e = sys.exc_info()[0]
                span.set_tag('error', True)
                span.log_kv({'event': 'error', 'error.object': e})
                raise

    def intercept_stream(self, request_or_iterator, metadata, client_info,
                         invoker):
        if client_info.is_server_stream:
            return self._intercept_server_stream(request_or_iterator, metadata,
                                                 client_info, invoker)
        with self._start_guarded_span(client_info.full_method, metadata,
                                      client_info.is_client_stream, False,
                                      client_info.timeout) as guarded_span:
            metadata = _inject_span_context(self._tracer, guarded_span.span,
                                            metadata)
            if self._log_payloads:
                request_or_iterator = log_or_wrap_request_or_iterator(
                    guarded_span.span, client_info.is_client_stream,
                    request_or_iterator)
            try:
                result = invoker(request_or_iterator, metadata)
            except:
                e = sys.exc_info()[0]
                guarded_span.span.set_tag('error', True)
                guarded_span.span.log_kv({'event': 'error', 'error.object': e})
                raise
            return _trace_result(guarded_span, self._log_payloads, result)
