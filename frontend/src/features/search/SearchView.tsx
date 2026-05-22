import React, { useState } from 'react';
import { Search, Filter, Layers, Info, ChevronRight } from 'lucide-react';
import { motion } from "motion/react";
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
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-5xl mx-auto px-6 py-12 space-y-10 font-sans"
    >
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold text-white">Cari Berita</h2>
        <p className="text-white/40 text-sm">Gunakan pencarian semantik untuk menemukan berita berdasarkan makna mendalam.</p>
      </div>

      <form onSubmit={handleSearch} className="relative group">
        <div className="absolute inset-0 bg-brand-blue/5 blur-2xl rounded-2xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-700 pointer-events-none" />
        <div className="relative">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-white/30 group-focus-within:text-brand-blue transition-colors" />
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Apa yang ingin Anda telusuri hari ini?" 
            className="w-full bg-surface-muted border border-white/10 rounded-2xl py-6 pl-16 pr-32 text-lg text-white focus:outline-none focus:ring-2 focus:ring-brand-blue/30 focus:border-brand-blue/50 transition-all placeholder:text-white/20 font-sans"
          />
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <button 
              type="submit"
              disabled={isSearching}
              className="bg-brand-blue hover:bg-brand-blue/90 disabled:opacity-50 text-white px-6 py-3 rounded-xl text-sm font-bold shadow-lg shadow-brand-blue/20 hover:shadow-brand-blue/30 active:scale-95 transition-all flex items-center gap-2 cursor-pointer select-none"
            >
              {isSearching ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Mencari...
                </>
              ) : (
                <>
                  Cari <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      <div className="space-y-6">
        {results.length > 0 ? (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-4"
          >
            <div className="flex items-center justify-between text-[11px] text-white/30 uppercase tracking-widest font-mono select-none">
              <span>{results.length} HASIL RELEVAN</span>
              <div className="flex items-center gap-2">
                <Filter size={12} />
                <span>Urutkan: Relevansi</span>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4">
              {results.map((article, idx) => (
                <NewsCard key={idx} article={article} />
              ))}
            </div>
          </motion.div>
        ) : !isSearching && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col gap-6"
          >
            <div className="data-card bg-surface-muted/20 border-dashed flex items-start gap-4">
              <Info className="w-5 h-5 text-brand-blue mt-0.5 shrink-0" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-white leading-none">Pencarian Konseptual Pintar</h4>
                <p className="text-xs text-white/40 leading-relaxed">
                  Mesin kami memetakan query Anda ke ruang vektor berdimensi tinggi, memungkinkan pencarian berita yang menangkap intensi dan topik, bahkan jika kata kunci tidak cocok persis.
                </p>
              </div>
            </div>
            
            <div className="text-center py-20 text-white/30 select-none">
              <Layers size={40} className="mx-auto mb-4 opacity-20 text-brand-blue animate-float" />
              <p className="text-sm italic font-medium">Masukkan pertanyaan atau topik untuk mencari secara semantik.</p>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};
