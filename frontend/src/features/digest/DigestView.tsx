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
      
      {/* 1. Global Headline Box */}
      <section className="relative group">
        <div className="absolute inset-0 bg-brand-accent/5 blur-3xl -z-10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
        <div className="bg-brand-background/40 backdrop-blur-sm border border-brand-border/50 rounded-3xl p-8 md:p-10 text-center relative">
          {/* Decorative Line */}
          <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-brand-border to-transparent" />
          
          {/* Badge top center */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-4 py-1.5 bg-brand-background border border-brand-border rounded-full flex items-center gap-2 shadow-2xl z-10">
            <div className="w-1.5 h-1.5 rounded-full bg-brand-accent animate-pulse" />
            <span className="text-[10px] font-bold text-white/60 tracking-[0.2em] uppercase">Global Headline</span>
          </div>
          
          <h1 className="text-xl md:text-2xl lg:text-3xl font-extrabold text-white leading-[1.3] tracking-tight max-w-3xl mx-auto">
            "{data.headline.replace("Headline: ", "")}"
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

      {/* 2. Top Intelligence Stories */}
      <section className="space-y-8">
        <div className="flex items-center gap-3 text-white/90">
          <TrendingUp className="w-5 h-5 text-brand-accent" />
          <h2 className="text-lg font-bold uppercase tracking-widest italic">Top Intelligence Stories</h2>
        </div>

        <div className="space-y-10">
          {data.top_stories.map((story) => {
            const impact = story.impact_level || 'LOW';
            const reportsCount = story.total_reports || story.articles.length;

            return (
              <div key={story.id} className="bg-[#1a2333]/80 backdrop-blur-md border border-white/5 rounded-3xl overflow-hidden hover:border-brand-accent/30 transition-all duration-500 shadow-2xl">
                <div className="p-8 md:p-10 space-y-6">
                  {/* Header: Badges & Brain Icon */}
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-4">
                      <div title={story.impact_reason} className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest cursor-help ${getImpactColor(impact)}`}>
                        IMPACT: {impact}
                      </div>
                      <div className="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em]">
                        {reportsCount} Reports Sourced
                      </div>
                    </div>
                    <div className="p-2 bg-brand-accent/10 border border-brand-accent/20 rounded-xl">
                      <BrainCircuit className="w-4 h-4 text-brand-accent" />
                    </div>
                  </div>

                  {/* Title */}
                  <h3 className="text-xl md:text-2xl font-bold text-white leading-tight tracking-tight">
                    {story.title}
                  </h3>

                  {/* Analyst Brief */}
                  <div className="bg-[#1e293b]/50 border border-white/5 rounded-2xl p-6 md:p-8 space-y-5">
                    <div className="flex items-center gap-2 text-brand-accent font-black text-[9px] uppercase tracking-[0.2em]">
                      <Sparkles className="w-3.5 h-3.5" />
                      Analyst Brief
                    </div>
                    <ol className="space-y-4">
                      {story.synthesis.map((point, idx) => (
                        <li key={idx} className="flex gap-4 text-sm md:text-base text-brand-text-main/90 leading-relaxed font-medium">
                          <span className="text-brand-accent font-black">{idx + 1}.</span>
                          {point}
                        </li>
                      ))}
                    </ol>
                  </div>

                  {/* Related Reports */}
                  <div className="pt-4 space-y-4">
                    <h4 className="text-[9px] font-black text-white/20 uppercase tracking-[0.3em]">Related Reports</h4>
                    <div className="space-y-3">
                      {story.articles.slice(0, 3).map((article, idx) => (
                        <a 
                          key={idx} 
                          href={article.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="flex items-center gap-4 group/article"
                        >
                          <SourceBadge source={article.source} />
                          <span className="text-xs text-brand-text-dim group-hover/article:text-brand-accent transition-colors">
                            {article.title}
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
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

