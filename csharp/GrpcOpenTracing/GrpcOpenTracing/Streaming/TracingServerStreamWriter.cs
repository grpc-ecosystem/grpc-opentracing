using System;
using System.Threading.Tasks;
using Grpc.Core;

namespace GrpcOpenTracing.Streaming
{
    internal class TracingServerStreamWriter<T> : IServerStreamWriter<T>
    {
        private readonly IServerStreamWriter<T> writer;
        private readonly Action<T> onWrite;

        public TracingServerStreamWriter(IServerStreamWriter<T> writer, Action<T> onWrite)
        {
            this.writer = writer;
            this.onWrite = onWrite;
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
    }
}