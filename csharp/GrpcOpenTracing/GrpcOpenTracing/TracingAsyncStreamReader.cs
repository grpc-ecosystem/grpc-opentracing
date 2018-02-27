using System;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;

namespace GrpcOpenTracing
{
    internal class TracingAsyncStreamReader<T> : IAsyncStreamReader<T>
    {
        private readonly IAsyncStreamReader<T> reader;
        private readonly Action<T> onMessage;
        private readonly Action onStreamEnd;
        private readonly Action<Exception> onException;

        public TracingAsyncStreamReader(IAsyncStreamReader<T> reader, Action<T> onMessage, Action onStreamEnd = null, Action<Exception> onException = null)
        {
            this.reader = reader;
            this.onMessage = onMessage;
            this.onStreamEnd = onStreamEnd;
            this.onException = onException;
        }

        public void Dispose() => this.reader.Dispose();
        public T Current => this.reader.Current;

        public async Task<bool> MoveNext(CancellationToken cancellationToken)
        {
            try
            {
                var hasNext = await this.reader.MoveNext(cancellationToken).ConfigureAwait(false);
                if (hasNext)
                {
                    this.onMessage?.Invoke(this.Current);
                }
                else
                {
                    this.onStreamEnd?.Invoke();
                }

                return hasNext;
            }
            catch (Exception ex)
            {
                this.onException?.Invoke(ex);
                throw;
            }
        }
    }
}