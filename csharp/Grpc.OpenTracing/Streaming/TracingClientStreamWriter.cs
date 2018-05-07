using System;
using System.Threading.Tasks;
using Grpc.Core;

namespace Grpc.OpenTracing.Streaming
{
    internal class TracingClientStreamWriter<T> : IClientStreamWriter<T>
    {
        private readonly IClientStreamWriter<T> _writer;
        private readonly Action<T> _onWrite;
        private readonly Action _onComplete;

        public TracingClientStreamWriter(IClientStreamWriter<T> writer, Action<T> onWrite, Action onComplete = null)
        {
            _writer = writer;
            _onWrite = onWrite;
            _onComplete = onComplete;
        }

        public WriteOptions WriteOptions
        {
            get => _writer.WriteOptions;
            set => _writer.WriteOptions = value;
        }

        public Task WriteAsync(T message)
        {
            _onWrite(message);
            return _writer.WriteAsync(message);
        }

        public Task CompleteAsync()
        {
            _onComplete?.Invoke();
            return _writer.CompleteAsync();
        }
    }
}