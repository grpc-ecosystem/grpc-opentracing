using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Grpc.Core;
using OpenTracing.Propagation;

namespace Grpc.OpenTracing.Propagation
{
    internal class MetadataCarrier : ITextMap
    {
        private readonly Metadata _metadata;

        public MetadataCarrier(Metadata metadata)
        {
            _metadata = metadata;
        }

        public void Set(string key, string value)
        {
            _metadata.Add(key, value);
        }

        public IEnumerator<KeyValuePair<string, string>> GetEnumerator()
        {
            foreach (var entry in _metadata)
            {
                if (entry.IsBinary)
                    continue;

                yield return new KeyValuePair<string, string>(entry.Key, entry.Value);
            }
        }

        IEnumerator IEnumerable.GetEnumerator()
        {
            return GetEnumerator();
        }
    }
}