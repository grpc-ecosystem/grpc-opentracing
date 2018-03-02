using System;
using System.Threading.Tasks;
using Grpc.Core;

namespace GrpcOpenTracing.Streaming
{
    internal class TracingClientStreamWriter<T> : IClientStreamWriter<T>
    {
        private readonly IClientStreamWriter<T> writer;
        private readonly Action<T> onWrite;
        private readonly Action onComplete;

        public TracingClientStreamWriter(IClientStreamWriter<T> writer, Action<T> onWrite, Action onComplete = null)
        {
            this.writer = writer;
            this.onWrite = onWrite;
            this.onComplete = onComplete;
        }

        public WriteOptions WriteOptions
        {
            get => this.writer.WriteOptions;
            set => this.writer.WriteOptions = value;
        }

        public Task WriteAsync(T message)
        {
            this.onWrite(message);
            return this.writer.WriteAsync(message);
        }

        public Task CompleteAsync()
        {
            this.onComplete?.Invoke();
            return this.writer.CompleteAsync();
        }
    }
}