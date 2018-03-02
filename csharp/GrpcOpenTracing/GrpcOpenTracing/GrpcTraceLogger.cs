using System;
using System.Collections.Generic;
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
            this.span.Log(new Dictionary<string, object>
            {
                { LogFields.Event, "gRPC request" },
                { "data", req }
            });
        }

        public void Response(TResponse rsp)
        {
            this.span.Log(new Dictionary<string, object>
            {
                { LogFields.Event, "gRPC response" },
                { "data", rsp }
            });
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