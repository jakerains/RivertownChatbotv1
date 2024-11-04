import { NextResponse } from 'next/server';
import { initBedrock, generateResponse } from '@/lib/bedrock';

const bedrock = initBedrock();

export async function POST(req: Request) {
  try {
    const { message, csMode } = await req.json();
    const stream = new TransformStream();
    const writer = stream.writable.getWriter();
    
    const responseGenerator = generateResponse(bedrock, message);
    for await (const chunk of responseGenerator) {
      await writer.write(
        new TextEncoder().encode(`data: ${JSON.stringify({ content: chunk })}\n\n`)
      );
    }

    await writer.close();

    return new NextResponse(stream.readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      },
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
} 