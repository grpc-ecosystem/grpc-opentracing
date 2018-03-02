using System;
using OpenTracing;
using OpenTracing.Tag;

namespace GrpcOpenTracing
{
    public static class Extensions
    {
        public static ISpan SetException(this ISpan span, Exception ex)
        {
            return span?.SetTag(Tags.Error, true)
                .SetTag(LogFields.ErrorKind, ex.GetType().Name)
                .SetTag(LogFields.ErrorObject, ex.ToString())
                .SetTag(LogFields.Message, ex.Message);
        }
        public static ISpanBuilder WithException(this ISpanBuilder spanBuilder, Exception ex)
        {
            return spanBuilder?.WithTag(Tags.Error, true)
                .WithTag(LogFields.ErrorKind, ex.GetType().Name)
                .WithTag(LogFields.ErrorObject, ex.ToString())
                .WithTag(LogFields.Message, ex.Message);
        }

        public static ISpanBuilder WithTag(this ISpanBuilder spanBuilder, AbstractTag<bool> tagSetter, bool value)
        {
            return spanBuilder.WithTag(tagSetter.Key, value);
        }

        public static ISpanBuilder WithTag(this ISpanBuilder spanBuilder, AbstractTag<int> tagSetter, int value)
        {
            return spanBuilder.WithTag(tagSetter.Key, value);
        }

        public static ISpanBuilder WithTag(this ISpanBuilder spanBuilder, AbstractTag<double> tagSetter, double value)
        {
            return spanBuilder.WithTag(tagSetter.Key, value);
        }

        public static ISpanBuilder WithTag(this ISpanBuilder spanBuilder, AbstractTag<string> tagSetter, string value)
        {
            return spanBuilder.WithTag(tagSetter.Key, value);
        }

        public static ISpan SetTag(this ISpan span, AbstractTag<string> tagSetter, string value)
        {
            return span.SetTag(tagSetter.Key, value);
        }

        public static ISpan SetTag(this ISpan span, AbstractTag<bool> tagSetter, bool value)
        {
            return span.SetTag(tagSetter.Key, value);
        }

        public static ISpan SetTag(this ISpan span, AbstractTag<int> tagSetter, int value)
        {
            return span.SetTag(tagSetter.Key, value);
        }

        public static ISpan SetTag(this ISpan span, AbstractTag<double> tagSetter, double value)
        {
            return span.SetTag(tagSetter.Key, value);
        }
    }
}
