import React from 'react';
import { motion } from 'motion/react';
import { ChevronRight, Zap } from 'lucide-react';
import { NewsArticle } from '../../types';

export const NewsCard: React.FC<{ article: NewsArticle }> = ({ article }) => {
  const getCategoryColor = (cat: string) => {
    const colors: Record<string, string> = {
      'Ekonomi': 'text-emerald-400 bg-emerald-400/10',
      'Politik': 'text-red-400 bg-red-400/10',
      'Teknologi': 'text-blue-400 bg-blue-400/10',
      'Kesehatan': 'text-cyan-400 bg-cyan-400/10',
      'Olahraga': 'text-orange-400 bg-orange-400/10',
      'Hiburan': 'text-pink-400 bg-pink-400/10',
      'Internasional': 'text-purple-400 bg-purple-400/10',
      'Lingkungan': 'text-green-400 bg-green-400/10',
      'Hukum': 'text-amber-400 bg-amber-400/10',
      'Umum': 'text-brand-text-dim bg-white/5'
    };
    return colors[cat] || colors['Umum'];
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('id-ID', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).replace(/\./g, ':');
  };

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="news-card group hover:border-brand-accent/30"
    >
      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-start">
          <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${getCategoryColor(article.category)}`}>
            {article.category}
          </span>
          <span className="text-[10px] text-brand-text-dim font-mono">
             {formatDate(article.publishedAt)}
          </span>
        </div>
        
        <h3 className="text-[15px] font-semibold leading-snug group-hover:text-brand-accent transition-colors">
          <a href={article.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
            {article.title}
          </a>
        </h3>
        
        <p className="text-brand-text-dim text-[13px] leading-relaxed">
          {article.summary}
        </p>

        {article.keyPoints && article.keyPoints.length > 0 && (
          <div className="space-y-1.5 mt-1">
            {article.keyPoints.map((point, i) => (
              <div key={i} className="flex items-start gap-2 text-[11px] text-brand-text-main/70">
                <ChevronRight size={12} className="mt-0.5 text-brand-accent/60" />
                <span>{point}</span>
              </div>
            ))}
          </div>
        )}

        <div className="pt-3 mt-2 border-t border-white/5 flex justify-between items-center text-[11px] text-brand-text-dim">
          <div className="flex items-center gap-1.5">
            <span className="font-medium text-brand-text-main/60">Sumber:</span>
            <span>{article.source}</span>
          </div>
          {article.relevanceScore !== undefined && (
            <div className="flex items-center gap-1 text-brand-green font-semibold">
              <Zap size={10} />
              SKOR: {article.relevanceScore.toFixed(2)}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
