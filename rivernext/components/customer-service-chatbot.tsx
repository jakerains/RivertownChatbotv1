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
    { id: 1, text: "Bounce into the world of Rivertown Ball Company! 🏀🎾⚾ Ready to have a ball? How can I roll out some assistance for you today?\n\nHere are a few things you could ask about:\n\n• Our range of custom wooden balls\n• Unique design options for wooden spheres\n• Creative uses for decorative balls\n• Our ball-making process", sender: 'bot' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

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

  const handleSend = () => {
    if (input.trim()) {
      setMessages([...messages, { id: messages.length + 1, text: input, sender: 'user' }]);
      setInput('');
      setIsTyping(true);
      // Simulate bot response
      setTimeout(() => {
        setIsTyping(false);
        setMessages(prev => [...prev, { 
          id: prev.length + 1, 
          text: "Thank you for your message. Our team will get back to you shortly with a detailed response.", 
          sender: 'bot' 
        }]);
      }, 2000);
    }
  }

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
        <ScrollArea className="flex-grow mb-4 bg-white bg-opacity-70 rounded-2xl shadow-xl p-6 border border-amber-200 backdrop-blur-xl">
          <div ref={scrollAreaRef} className="space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${
                    message.sender === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <motion.div
                    className={`max-w-[80%] p-4 rounded-2xl shadow-md ${
                      message.sender === 'user'
                        ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-white'
                        : 'bg-white text-amber-800'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                  >
                    <TypewriterText text={message.text} />
                  </motion.div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-amber-800 flex items-center mt-4"
            >
              <RollingBallAnimation />
            </motion.div>
          )}
        </ScrollArea>
        
        <div className="flex space-x-2 bg-white bg-opacity-70 p-3 rounded-2xl backdrop-blur-xl shadow-lg">
          <Input
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            className="flex-grow bg-transparent border-amber-300 focus:ring-amber-500 focus:border-amber-500 text-amber-800 placeholder-amber-400 rounded-xl"
          />
          <Button 
            onClick={handleSend} 
            className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white transition-all duration-300 rounded-xl px-6"
          >
            <Send className="h-5 w-5 mr-2" />
            <span className="hidden sm:inline">Send</span>
          </Button>
        </div>
      </main>
    </div>
  )
}