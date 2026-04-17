import React, { useState } from 'react';
import { Search, Filter, Layers } from 'lucide-react';
import { NewsArticle } from '../../types';
import { NewsCard } from '../../components/news/NewsCard';
import { apiService } from '../../services/api';

export const SearchView: React.FC<{ onSearchSuccess?: () => void }> = ({ onSearchSuccess }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<NewsArticle[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    try {
      const data = await apiService.searchArticles(query);
      setResults(data);
      if (onSearchSuccess) onSearchSuccess();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-bold">Cari Berita</h2>
        <p className="text-xs text-brand-text-dim">Gunakan pencarian semantik untuk menemukan berita berdasarkan makna.</p>
      </div>

      <form onSubmit={handleSearch} className="relative">
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Cari 'dampak inflasi terhadap startup'..."
          className="w-full bg-white/5 border border-brand-border rounded-xl px-4 py-3 pr-12 text-sm focus:outline-none focus:border-brand-accent transition-all"
        />
        <button 
          type="submit"
          className="absolute right-2 top-2 bottom-2 px-3 bg-brand-accent text-brand-bg rounded-lg hover:bg-brand-accent/90 transition-colors flex items-center justify-center"
        >
          {isSearching ? (
            <div className="w-4 h-4 border-2 border-brand-bg/30 border-t-brand-bg rounded-full animate-spin" />
          ) : (
            <Search size={16} />
          )}
        </button>
      </form>

      <div className="space-y-4">
        {results.length > 0 ? (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between text-[11px] text-brand-text-dim uppercase tracking-wider">
              <span>{results.length} hasil relevan</span>
              <div className="flex items-center gap-2">
                <Filter size={12} />
                <span>Urutkan: Relevansi</span>
              </div>
            </div>
            <div className="flex flex-col gap-4">
              {results.map((article, idx) => (
                <NewsCard key={idx} article={article} />
              ))}
            </div>
          </div>
        ) : !isSearching && (
          <div className="text-center py-12 text-brand-text-dim">
            <Layers size={32} className="mx-auto mb-3 opacity-20" />
            <p className="text-xs italic">Masukkan pertanyaan atau topik untuk mencari secara semantik.</p>
          </div>
        )}
      </div>
    </div>
  );
};
