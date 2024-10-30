import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { StreamingTextResponse } from 'ai';

const encoder = new TextEncoder();

export async function init_bedrock() {
  const client = new BedrockRuntimeClient({
    region: process.env.AWS_REGION,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
    }
  });
  
  return [client, client];
}

// Helper function to convert iterator to stream
function iteratorToStream(iterator: AsyncIterator<any>) {
  return new ReadableStream({
    async pull(controller) {
      try {
        const { value, done } = await iterator.next();
        if (done) {
          controller.close();
        } else {
          // Encode the chunk as a Uint8Array
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content: value })}\n\n`));
        }
      } catch (error) {
        controller.error(error);
      }
    },
  });
}

export async function get_response_with_rag(
  bedrock_client: BedrockRuntimeClient,
  runtime_client: BedrockRuntimeClient,
  prompt: string,
  phone_number: string | null = null,
  dynamodb: DynamoDBClient | null = null
) {
  try {
    const command = new InvokeModelCommand({
      modelId: "anthropic.claude-v2",
      contentType: "application/json",
      accept: "application/json",
      body: JSON.stringify({
        prompt: `\n\nHuman: ${prompt}\n\nAssistant:`,
        max_tokens_to_sample: 1000,
        temperature: 0.7,
        top_p: 0.9,
      })
    });

    const response = await runtime_client.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(response.body));
    
    // Create stream from response
    const stream = iteratorToStream((async function* () {
      const chunks = responseBody.completion.split(" ");
      for (const chunk of chunks) {
        yield chunk + " ";
        // Add a small delay to simulate streaming
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    })());

    // Return StreamingTextResponse
    return new StreamingTextResponse(stream);

  } catch (error) {
    console.error("Error in get_response_with_rag:", error);
    throw error;
  }
}
