using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Grpc.Core;
using OpenTracing.Propagation;

namespace GrpcOpenTracing.Propagation
{
    internal class MetadataCarrier : ITextMap
    {
        private readonly Metadata metadata;
        private readonly Dictionary<string, string> dictionary;

        public MetadataCarrier(Metadata metadata)
        {
            this.metadata = metadata;
            this.dictionary = metadata.Where(e => !e.IsBinary).ToDictionary(e => e.Key, e => e.Value);
        }

        public string Get(string key)
        {
            return this.dictionary[key];
        }

        public void Set(string key, string value)
        {
            if (this.dictionary.ContainsKey(key))
            {
                var oldEntry = this.metadata.First(e => e.Key.Equals(key));
                this.metadata.Remove(oldEntry);
            }

            this.dictionary[key] = value;
            this.metadata.Add(key, value);
        }

        public IEnumerator<KeyValuePair<string, string>> GetEnumerator()
        {
            return this.dictionary.GetEnumerator();
        }

        IEnumerator IEnumerable.GetEnumerator()
        {
            return GetEnumerator();
        }
    }
}