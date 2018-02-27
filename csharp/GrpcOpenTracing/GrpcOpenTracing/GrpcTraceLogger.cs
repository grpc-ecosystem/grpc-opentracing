using System;
using OpenTracing;

namespace GrpcOpenTracing
{
    internal class GrpcTraceLogger<TRequest, TResponse> 
        where TRequest : class 
        where TResponse : class
    {
        private readonly ISpan span;

        public GrpcTraceLogger(ISpan span)
        {
            this.span = span;
        }

        public void Request(TRequest req)
        {
            this.span.Log("gRPC request: " + req);
        }

        public void Response(TResponse rsp)
        {
            this.span.Log("gRPC response: " + rsp);
        }

        public void FinishSuccess()
        {
            this.span.Log("Call completed")
                .Finish();
        }

        public void FinishException(Exception ex)
        {
            this.span.Log("Call cancelled")
                .SetException(ex)
                .Finish();
        }
    }
}