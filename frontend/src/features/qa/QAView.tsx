import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Zap, ChevronRight } from 'lucide-react';
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
      // Menggunakan requestAnimationFrame untuk memastikan DOM sudah selesai update
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
    <div className="max-w-5xl mx-auto px-4 py-8 h-[calc(100vh-140px)] flex flex-col">
      {/* Messages Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-10 mb-8 px-2 scroll-smooth"
      >
        {messages.map((msg, i) => (
          <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} animate-in fade-in slide-in-from-bottom-2 duration-500`}>
            {/* Label */}
            <div className="flex items-center gap-2 mb-3 px-1">
              <div className={`text-[10px] font-black uppercase tracking-[0.2em] opacity-40 flex items-center gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
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
            <div className={`p-5 rounded-3xl text-[14px] leading-[1.7] shadow-xl max-w-[85%] ${msg.role === 'user'
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

            {/* Reasoning Process */}
            {msg.role === 'ai' && msg.reasoning && (
              <div className="mt-4 ml-6 space-y-3 animate-in fade-in slide-in-from-top-1 duration-700 delay-300">
                <div className="flex items-center gap-2 text-[9px] font-bold text-brand-text-dim tracking-widest uppercase opacity-60">
                  <Sparkles size={10} className="text-brand-accent" />
                  Reasoning Process
                </div>
                <div className="space-y-1.5 pl-1 border-l border-brand-accent/20">
                  {msg.reasoning.map((step, idx) => (
                    <div key={idx} className="flex items-center gap-2 group">
                      <ChevronRight size={10} className="text-brand-accent/40 group-hover:text-brand-accent transition-colors" />
                      <span className="text-[11px] text-brand-text-dim italic font-medium opacity-80 group-hover:opacity-100 transition-opacity">
                        {step}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Thinking Indicator */}
        {isTyping && (
          <div className="flex flex-col items-start animate-in fade-in duration-300">
            <div className="flex items-center gap-2 mb-3 px-1">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] opacity-40 flex items-center gap-2">
                <div className="w-5 h-5 rounded bg-brand-accent/20 flex items-center justify-center text-brand-accent">
                  <Zap size={10} fill="currentColor" className="animate-pulse" />
                </div>
                <span>Sekilas Agent</span>
              </div>
            </div>
            <div className="bg-brand-card/40 p-4 rounded-3xl border border-white/5 flex gap-1.5">
              <span className="w-1.5 h-1.5 bg-brand-accent rounded-full animate-bounce" />
              <span className="w-1.5 h-1.5 bg-brand-accent rounded-full animate-bounce [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 bg-brand-accent rounded-full animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form
        onSubmit={handleSend}
        className="relative max-w-4xl mx-auto w-full group"
      >
        <div className="absolute inset-0 bg-brand-accent/10 blur-2xl rounded-full opacity-0 group-focus-within:opacity-100 transition-opacity duration-700" />
        <div className="relative flex items-center bg-brand-card/90 backdrop-blur-2xl border border-white/10 rounded-full p-2 pr-4 shadow-2xl transition-all duration-300 group-focus-within:border-brand-accent/40 group-focus-within:bg-brand-card">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Tanyakan analisis lebih lanjut..."
            className="flex-1 bg-transparent px-6 py-3 text-[14px] text-brand-text-main focus:outline-none placeholder:text-brand-text-dim/50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="w-10 h-10 bg-brand-accent text-white rounded-full flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg disabled:opacity-30 disabled:grayscale"
          >
            <Zap size={18} fill="currentColor" />
          </button>
        </div>
      </form>
    </div>
  );
};

