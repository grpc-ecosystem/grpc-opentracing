# A OpenTraced client for a Python service that implements the store interface.
from __future__ import print_function

import sys
import argparse
from builtins import input

import grpc
import lightstep

from grpc_opentracing import open_tracing_client_interceptor, ClientRequestAttribute
from grpc_opentracing.grpcext import intercept_channel

import store_pb2


class CommandExecuter(object):

  def __init__(self, stub):
    self._stub = stub

  def _execute_rpc(self, method, via, request_or_iterator):
    if via == 'future':
      result = getattr(self._stub, method).future(request_or_iterator)
      return result.result()
    elif via == 'with_call':
      return getattr(self._stub, method).with_call(request_or_iterator)[0]
    else:
      return getattr(self._stub, method)(request_or_iterator)

  def do_stock_item(self, via, arguments):
    if len(arguments) != 1:
      print('must input a single item')
      return
    request = store_pb2.AddItemRequest(name=arguments[0])
    self._execute_rpc('AddItem', via, request)

  def do_stock_items(self, via, arguments):
    if not arguments:
      print('must input at least one item')
      return
    requests = [store_pb2.AddItemRequest(name=name) for name in arguments]
    self._execute_rpc('AddItems', via, iter(requests))

  def do_sell_item(self, via, arguments):
    if len(arguments) != 1:
      print('must input a single item')
      return
    request = store_pb2.RemoveItemRequest(name=arguments[0])
    response = self._execute_rpc('RemoveItem', via, request)
    if not response.was_successful:
      print('unable to sell')

  def do_sell_items(self, via, arguments):
    if not arguments:
      print('must input at least one item')
      return
    requests = [store_pb2.RemoveItemRequest(name=name) for name in arguments]
    response = self._execute_rpc('RemoveItems', via, iter(requests))
    if not response.was_successful:
      print('unable to sell')

  def do_inventory(self, via, arguments):
    if arguments:
      print('inventory does not take any arguments')
      return
    if via != 'functor':
      print('inventory can only be called via functor')
      return
    request = store_pb2.Empty()
    result = self._execute_rpc('ListInventory', via, request)
    for query in result:
      print(query.name, '\t', query.count)

  def do_query_item(self, via, arguments):
    if len(arguments) != 1:
      print('must input a single item')
      return
    request = store_pb2.QueryItemRequest(name=arguments[0])
    query = self._execute_rpc('QueryQuantity', via, request)
    print(query.name, '\t', query.count)

  def do_query_items(self, via, arguments):
    if not arguments:
      print('must input at least one item')
      return
    if via != 'functor':
      print('query_items can only be called via functor')
      return
    requests = [store_pb2.QueryItemRequest(name=name) for name in arguments]
    result = self._execute_rpc('QueryQuantities', via, iter(requests))
    for query in result:
      print(query.name, '\t', query.count)


def execute_command(command_executer, command, arguments):
  via = 'functor'
  if len(arguments) > 1 and arguments[0] == '--via':
    via = arguments[1]
    if via not in ('functor', 'with_call', 'future'):
      print('invalid --via option')
      return
    arguments = arguments[2:]

  try:
    getattr(command_executer, 'do_' + command)(via, arguments)
  except AttributeError:
    print('unknown command: \"%s\"' % command)


INSTRUCTIONS = \
"""Enter commands to interact with the store service:

    stock_item     Stock a single item.
    stock_items    Stock one or more items.
    sell_item      Sell a single item.
    sell_items     Sell one or more items.
    inventory      List the store's inventory.
    query_item     Query the inventory for a single item.
    query_items    Query the inventory for one or more items.

You can also optionally provide a --via argument to instruct the RPC to be
initiated via either the functor, with_call, or future method.

Example:
    > stock_item apple
    > stock_items --via future apple milk
    > inventory
    apple   2
    milk    1
"""


def read_and_execute(command_executer):
  print(INSTRUCTIONS)
  while True:
    try:
      line = input('> ')
      components = line.split()
      if not components:
        continue
      command = components[0]
      arguments = components[1:]
      execute_command(command_executer, command, arguments)
    except EOFError:
      break


def run():
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
      component_name='store-client', access_token=args.access_token)
  traced_attributes = []
  if args.include_grpc_tags:
    traced_attributes = [
        ClientRequestAttribute.HEADERS, ClientRequestAttribute.METHOD_TYPE,
        ClientRequestAttribute.METHOD_NAME
    ]
  tracer_interceptor = open_tracing_client_interceptor(
      tracer,
      log_payloads=args.log_payloads,
      traced_attributes=traced_attributes)
  channel = grpc.insecure_channel('localhost:50051')
  channel = intercept_channel(channel, tracer_interceptor)
  stub = store_pb2.StoreStub(channel)

  read_and_execute(CommandExecuter(stub))

  tracer.flush()


if __name__ == '__main__':
  run()
