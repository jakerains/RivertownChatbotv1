import { NextRequest, NextResponse } from 'next/server';
import { initBedrock, generateResponse } from '@/lib/bedrock';

const bedrock = initBedrock();

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();
    const stream = new TransformStream();
    const writer = stream.writable.getWriter();
    
    let currentResponse = '';
    
    // Generate and stream the response
    const responseGenerator = generateResponse(bedrock, message);
    for await (const chunk of responseGenerator) {
      currentResponse += chunk;
      await writer.write(
        new TextEncoder().encode(`data: ${JSON.stringify({ content: currentResponse })}\n\n`)
      );
    }

    await writer.close();

    return new NextResponse(stream.readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
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