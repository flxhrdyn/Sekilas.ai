import React from 'react';
import { DigestData, NewsArticle } from '../../types';
import { NewsCard } from '../../components/news/NewsCard';

export const DigestView: React.FC<{ data: DigestData | null }> = ({ data }) => {
  if (!data) return <div className="text-center py-20 opacity-50">Memuat data digest...</div>;

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between mb-2">
        <h2 className="text-2xl font-bold text-white">Insight Digest Hari Ini</h2>
      </div>
      <div className="mb-8">
        <div className="p-4 bg-brand-card/30 border border-brand-border rounded-xl italic text-sm text-brand-text-main/90 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-brand-accent" />
          "{data.headline}"
        </div>
      </div>

      <div className="space-y-8">
        {Object.entries(data.category_digests).map(([category, articles]) => (
          <div key={category} className="space-y-4">
            <div className="flex items-center gap-4">
              <h3 className="text-sm font-bold uppercase tracking-widest text-brand-accent/80 whitespace-nowrap">
                {category}
              </h3>
              <div className="h-[1px] w-full bg-white/10" />
            </div>
            <div className="grid grid-cols-1 gap-4">
              {articles.map((article: any, idx: number) => (
                <NewsCard 
                  key={idx} 
                  article={{
                    title: article.title,
                    summary: article.summary,
                    keyPoints: article.key_points || [],
                    source: article.source,
                    category: article.category || category,
                    publishedAt: article.published_at || "",
                    url: article.url
                  }} 
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
