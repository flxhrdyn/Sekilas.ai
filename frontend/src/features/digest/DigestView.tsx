import { DigestData, StoryGroup } from "../../types";
import { 
  Zap, 
  Clock, 
  ArrowUpRight, 
  Newspaper, 
  TrendingUp, 
  BrainCircuit, 
  FileText,
  Sparkles
} from "lucide-react";

interface DigestViewProps {
  data: DigestData | null;
}

// Helper to determine impact color
const getImpactColor = (impact?: string) => {
  switch (impact?.toLowerCase()) {
    case 'high': return 'text-red-500 border-red-500/30 bg-red-500/10';
    case 'medium': return 'text-orange-500 border-orange-500/30 bg-orange-500/10';
    case 'low': return 'text-blue-500 border-blue-500/30 bg-blue-500/10';
    default: return 'text-blue-500 border-blue-500/30 bg-blue-500/10';
  }
};

// Helper to derive impact if not provided
const deriveImpact = (story: StoryGroup) => {
  if (story.articles.length >= 8) return 'HIGH';
  if (story.articles.length >= 3) return 'MEDIUM';
  return 'LOW';
};

// Source Branding Component
const SourceBadge = ({ source }: { source: string }) => {
  const s = source.toUpperCase();
  let bg = 'bg-brand-accent/20';
  let text = 'text-brand-accent';
  let isIntl = false;

  if (s.includes('KOMPAS')) { bg = 'bg-blue-600/20'; text = 'text-blue-400'; }
  else if (s.includes('DETIK')) { bg = 'bg-blue-500/20'; text = 'text-blue-300'; }
  else if (s.includes('TEMPO')) { bg = 'bg-red-600/20'; text = 'text-red-400'; }
  else if (s.includes('REUTERS')) { bg = 'bg-orange-600/20'; text = 'text-orange-400'; isIntl = true; }
  else if (s.includes('ANTARA')) { bg = 'bg-sky-600/20'; text = 'text-sky-400'; }
  else if (s.includes('TECH IN ASIA')) { bg = 'bg-emerald-600/20'; text = 'text-emerald-400'; isIntl = true; }
  else if (s.includes('BBC') || s.includes('CNN') || s.includes('AL JAZEERA')) { isIntl = true; }

  return (
    <div className="flex items-center gap-1.5">
      <span className={`px-1.5 py-0.5 rounded text-[9px] font-black tracking-tighter ${bg} ${text}`}>
        {s}
      </span>
      <span className="text-[7px] font-bold text-white/20 uppercase tracking-[0.2em]">
        {isIntl ? "INT'L" : "NASIONAL"}
      </span>
    </div>
  );
};

