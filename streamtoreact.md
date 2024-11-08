I'll create a detailed implementation guide for converting this Streamlit chatbot to Next.js/React. I'll break down each component and explain the architecture.

```markdown
# RiverTown Chatbot Implementation Guide

## Overview
The application is a chatbot that uses Amazon Bedrock for RAG (Retrieval Augmented Generation) with three main functionalities:
1. General product Q&A using RAG
2. Customer order lookups
3. Customer service call routing

## Core Components

### 1. AWS Service Initialization
Reference implementation in bedrock_utils.py:
```python:bedrock_utils.py
startLine: 18
endLine: 38
```

For Next.js, you'll need to create similar initialization in a server-side utility:

```typescript
// lib/aws-config.ts
import { BedrockRuntimeClient } from "@aws-sdk/client-bedrock-runtime";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";

export function initAWSClients() {
  const bedrockRuntime = new BedrockRuntimeClient({
    region: process.env.AWS_REGION,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
    }
  });
  
  const dynamodb = new DynamoDBClient({
    region: process.env.AWS_REGION,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
    }
  });
  
  return { bedrockRuntime, dynamodb };
}
```

### 2. Chat State Management
The Streamlit app uses session state:
```python:app.py
startLine: 14
endLine: 19
```

For Next.js, use React state with a custom hook:

```typescript
// hooks/useChatState.ts
import { create } from 'zustand';

interface ChatState {
  messages: Message[];
  phoneNumber: string | null;
  csMode: boolean;
  addMessage: (message: Message) => void;
  setPhoneNumber: (number: string | null) => void;
  setCsMode: (mode: boolean) => void;
  reset: () => void;
}

export const useChatState = create<ChatState>((set) => ({
  messages: [],
  phoneNumber: null,
  csMode: false,
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  setPhoneNumber: (number) => set({ phoneNumber: number }),
  setCsMode: (mode) => set({ csMode: mode }),
  reset: () => set({ messages: [], phoneNumber: null, csMode: false })
}));
```

### 3. RAG Implementation
The Streamlit app handles RAG in bedrock_utils.py:
```python:bedrock_utils.py
startLine: 71
endLine: 140
```

For Next.js, create an API route:

```typescript
// app/api/chat/route.ts
import { BedrockRuntimeClient } from "@aws-sdk/client-bedrock-runtime";
import { StreamingTextResponse } from 'ai';

export async function POST(req: Request) {
  const { message, context } = await req.json();
  const client = new BedrockRuntimeClient({/*config*/});
  
  const response = await client.invokeModelWithResponseStream({
    modelId: "anthropic.claude-instant-v1",
    body: JSON.stringify({
      prompt: formatPrompt(message, context),
      max_tokens: 2048,
      temperature: 0.7,
      stop_sequences: ["\n\nHuman:", "\n\nAssistant:"]
    })
  });

  // Convert to ReadableStream
  return new StreamingTextResponse(response);
}
```

### 4. Customer Service Mode
The CS mode detection in Streamlit:
```python:app.py
startLine: 41
endLine: 50
```

For Next.js, create a utility:

```typescript
// utils/cs-detection.ts
const CS_KEYWORDS = [
  'speak to someone',
  'talk to a person',
  'customer service',
  'representative',
  'speak to a human',
  'talk to someone',
  'call me',
  'contact me'
];

export function isCustomerServiceRequest(message: string): boolean {
  return CS_KEYWORDS.some(keyword => 
    message.toLowerCase().includes(keyword)
  );
}
```

### 5. Order Lookup
The order lookup functionality:
```python:bedrock_utils.py
startLine: 40
endLine: 52
```

Create a DynamoDB utility for Next.js:

```typescript
// lib/dynamo-utils.ts
import { DynamoDBClient, QueryCommand } from "@aws-sdk/client-dynamodb";

export async function lookupCustomerOrders(
  dynamodb: DynamoDBClient,
  firstName: string,
  lastName: string
) {
  const command = new QueryCommand({
    TableName: process.env.DYNAMODB_TABLE,
    KeyConditionExpression: 
      "firstName = :firstName AND lastName = :lastName",
    ExpressionAttributeValues: {
      ":firstName": { S: firstName },
      ":lastName": { S: lastName }
    }
  });
  
  return await dynamodb.send(command);
}
```

### 6. Phone Call Integration
The Bland API integration:
```python:bedrock_utils.py
startLine: 210
endLine: 243
```

Create a service for Next.js:

```typescript
// services/bland-service.ts
export async function initializeCustomerCall(
  phoneNumber: string,
  task: string
) {
  const response = await fetch(`${process.env.BLAND_API_URL}/calls`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.BLAND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      phone_number: phoneNumber,
      task,
      model: "turbo",
      voice: "Alexa",
      max_duration: 12,
      wait_for_greeting: true,
      temperature: 0.8
    })
  });
  
  return response.json();
}
```

## Implementation Steps

1. Set up Next.js project with TypeScript
2. Configure AWS credentials in .env.local
3. Create chat interface components
4. Implement chat state management
5. Create API routes for:
   - RAG responses
   - Order lookups
   - Customer service calls
6. Set up streaming responses
7. Implement error handling
8. Add loading states and UI feedback

## Key Differences from Streamlit

1. **State Management**: Replace Streamlit's session_state with React state management
2. **Streaming**: Use Server-Sent Events or WebSocket for streaming responses
3. **UI Components**: Build custom React components instead of using Streamlit's built-in components
4. **API Routes**: Create separate API routes instead of running everything in one script
5. **Client/Server Split**: Clearly separate client-side and server-side code
6. **Error Handling**: Implement more robust error handling for network requests

This should give developers a clear roadmap for implementing the same functionality in a Next.js application while maintaining the core features of the original Streamlit app.
```