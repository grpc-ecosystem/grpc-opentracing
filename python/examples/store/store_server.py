# A OpenTraced server for a Python service that implements the store interface.
from __future__ import print_function

import time
import sys
import argparse
from collections import defaultdict

from six import iteritems

import grpc
from concurrent import futures
import lightstep

from grpc_opentracing import open_tracing_server_interceptor, ServerRequestAttribute
from grpc_opentracing.grpcext import intercept_server

import store_pb2

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class Store(store_pb2.StoreServicer):

    def __init__(self):
        self._inventory = defaultdict(int)

    def AddItem(self, request, context):
        self._inventory[request.name] += 1
        return store_pb2.Empty()

    def AddItems(self, request_iter, context):
        for request in request_iter:
            self._inventory[request.name] += 1
        return store_pb2.Empty()

    def RemoveItem(self, request, context):
        new_quantity = self._inventory[request.name] - 1
        if new_quantity < 0:
            return store_pb2.RemoveItemResponse(was_successful=False)
        self._inventory[request.name] = new_quantity
        return store_pb2.RemoveItemResponse(was_successful=True)

    def RemoveItems(self, request_iter, context):
        response = store_pb2.RemoveItemResponse(was_successful=True)
        for request in request_iter:
            response = self.RemoveItem(request, context)
            if not response.was_successful:
                break
        return response

    def ListInventory(self, request, context):
        for name, count in iteritems(self._inventory):
            if not count:
                continue
            else:
                yield store_pb2.QuantityResponse(name=name, count=count)

    def QueryQuantity(self, request, context):
        count = self._inventory[request.name]
        return store_pb2.QuantityResponse(name=request.name, count=count)

    def QueryQuantities(self, request_iter, context):
        for request in request_iter:
            count = self._inventory[request.name]
            yield store_pb2.QuantityResponse(name=request.name, count=count)


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument('--access_token', help='LightStep Access Token')
    parser.add_argument(
        '--log_payloads',
        action='store_true',
        help='log request/response objects to open-tracing spans')
    parser.add_argument(
        '--include_grpc_tags',
        action='store_true',
        help='set gRPC-specific tags on spans')
    args = parser.parse_args()
    if not args.access_token:
        print('You must specify access_token')
        sys.exit(-1)

    tracer = lightstep.Tracer(
        component_name='store-server', access_token=args.access_token)
    traced_attributes = []
    if args.include_grpc_tags:
        traced_attributes = [
            ServerRequestAttribute.HEADERS, ServerRequestAttribute.METHOD_TYPE,
            ServerRequestAttribute.METHOD_NAME, ServerRequestAttribute.DEADLINE
        ]
    tracer_interceptor = open_tracing_server_interceptor(
        tracer,
        log_payloads=args.log_payloads,
        traced_attributes=traced_attributes)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server = intercept_server(server, tracer_interceptor)

    store_pb2.add_StoreServicer_to_server(Store(), server)
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
