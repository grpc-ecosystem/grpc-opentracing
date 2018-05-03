using System;
using System.Threading.Tasks;
using Grpc.Core;

namespace Grpc.OpenTracing.Streaming
{
    internal class TracingServerStreamWriter<T> : IServerStreamWriter<T>
    {
        private readonly IServerStreamWriter<T> _writer;
        private readonly Action<T> _onWrite;

        public TracingServerStreamWriter(IServerStreamWriter<T> writer, Action<T> onWrite)
        {
            _writer = writer;
            _onWrite = onWrite;
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
    }
}