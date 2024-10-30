'use client';

import { useState } from 'react';

interface ChatResponse {
  content: string;
}

export function useChat() {
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (message: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: message }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const reader = response.body?.getReader();
      let result = '';

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6)) as ChatResponse;
            result += data.content;
          }
        }
      }

      return result;
    } finally {
      setIsLoading(false);
    }
  };

  return { sendMessage, isLoading };
}
