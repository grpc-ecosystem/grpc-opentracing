using System;
using System.Collections.Generic;
using OpenTracing;

namespace Grpc.OpenTracing
{
    internal class GrpcTraceLogger<TRequest, TResponse> 
        where TRequest : class 
        where TResponse : class
    {
        private readonly ISpan _span;

        public GrpcTraceLogger(ISpan span)
        {
            _span = span;
        }

        public void Request(TRequest req)
        {
            // TODO: Only log on streaming or verbose
            _span.Log(new Dictionary<string, object>
            {
                { LogFields.Event, "gRPC request" },
                { "data", req }
            });
        }

        public void Response(TResponse rsp)
        {
            // TODO: Only log on streaming or verbose
            _span.Log(new Dictionary<string, object>
            {
                { LogFields.Event, "gRPC response" },
                { "data", rsp }
            });
        }

        public void FinishSuccess()
        {
            _span.Finish();
        }

        public void FinishException(Exception ex)
        {
            _span.SetException(ex)
                .Finish();
        }
    }
}