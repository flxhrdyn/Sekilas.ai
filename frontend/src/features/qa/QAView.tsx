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
        `Synthesizing intelligence response using Llama 8B`
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
                      <div className="w-5 h-5 rounded bg-brand-accent/20 flex items-center justify-center text-brand-accent">
                        <Zap size={10} fill="currentColor" />
                      </div>
                      <span>Sekilas Agent</span>
                    </>
                  ) : (
                    <>
                      <div className="w-5 h-5 rounded bg-white/10 flex items-center justify-center text-white/50">
                        <User size={10} />
                      </div>
                      <span>Anda</span>
                    </>
                  )}
                </div>
              </div>

              {/* Bubble */}
              <div className={`p-5 rounded-3xl text-[14px] leading-[1.7] shadow-xl max-w-[85%] ${
                msg.role === 'user'
                  ? 'bg-brand-accent text-white font-medium rounded-tr-none'
                  : 'bg-brand-card/80 border border-white/5 text-brand-text-main rounded-tl-none backdrop-blur-sm'
              }`}>
                {msg.role === 'ai' ? (
                  <div className="markdown-content prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown 
                      components={{
                        a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-brand-accent hover:underline font-bold" />,
                        h3: ({node, ...props}) => <h3 {...props} className="text-brand-accent text-base font-bold mt-4 mb-2 border-b border-white/10 pb-1" />,
                        ul: ({node, ...props}) => <ul {...props} className="list-disc ml-4 space-y-1 my-3" />,
                        li: ({node, ...props}) => <li {...props} className="text-brand-text-main/90" />,
                        p: ({node, ...props}) => <p {...props} className="mb-3 last:mb-0" />,
                        strong: ({node, ...props}) => <strong {...props} className="text-brand-accent font-bold" />
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
                <div className="flex flex-col gap-2 ml-8 border-l border-brand-accent/20 pl-4 py-2 select-none">
                  <div className="flex items-center gap-2 text-[10px] text-brand-text-dim/60 uppercase tracking-widest font-bold">
                    <Activity className="w-3.5 h-3.5 text-brand-accent" />
                    Reasoning Process
                  </div>
                  {msg.reasoning.map((thought, idx) => (
                    <div key={idx} className="flex gap-2 text-[11px] text-brand-text-dim/80 italic">
                      <span className="text-brand-accent opacity-50 font-bold">›</span>
                      {thought}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Thinking Indicator with Dynamic Reasoning */}
        {isTyping && (
          <div className="flex flex-col gap-5 py-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header Reasoning */}
            <div className="flex items-center gap-3 text-brand-accent/60 px-4">
              <Sparkles className="w-4 h-4 animate-pulse" />
              <span className="text-[10px] font-bold tracking-[0.2em] uppercase italic">
                Reasoning Process
              </span>
            </div>
            
            {/* List of Steps */}
            <div className="ml-8 pl-6 border-l border-brand-accent/20 space-y-4 py-1">
              {[
                `Analyzing intelligence query: "${messages[messages.length - 1]?.content.substring(0, 35)}..."`,
                "Engaging Qdrant Multilingual Vector Store for hybrid retrieval",
                "Optimizing retrieval depth (fetch_limit: 40) for edge cases",
                "Reranking candidate chunks using Llama 3.1 8B for factual precision",
                "Synthesizing high-fidelity response using Qwen 2.5 32B"
              ].map((step, idx) => (
                <div 
                  key={idx} 
                  className="flex items-center gap-3 text-xs text-brand-text-dim/80 italic animate-in fade-in slide-in-from-left-4 duration-700 fill-mode-both"
                  style={{ animationDelay: `${idx * 1000}ms` }}
                >
                  <ChevronRight className="w-3 h-3 text-brand-accent/40" />
                  {step}
                </div>
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
        <div className="absolute inset-0 bg-brand-accent/10 blur-2xl rounded-full opacity-0 group-focus-within:opacity-100 transition-opacity duration-700 pointer-events-none" />
        <div className="relative flex items-center bg-brand-card/90 backdrop-blur-2xl border border-white/10 rounded-full p-2 pr-4 shadow-2xl transition-all duration-300 group-focus-within:border-brand-accent/40 group-focus-within:bg-brand-card">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
            placeholder="Tanyakan analisis lebih lanjut..."
            className="flex-1 bg-transparent px-6 py-3 text-[14px] text-brand-text-main focus:outline-none placeholder:text-brand-text-dim/50 font-sans"
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="w-10 h-10 bg-brand-accent text-white rounded-full flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg disabled:opacity-30 disabled:grayscale cursor-pointer"
          >
            <Zap size={18} fill="currentColor" />
          </button>
        </div>
      </form>
    </motion.div>
  );
};
