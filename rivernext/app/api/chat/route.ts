import { NextRequest, NextResponse } from 'next/server';
import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";
import { Readable } from 'stream';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    console.log('Received request body:', body);
    
    const { messages } = body;
    
    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      throw new Error('Messages array is required and must not be empty');
    }

    console.log('AWS Region:', process.env.AWS_REGION);
    console.log('Using credentials:', !!process.env.AWS_ACCESS_KEY_ID, !!process.env.AWS_SECRET_ACCESS_KEY);

    const client = new BedrockRuntimeClient({
      region: process.env.AWS_REGION,
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
      }
    });

    const input = {
      modelId: "us.anthropic.claude-3-5-haiku-20241022-v1:0",
      contentType: "application/json",
      accept: "application/json",
      body: JSON.stringify({
        anthropic_version: "bedrock-2023-05-31",
        messages: messages,
        max_tokens: 1024,
        temperature: 0.7,
        top_p: 0.999,
        top_k: 250,
      })
    };

    console.log('Sending request to Bedrock:', input);
    const command = new InvokeModelCommand(input);
    const response = await client.send(command);
    console.log('Received response from Bedrock');

    // Convert Node.js Readable stream to string
    const responseBody = await streamToString(response.body as Readable);
    const parsedResponse = JSON.parse(responseBody);
    console.log('Parsed response:', parsedResponse);

    // Extract bot's text response
    const botResponse = parsedResponse.content
      .filter((item: any) => item.type === 'text')
      .map((item: any) => item.text)
      .join(' ');

    // Return the bot's response as JSON
    return NextResponse.json({ content: botResponse }, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal Server Error' },
      { status: 500 }
    );
  }
}

/**
 * Helper function to convert Node.js ReadableStream to string
 * @param stream Readable
 * @returns Promise<string>
 */
async function streamToString(stream: Readable): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    stream.on('data', (chunk) => chunks.push(Buffer.from(chunk)));
    stream.on('error', (err) => reject(err));
    stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
  });
} 