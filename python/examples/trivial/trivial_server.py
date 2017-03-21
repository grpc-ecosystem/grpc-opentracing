from __future__ import print_function

import time
import sys
import argparse

import grpc
from concurrent import futures
import lightstep

from grpc_opentracing import open_tracing_server_interceptor
from grpc_opentracing.grpcext import intercept_server

import command_line_pb2

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class CommandLine(command_line_pb2.CommandLineServicer):

    def Echo(self, request, context):
        return command_line_pb2.CommandResponse(text=request.text)


def serve():
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
        component_name='trivial-server', access_token=args.access_token)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    tracer_interceptor = open_tracing_server_interceptor(
        tracer, log_payloads=args.log_payloads)
    server = intercept_server(server, tracer_interceptor)

    command_line_pb2.add_CommandLineServicer_to_server(CommandLine(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

    tracer.flush()


if __name__ == '__main__':
    serve()
