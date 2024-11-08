// AWS Bedrock Types
export interface BedrockConfig {
  region: string;
  credentials: {
    accessKeyId: string;
    secretAccessKey: string;
  };
}

export interface BedrockResponse {
  completion: string;
  modelId: string;
  timestamp: number;
}

export interface BedrockPrompt {
  prompt: string;
  maxTokens?: number;
  temperature?: number;
  modelId?: string;
}

// DynamoDB Types
export interface DynamoDBConfig {
  region: string;
  tableName: string;
  credentials: {
    accessKeyId: string;
    secretAccessKey: string;
  };
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: number;
  metadata?: Record<string, any>;
}

export interface ChatSession {
  sessionId: string;
  userId?: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
} 