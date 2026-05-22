import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Zap, ChevronRight, Info, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { apiService } from '../../services/api';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'ai';
  content: string;
  reasoning?: string[];
}

export const QAView: React.FC<{ 
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  onActionSuccess?: () => void 
}> = ({ messages, setMessages, onActionSuccess }) => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (scrollRef.current) {
      requestAnimationFrame(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTo({
            top: scrollRef.current.scrollHeight,
            behavior: 'smooth'
          });
        }
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setIsTyping(true);

    try {
      const data = await apiService.askQA(userMsg);

      // Simulating reasoning steps based on the actual data returned
      const reasoningSteps = [
        `Analyzing query: "${userMsg}"`,
        `Accessing Qdrant Vector DB for semantic retrieval`,
        `Retrieved ${data.retrieved?.length || 0} valid context documents`,
        `Applying cross-reference check on ${data.sources?.length || 0} sources`,
        `Synthesizing intelligence response using Gemini`
      ];

      setMessages(prev => [...prev, {
        role: 'ai',
        content: data.answer,
        reasoning: reasoningSteps
      }]);
      if (onActionSuccess) onActionSuccess();
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: 'Maaf, terjadi kesalahan saat menghubungi AI Agent.'
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-5xl mx-auto px-4 py-8 h-[calc(100vh-140px)] flex flex-col font-sans"
    >
      {/* Messages Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-8 mb-8 px-2 scroll-smooth custom-scrollbar"
      >
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div 
              key={i} 
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex flex-col gap-3 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              {/* Label */}
              <div className="flex items-center gap-2 select-none">
                <div className={`text-[9px] font-black uppercase tracking-[0.2em] opacity-40 flex items-center gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  {msg.role === 'ai' ? (
                    <>
                      <div className="w-6 h-6 rounded bg-brand-blue/20 flex items-center justify-center text-brand-blue">
                        <Zap size={10} fill="currentColor" />
                      </div>
                      <span>Sekilas Agent</span>
                    </>
                  ) : (
                    <>
                      <div className="w-6 h-6 rounded bg-white/10 flex items-center justify-center text-white/50">
                        <User size={10} />
                      </div>
                      <span>Anda</span>
                    </>
                  )}
                </div>
              </div>

              {/* Bubble */}
              <div className={`max-w-[80%] p-5 rounded-2xl text-[14px] leading-relaxed shadow-xl ${
                msg.role === 'user' 
                  ? 'bg-brand-blue/20 text-white rounded-tr-none' 
                  : 'bg-surface-muted text-white/90 rounded-tl-none border border-white/5'
              }`}>
                {msg.role === 'ai' ? (
                  <div className="markdown-content prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown 
                      components={{
                        a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-brand-blue hover:underline font-bold" />,
                        h3: ({node, ...props}) => <h3 {...props} className="text-brand-blue text-base font-bold mt-4 mb-2 border-b border-white/10 pb-1" />,
                        ul: ({node, ...props}) => <ul {...props} className="list-disc ml-4 space-y-1 my-3" />,
                        li: ({node, ...props}) => <li {...props} className="text-brand-text-main/90" />,
                        p: ({node, ...props}) => <p {...props} className="mb-3 last:mb-0" />,
                        strong: ({node, ...props}) => <strong {...props} className="text-brand-blue font-bold" />
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  msg.content
                )}
              </div>

              {/* Reasoning steps if available */}
              {msg.reasoning && msg.role === 'ai' && (
                <div className="flex flex-col gap-2 ml-8 border-l border-white/10 pl-4 py-2 select-none">
                  <div className="flex items-center gap-2 text-[10px] text-white/30 uppercase tracking-widest font-bold">
                    <Activity className="w-3.5 h-3.5 text-brand-blue" />
                    Reasoning Process
                  </div>
                  {msg.reasoning.map((thought, idx) => (
                    <div key={idx} className="flex gap-2 text-[11px] text-white/40 italic">
                      <span className="text-brand-blue opacity-50 font-bold">›</span>
                      {thought}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Thinking Indicator */}
        {isTyping && (
          <div className="flex flex-col gap-4 py-4 select-none">
            {/* Header Reasoning */}
            <div className="flex items-center gap-3 text-brand-blue/60 px-4">
              <Sparkles className="w-4 h-4 animate-pulse" />
              <span className="text-[10px] font-bold tracking-[0.2em] uppercase italic">
                Reasoning Process
              </span>
            </div>
            
            {/* List of Steps */}
            <div className="ml-8 pl-6 border-l border-brand-blue/20 space-y-3 py-1 font-mono">
              {[
                `Analyzing intelligence query: "${messages[messages.length - 1]?.content.substring(0, 35)}..."`,
                "Engaging Qdrant Multilingual Vector Store for hybrid retrieval",
                "Optimizing retrieval depth (fetch_limit: 40) for edge cases",
                "Reranking candidate chunks using Llama 3.1 8B for factual precision",
                "Synthesizing high-fidelity response using Qwen 2.5 32B"
              ].map((step, idx) => (
                <motion.div 
                  key={idx} 
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.8 }}
                  className="flex items-center gap-3 text-[11px] text-white/40 italic"
                >
                  <ChevronRight className="w-3 h-3 text-brand-blue/40" />
                  {step}
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form
        onSubmit={handleSend}
        className="relative max-w-4xl mx-auto w-full group"
      >
        <div className="absolute inset-0 bg-brand-blue/5 blur-2xl rounded-full opacity-0 group-focus-within:opacity-100 transition-opacity duration-700 pointer-events-none" />
        <div className="relative flex items-center bg-brand-card/90 backdrop-blur-2xl border border-white/10 rounded-2xl p-2 pr-4 shadow-2xl transition-all duration-300 group-focus-within:border-brand-blue/40 group-focus-within:bg-brand-card">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
            placeholder="Tanyakan analisis lebih lanjut..."
            className="flex-1 bg-transparent px-6 py-3 text-sm text-white focus:outline-none placeholder:text-white/20 font-sans"
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="w-10 h-10 bg-brand-blue text-white rounded-xl flex items-center justify-center hover:scale-105 active:scale-95 disabled:opacity-30 disabled:hover:scale-100 transition-all shadow-lg cursor-pointer"
          >
            <Zap size={16} className="text-white fill-current" />
          </button>
        </div>
      </form>
    </motion.div>
  );
};
