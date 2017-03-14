"""Internal utilities for gRPC OpenTracing."""


def get_method_type(is_client_stream, is_server_stream):
  if is_client_stream and is_server_stream:
    return 'BIDI_STREAMING'
  elif is_client_stream:
    return 'CLIENT_STREAMING'
  elif is_server_stream:
    return 'SERVER_STREAMING'
  else:
    return 'UNARY'


def get_deadline_millis(timeout):
  if timeout is None:
    return 'None'
  return str(int(round(timeout * 1000)))
