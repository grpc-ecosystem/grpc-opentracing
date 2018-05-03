using System;
using System.Collections.Generic;
using OpenTracing;
using OpenTracing.Tag;

namespace Grpc.OpenTracing
{
    public static class Extensions
    {
        public static ISpan SetException(this ISpan span, Exception ex)
        {
            return span?.SetTag(Tags.Error, true)
                .Log(new Dictionary<string, object>(4)
                {
                    {LogFields.Event, Tags.Error.Key},
                    {LogFields.ErrorKind, ex.GetType().Name},
                    {LogFields.ErrorObject, ex},
                    {LogFields.Message, ex.Message}
                });
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
