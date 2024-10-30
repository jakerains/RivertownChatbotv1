import { StreamingTextResponse } from 'ai';
import { init_bedrock, get_response_with_rag } from '@/utils/bedrock-utils';
import { init_dynamodb } from '@/utils/dynamo-utils';

export const runtime = 'edge';

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    const lastMessage = messages[messages.length - 1];
    
    // Initialize clients
    const [bedrock_client, runtime_client] = await init_bedrock();
    const dynamodb = await init_dynamodb();
    
    // Get response stream
    const stream = await get_response_with_rag(
      bedrock_client,
      runtime_client,
      lastMessage.content
    );
    
    // Return streaming response
    return stream;

  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to process chat request' }), 
      { status: 500 }
    );
  }
}