export const DigestView = ({ data }: DigestViewProps) => {
  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center py-32 opacity-50 space-y-4">
        <div className="w-10 h-10 border-2 border-brand-accent border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium tracking-wide">Menyelaraskan Intelijen...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 space-y-16 animate-in fade-in slide-in-from-bottom-6 duration-1000">
      
      {/* 1. Global Headline Box (Restored) */}
      <section className="relative group overflow-visible">
        <div className="absolute inset-0 bg-brand-accent/5 blur-[120px] -z-10 rounded-full opacity-30 group-hover:opacity-50 transition-opacity duration-1000" />
        <div className="bg-brand-sidebar/40 backdrop-blur-2xl border border-white/[0.05] rounded-[2.5rem] p-10 md:p-14 text-center relative shadow-2xl overflow-visible">
          {/* Subtle Radial Gradient Overlay */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(59,130,246,0.1),transparent_70%)] pointer-events-none" />
          
          {/* Badge top center */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-5 py-2 bg-brand-bg border border-brand-accent/30 rounded-full flex items-center gap-2.5 shadow-[0_0_25px_rgba(59,130,246,0.15)] z-20">
            <div className="w-1.5 h-1.5 rounded-full bg-brand-green animate-pulse" />
            <span className="text-[9px] font-black text-white/80 tracking-[0.3em] uppercase">Today's Global Headline</span>
          </div>
          
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-white leading-tight tracking-tight max-w-4xl mx-auto drop-shadow-md">
            {data.headline}
          </h1>
        </div>
      </section>

      {/* Strategic Correlations Area */}
      {data.correlations && data.correlations.length > 0 && (
        <section className="space-y-6">
          <div className="flex items-center gap-3 text-brand-accent/50">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-brand-accent/20 to-transparent" />
            <h2 className="text-[10px] font-black uppercase tracking-[0.4em] italic whitespace-nowrap">Strategic Correlations</h2>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-brand-accent/20 to-transparent" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {data.correlations?.map((cor, idx: number) => (
              <div key={idx} className="bg-[#1a2333]/40 border border-white/5 rounded-2xl p-6 relative overflow-hidden group hover:border-brand-accent/30 transition-all duration-500 shadow-xl">
                <div className="absolute -right-4 -bottom-4 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                  <Sparkles className="w-24 h-24 text-brand-accent" />
                </div>
                <div className="relative space-y-3">
                  <div className="flex items-center gap-2 text-brand-accent font-black text-[8px] uppercase tracking-widest">
                    <Zap className="w-3 h-3" />
                    Correlation analysis #{idx + 1}
                  </div>
                  <h3 className="text-white font-bold text-lg leading-snug">
                    {cor.title}
                  </h3>
                  <p className="text-xs md:text-sm text-brand-text-dim leading-relaxed antialiased font-medium">
                    {cor.analysis}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 2. Top Intelligence Stories (Elite Top 5) */}
      <section className="space-y-12">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-white/90">
            <TrendingUp className="w-5 h-5 text-brand-accent scale-125" />
            <h2 className="text-xl font-black uppercase tracking-[0.3em] italic">Top Curated Intelligence</h2>
          </div>
          <div className="px-3 py-1 bg-brand-accent/5 border border-brand-accent/20 rounded-full text-[9px] font-bold text-brand-accent uppercase tracking-widest">
            Elite Top 5
          </div>
        </div>

        <div className="space-y-12">
          {/* HERO STORY (Rank #1) - RESTORED & ROBUST */}
          {data.top_stories.length > 0 && (
            <div className="group relative">
              <div className="bg-brand-sidebar/60 backdrop-blur-3xl border border-brand-accent/20 rounded-[3rem] overflow-hidden shadow-2xl">
                <div className="p-8 md:p-12 space-y-8">
                  {/* CLEAN HEADER (NO OVERLAP) */}
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="px-4 py-1.5 bg-brand-accent text-white rounded-lg text-[10px] font-black uppercase tracking-widest shadow-[0_4px_15px_rgba(59,130,246,0.3)]">
                        TOP PRIORITY
                      </div>
                      <div className="px-3 py-1.5 bg-white/[0.03] border border-white/[0.05] rounded-lg text-[9px] font-bold text-white/60 uppercase tracking-widest">
                        {data.top_stories[0].total_reports || data.top_stories[0].articles.length} Sourced Reports
                      </div>
                      <div title={data.top_stories[0].impact_reason} className={`px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest border border-white/5 cursor-help ${getImpactColor(data.top_stories[0].impact_level)}`}>
                        {data.top_stories[0].impact_level} IMPACT
                      </div>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.02] border border-white/[0.05] rounded-lg">
                      <BrainCircuit className="w-4 h-4 text-brand-accent/70" />
                      <span className="text-[8px] font-bold text-white/20 uppercase tracking-tighter">AI Synthesized</span>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <h3 className="text-3xl md:text-4xl font-black text-white leading-[1.1] tracking-tight">
                      {data.top_stories[0].title}
                    </h3>
                    
                    <div className="bg-white/[0.02] border border-white/[0.03] rounded-[2rem] p-8 md:p-10 shadow-inner">
                       <div className="flex items-center gap-2.5 text-brand-accent font-black text-[10px] uppercase tracking-[0.3em] mb-6 opacity-80">
                         <Sparkles className="w-4 h-4" />
                         Analyst Synthesis
                       </div>
                      <ol className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
                        {data.top_stories[0].synthesis.map((point: string, idx: number) => (
                          <li key={idx} className="flex gap-5 text-base md:text-lg text-white/90 leading-relaxed font-semibold group/point">
                            <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-brand-accent/10 border border-brand-accent/30 flex items-center justify-center text-xs font-black text-brand-accent group-hover/point:bg-brand-accent group-hover/point:text-white transition-all duration-300">
                              {idx + 1}
                            </span>
                            <span className="pt-0.5">{point}</span>
                          </li>
                        ))}
                      </ol>
                    </div>

                    {/* SOURCE VALIDATION (Hyperlinked) */}
                    <div className="pt-4 space-y-4">
                      <div className="flex items-center gap-3">
                         <span className="text-[9px] font-black text-white/20 uppercase tracking-[0.4em] whitespace-nowrap">Source Validation</span>
                         <div className="h-px w-full bg-gradient-to-r from-white/10 to-transparent" />
                      </div>
                      <div className="flex flex-wrap gap-4">
                        {data.top_stories[0].articles.map((article: any, idx: number) => (
                          <a 
                            key={idx} 
                            href={article.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-brand-accent/40 hover:bg-white/[0.05] transition-all duration-300 group/article"
                          >
                            <SourceBadge source={article.source} />
                            <span className="text-xs font-medium text-white/40 group-hover/article:text-white transition-colors max-w-[150px] truncate">
                              {article.title}
                            </span>
                            <ArrowUpRight className="w-3 h-3 text-white/10 group-hover/article:text-brand-accent" />
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SECONDARY STORIES GRID (Rank #2-5) */}
          {data.top_stories.length > 1 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {data.top_stories.slice(1).map((story) => {
                const impact = story.impact_level || 'LOW';
                const reportsCount = story.total_reports || story.articles.length;

                return (
                  <div key={story.id} className="group relative">
                    <div className="bg-brand-card/30 backdrop-blur-xl border border-white/[0.05] rounded-[2rem] overflow-hidden hover:border-brand-accent/30 transition-all duration-500 shadow-xl h-full flex flex-col">
                      <div className="p-8 space-y-6 flex-1">
                        <div className="flex justify-between items-center">
                          <div title={story.impact_reason} className={`px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest border ${getImpactColor(impact)}`}>
                            {impact}
                          </div>
                          <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest">
                            {reportsCount} Sources
                          </span>
                        </div>

                        <h3 className="text-xl font-bold text-white leading-tight tracking-tight group-hover:text-brand-accent transition-colors">
                          {story.title}
                        </h3>

                        <div className="space-y-2.5">
                          {story.synthesis.slice(0, 2).map((point: string, idx: number) => (
                            <div key={idx} className="flex gap-2.5 text-xs md:text-sm text-white/60 leading-tight font-medium">
                              <div className="w-1 h-1 rounded-full bg-brand-accent/40 mt-1.5 flex-shrink-0" />
                              {point}
                            </div>
                          ))}
                        </div>
                      </div>
                        <div className="px-6 py-4 bg-white/[0.02] border-t border-white/[0.03] flex flex-wrap gap-x-6 gap-y-3">
                           {story.articles.slice(0, 2).map((article: any, idx: number) => (
                             <a 
                               key={idx} 
                               href={article.url} 
                               target="_blank" 
                               rel="noopener noreferrer"
                               className="flex items-center gap-2 group/src"
                             >
                               <SourceBadge source={article.source} />
                               <ArrowUpRight className="w-3 h-3 text-white/10 group-hover/src:text-brand-accent transition-colors" />
                             </a>
                           ))}
                        </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* 3. Supplemental Updates */}
      <section className="space-y-8">
        <div className="flex items-center gap-3 text-white/90">
          <FileText className="w-5 h-5 text-brand-accent" />
          <h2 className="text-lg font-bold uppercase tracking-widest italic flex items-center gap-3">
            Supplemental Updates
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-12">
          {Object.entries(data.other_news).map(([category, articles]) => (
            <div key={category} className="space-y-6">
              <div className="flex items-center justify-between border-b border-brand-border/30 pb-3">
                <h3 className="text-xs font-black text-brand-accent uppercase tracking-[0.2em]">
                  {category}
                </h3>
                <span className="text-[10px] font-bold text-white/20 uppercase">
                  {articles.length} Updates
                </span>
              </div>
              
              <div className="space-y-6">
                {articles.slice(0, 2).map((article, idx) => (
                  <a 
                    key={idx} 
                    href={article.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block group/item"
                  >
                    <div className="space-y-2">
                      <h4 className="text-sm font-bold text-brand-text-main group-hover/item:text-brand-accent transition-colors leading-snug">
                        {article.title}
                      </h4>
                      <div className="flex items-center gap-3 text-[10px] text-white/30 font-bold uppercase">
                        <span>{article.source}</span>
                        <span className="w-1 h-1 rounded-full bg-white/10" />
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3 h-3" />
                          {new Date(article.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="pt-24 pb-12 text-center opacity-20 hover:opacity-100 transition-opacity duration-500">
        <p className="text-[10px] font-black uppercase tracking-[0.4em]">
          Sekilas.ai Intelligence Engine • {data.date}
        </p>
      </footer>
    </div>
  );
};

