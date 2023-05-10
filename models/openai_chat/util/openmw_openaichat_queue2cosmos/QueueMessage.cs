using System;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Host;
using Microsoft.Extensions.Logging;
using System.IO;
using System.IO.Compression;
using System.Text;

namespace openmw_openaichat_queue2cosmos
{
    public class QueueMessage
    {
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
        public void Run(
            [QueueTrigger("openmw-messages", Connection = "StorageConnectionAppSetting")]byte[] message, 
            ILogger log
        )
        {
            // log.LogInformation($"C# Queue trigger function processed: {message}");
            log.LogInformation($"C# Queue trigger function processed: {DecompressMessage(message)}");
        }
    }
}
