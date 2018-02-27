using System;
using OpenTracing;

namespace GrpcOpenTracing
{
    static class Extensions
    {
        public static ISpan SetException(this ISpan span, Exception ex)
        {
            return span?.SetTag("error", true)
                .SetTag("error.kind", ex.GetType().Name)
                .SetTag("error.object", ex.ToString())
                .SetTag("message", ex.Message);
        }
        public static ISpanBuilder WithException(this ISpanBuilder spanBuilder, Exception ex)
        {
            return spanBuilder?.WithTag("error", true)
                .WithTag("error.kind", ex.GetType().Name)
                .WithTag("error.object", ex.ToString())
                .WithTag("message", ex.Message);
        }
    }
}
