using System;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;

namespace Grpc.OpenTracing.Streaming
{
    internal class TracingAsyncStreamReader<T> : IAsyncStreamReader<T>
    {
        private readonly IAsyncStreamReader<T> _reader;
        private readonly Action<T> _onMessage;
        private readonly Action _onStreamEnd;
        private readonly Action<Exception> _onException;

        public TracingAsyncStreamReader(IAsyncStreamReader<T> reader, Action<T> onMessage, Action onStreamEnd = null, Action<Exception> onException = null)
        {
            _reader = reader;
            _onMessage = onMessage;
            _onStreamEnd = onStreamEnd;
            _onException = onException;
        }

        public void Dispose() => _reader.Dispose();
        public T Current => _reader.Current;

        public async Task<bool> MoveNext(CancellationToken cancellationToken)
        {
            try
            {
                var hasNext = await _reader.MoveNext(cancellationToken).ConfigureAwait(false);
                if (hasNext)
                {
                    _onMessage?.Invoke(Current);
                }
                else
                {
                    _onStreamEnd?.Invoke();
                }

                return hasNext;
            }
            catch (Exception ex)
            {
                _onException?.Invoke(ex);
                throw;
            }
        }
    }
}