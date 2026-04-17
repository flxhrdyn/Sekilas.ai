import React, { useState } from 'react';
import { Send, Bot, User } from 'lucide-react';
import { apiService } from '../../services/api';

export const QAView: React.FC<{ onActionSuccess?: () => void }> = ({ onActionSuccess }) => {
  const [messages, setMessages] = useState<{ role: 'user' | 'ai', content: string }[]>([
    { role: 'ai', content: 'Halo! Saya asisten cerdas Sekilas.ai. Tanyakan apa saja tentang berita hari ini.' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setIsTyping(true);

    try {
      const data = await apiService.askQA(userMsg);
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: data.answer 
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
    <div className="flex flex-col h-[calc(100vh-10rem)] border border-brand-border rounded-xl overflow-hidden bg-white/5">
      <div className="p-3 border-b border-brand-border flex items-center gap-3 bg-brand-sidebar/50">
        <div className="w-8 h-8 rounded-lg bg-brand-accent/20 flex items-center justify-center text-brand-accent">
          <Bot size={18} />
        </div>
        <div>
          <h2 className="text-sm font-bold">Tanya AI Agent (RAG)</h2>
          <div className="flex items-center gap-1.5 text-[9px] mono-text text-brand-green">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-green animate-pulse" />
            Live Qdrant Connection
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] ${
                msg.role === 'user' ? 'bg-brand-accent text-brand-bg' : 'bg-brand-card text-brand-accent border border-brand-border'
              }`}>
                {msg.role === 'user' ? <User size={12} /> : <Bot size={12} />}
              </div>
              <div className={`p-3 rounded-xl text-[13px] leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user' 
                  ? 'bg-brand-accent text-brand-bg font-medium' 
                  : 'bg-brand-card text-brand-text-main border border-brand-border'
              }`}>
                {msg.content}
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="flex gap-2">
              <div className="w-6 h-6 rounded-full bg-brand-card text-brand-accent border border-brand-border flex items-center justify-center">
                <Bot size={12} />
              </div>
              <div className="bg-brand-card p-3 rounded-xl border border-brand-border flex gap-1">
                <span className="w-1 h-1 bg-brand-accent/40 rounded-full animate-bounce" />
                <span className="w-1 h-1 bg-brand-accent/40 rounded-full animate-bounce [animation-delay:0.2s]" />
                <span className="w-1 h-1 bg-brand-accent/40 rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="p-3 bg-brand-sidebar/30 border-t border-brand-border flex gap-2">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Tanyakan sesuatu tentang berita..."
          className="flex-1 bg-black/20 border border-brand-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-accent transition-all"
        />
        <button 
          type="submit"
          disabled={!input.trim() || isTyping}
          className="bg-brand-accent text-brand-bg p-2 rounded-lg hover:bg-brand-accent/90 transition-colors disabled:opacity-50"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};
