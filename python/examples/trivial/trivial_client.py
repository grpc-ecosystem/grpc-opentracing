from __future__ import print_function

import sys
import argparse

import grpc
import lightstep

from grpc_opentracing import open_tracing_client_interceptor
from grpc_opentracing.grpcext import intercept_channel

import command_line_pb2


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--access_token', help='LightStep Access Token')
    parser.add_argument(
        '--log_payloads',
        action='store_true',
        help='log request/response objects to open-tracing spans')
    args = parser.parse_args()
    if not args.access_token:
        print('You must specify access_token')
        sys.exit(-1)

    tracer = lightstep.Tracer(
        component_name='trivial-client', access_token=args.access_token)
    tracer_interceptor = open_tracing_client_interceptor(
        tracer, log_payloads=args.log_payloads)
    channel = grpc.insecure_channel('localhost:50051')
    channel = intercept_channel(channel, tracer_interceptor)
    stub = command_line_pb2.CommandLineStub(channel)
    response = stub.Echo(command_line_pb2.CommandRequest(text='Hello, hello'))
    print(response.text)

    tracer.flush()


if __name__ == '__main__':
    run()
