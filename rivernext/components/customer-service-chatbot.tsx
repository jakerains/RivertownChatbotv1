"use client"

import React, { useState, useEffect, useRef, useMemo } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { CircleDot, Send, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
}

const streamReader = async (response: Response, callback: (chunk: string) => void) => {
  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          callback(data.content);
        } catch (e) {
          console.error('Error parsing SSE data:', e);
        }
      }
    }
  }
};

const TypewriterText = ({ text }: { text: string }) => {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    let i = 0;
    const intervalId = setInterval(() => {
      setDisplayedText(text.slice(0, i));
      i++;
      if (i > text.length) clearInterval(intervalId);
    }, 20);

    return () => clearInterval(intervalId);
  }, [text]);

  return (
    <span className="whitespace-pre-wrap">
      {displayedText.split('').map((char, index) => (
        <motion.span
          key={index}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.1 }}
        >
          {char}
        </motion.span>
      ))}
    </span>
  );
};

const FloatingBall = React.memo(({ delay }: { delay: number }) => (
  <div 
    className="absolute rounded-full opacity-20 blur-md pointer-events-none"
    style={{
      width: `${Math.random() * 100 + 50}px`,
      height: `${Math.random() * 100 + 50}px`,
      backgroundColor: `rgb(${Math.floor(Math.random() * 56 + 160)}, ${Math.floor(Math.random() * 56 + 82)}, ${Math.floor(Math.random() * 56 + 45)})`,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      animation: `float 20s infinite linear ${delay}s`
    }}
  />
));

const RollingBallAnimation = () => (
  <div className="flex items-center w-full">
    <motion.div
      className="w-6 h-6 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full shadow-lg"
      animate={{
        x: ["0%", "100%", "0%"],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: "linear",
      }}
    />
    <span className="ml-2 font-medium whitespace-nowrap">Rolling up a response...</span>
  </div>
);

export default function CustomerServiceChatbot() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: "Bounce into the world of Rivertown Ball Company! ", sender: 'bot' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const floatingBalls = useMemo(() => (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(10)].map((_, i) => (
        <FloatingBall key={i} delay={i * 2} />
      ))}
    </div>
  ), []);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (input.trim()) {
      setMessages(prev => [...prev, { 
        id: prev.length + 1, 
        text: input, 
        sender: 'user' 
      }]);
      setInput('');
      setIsTyping(true);

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: input,
            csMode: true
          }),
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        let currentResponse = '';
        await streamReader(response, (chunk) => {
          setMessages(prev => {
            const newMessages = [...prev];
            if (newMessages[newMessages.length - 1]?.sender === 'bot') {
              newMessages[newMessages.length - 1].text = chunk;
            } else {
              newMessages.push({
                id: prev.length + 1,
                text: chunk,
                sender: 'bot'
              });
            }
            return newMessages;
          });
        });

      } catch (error) {
        console.error('Error:', error);
        setMessages(prev => [...prev, {
          id: prev.length + 1,
          text: "I apologize, but I'm having trouble connecting right now. Please try again later.",
          sender: 'bot'
        }]);
      } finally {
        setIsTyping(false);
      }
    }
  };

  return (
    <div className="relative flex flex-col h-screen bg-gradient-to-br from-amber-50 to-amber-100 overflow-hidden font-sans">
      <style jsx global>{`
        @keyframes float {
          0% { transform: translate(0, 0) rotate(0deg); }
          33% { transform: translate(30px, 30px) rotate(120deg); }
          66% { transform: translate(-30px, 50px) rotate(240deg); }
          100% { transform: translate(0, 0) rotate(360deg); }
        }
      `}</style>
      {floatingBalls}
      <header className="relative z-10 bg-white bg-opacity-70 p-4 backdrop-blur-xl shadow-lg">
        <div className="container mx-auto flex items-center">
          <motion.div
            className="bg-gradient-to-r from-amber-400 to-amber-600 p-2 rounded-full mr-3 shadow-md"
            animate={{ rotate: 360 }}
            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
          >
            <CircleDot className="h-6 w-6 text-white" />
          </motion.div>
          <h1 className="text-2xl font-bold text-amber-800 tracking-tight">Rivertown Ball Company</h1>
        </div>
      </header>
      
      <main className="relative z-10 flex-grow container mx-auto p-4 md:p-6 flex flex-col max-w-3xl">
        <ScrollArea className="flex-grow mb-4 h-[calc(100vh-12rem)] rounded-lg bg-white bg-opacity-50 backdrop-blur-sm shadow-lg p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.sender === 'user'
                      ? 'bg-amber-500 text-white'
                      : 'bg-white bg-opacity-70 text-gray-800'
                  }`}
                >
                  <TypewriterText text={message.text} />
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white bg-opacity-70 rounded-lg p-3">
                  <span className="animate-pulse">...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        <div className="relative z-10 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about our wooden balls..."
            className="bg-white bg-opacity-70 backdrop-blur-sm"
          />
          <Button 
            onClick={handleSend}
            className="bg-amber-500 hover:bg-amber-600 text-white"
          >
            Send
          </Button>
        </div>
      </main>
    </div>
  )
}