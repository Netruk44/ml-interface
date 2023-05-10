using System;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Host;
using Microsoft.Extensions.Logging;
using System.IO;
using System.IO.Compression;
using System.Text;
using Microsoft.Azure.Cosmos;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace openmw_openaichat_queue2cosmos
{
    public class QueueMessageItem
    {
        [JsonProperty("input_json")]
        public JObject InputJson { get; set; }

        [JsonProperty("output_json")]
        public JObject OutputJson { get; set; }

        [JsonProperty("api_output")]
        public JObject ApiOutput { get; set; }
    }

    public class QueueMessage
    {
        internal const string API_VERSION = "v1";

        public static string DecompressMessage(byte[] message)
        {
            using (var memorySteamOut = new MemoryStream())
            {
                using (var memoryStreamIn = new MemoryStream(message))
                using (var gzipStream = new GZipStream(memoryStreamIn, CompressionMode.Decompress))
                {
                    gzipStream.CopyTo(memorySteamOut);
                }
                return Encoding.UTF8.GetString(memorySteamOut.ToArray());
            }
        }

        [FunctionName("QueueMessage")]
        public async Task Run(
            [QueueTrigger("openmw-messages", Connection = "StorageConnectionAppSetting")]byte[] message, 
            ILogger log
        )
        {
            // log.LogInformation($"C# Queue trigger function processed: {message}");
            string decompressedMessage = DecompressMessage(message);
            log.LogInformation($"C# Queue trigger function processed: {decompressedMessage}");

            QueueMessageItem queueMessageItem = JsonConvert.DeserializeObject<QueueMessageItem>(decompressedMessage);

            using CosmosClient client = new(
                accountEndpoint: Environment.GetEnvironmentVariable("COSMOS_ENDPOINT")!,
                authKeyOrResourceToken: Environment.GetEnvironmentVariable("COSMOS_KEY")!
            );

            var database = client.GetDatabase("openmw_conv");
            var api_output_container = database.GetContainer("api_output");
            var json_input_container = database.GetContainer("js_input");
            var json_output_container = database.GetContainer("js_output");

            var message_id = Guid.NewGuid().ToString();

            var api_output_document = queueMessageItem.ApiOutput.DeepClone();
            api_output_document["document_id"] = Guid.NewGuid().ToString();
            api_output_document["message_id"] = message_id;
            api_output_document["original_id"] = api_output_document["id"];
            api_output_document["id"] = message_id;
            api_output_document["api_version"] = API_VERSION;

            var json_input_document = queueMessageItem.InputJson.DeepClone();
            json_input_document["document_id"] = Guid.NewGuid().ToString();
            json_input_document["message_id"] = message_id;
            json_input_document["id"] = message_id;
            json_input_document["api_version"] = API_VERSION;

            var json_output_document = queueMessageItem.OutputJson.DeepClone();
            json_output_document["document_id"] = Guid.NewGuid().ToString();
            json_output_document["message_id"] = message_id;
            json_output_document["id"] = message_id;
            json_output_document["api_version"] = API_VERSION;
            
            await api_output_container.CreateItemAsync(api_output_document);
            await json_input_container.CreateItemAsync(json_input_document);
            await json_output_container.CreateItemAsync(json_output_document);
        }
    }
}
