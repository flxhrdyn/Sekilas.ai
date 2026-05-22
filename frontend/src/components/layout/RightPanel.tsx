import React from 'react';
import { Layers, Zap, RefreshCcw } from 'lucide-react';
import { SystemStatus } from '../../types';
import { apiService } from '../../services/api';

export const RightPanel: React.FC<{ 
  stats?: Record<string, number>, 
  systemStatus: SystemStatus | null,
  onSyncSuccess?: () => void
}> = ({ stats, systemStatus, onSyncSuccess }) => {
  const LIMIT = 1000;
  const usage = systemStatus?.llm_usage || 0;
  const percentage = Math.min((usage / LIMIT) * 100, 100);

  const handleSync = async () => {
    const newVal = window.prompt("Masukkan jumlah request yang tertera di Google AI Studio:", usage.toString());
    if (newVal !== null) {
      const count = parseInt(newVal);
      if (!isNaN(count)) {
        try {
          await apiService.updateSystemUsage(count);
          if (onSyncSuccess) onSyncSuccess();
        } catch (err) {
          alert("Gagal memperbarui status.");
        }
      }
    }
  };

  return (
    <div className="flex flex-col gap-6 font-sans">
      <div className="data-card bg-surface-muted/30">
        <div className="text-[10px] text-white/30 font-bold uppercase tracking-[0.2em] mb-2">Artikel Diproses (24J)</div>
        <div className="text-4xl font-extrabold text-white mb-1 mono-stat leading-none">
          {new Intl.NumberFormat('en-US').format(stats?.total_in_qdrant || 0)}
        </div>
        <div className={`text-[10px] font-bold ${
          (stats?.qdrant_change_percent || 0) > 0 
            ? 'text-emerald-400' 
            : (stats?.qdrant_change_percent || 0) < 0 
              ? 'text-red-400' 
              : 'text-white/30'
        }`}>
          {stats?.qdrant_change_percent !== undefined 
            ? `${stats.qdrant_change_percent > 0 ? '+' : ''}${stats.qdrant_change_percent}% vs Kemarin`
            : 'Stabil vs Kemarin'
          }
        </div>
      </div>

      <div className="data-card bg-surface-muted/30">
        <div className="text-[10px] text-white/30 font-bold uppercase tracking-[0.2em] mb-4">Statistik Terakhir</div>
        <div className="space-y-3">
          {[
            { label: 'Raw Ingested', value: stats?.raw_articles || 0, color: 'bg-brand-blue' },
            { label: 'Cleaned', value: stats?.filtered_articles || 0, color: 'bg-emerald-500' },
            { label: 'Deduplicated', value: stats?.duplicate_discarded || 0, color: 'bg-red-500' },
          ].map((item, i) => (
            <div key={i} className="flex items-center justify-between text-sm group">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${item.color}`} />
                <span className="text-white/60 group-hover:text-white transition-colors">{item.label}</span>
              </div>
              <span className="text-xs font-mono font-bold text-white/70">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {systemStatus?.agents && (
        <div className="data-card bg-surface-muted/30">
          <div className="text-[10px] text-white/30 font-bold uppercase tracking-[0.2em] mb-4 flex items-center justify-between">
            <span>AI Agents Status</span>
            <div className="flex items-center gap-1.5">
               <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
               <span className="text-[8px] text-emerald-500 font-bold tracking-widest">ORCHESTRATED</span>
            </div>
          </div>
          <div className="space-y-4">
            {systemStatus.agents.map((agent) => (
              <div key={agent.id} className="flex items-center justify-between group/agent">
                <div className="flex items-center gap-3">
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    agent.status === 'online' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)] animate-pulse' :
                    agent.status === 'standby' ? 'bg-brand-blue shadow-[0_0_8px_rgba(59,130,246,0.4)] animate-pulse' :
                    agent.status === 'offline' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]' :
                    'bg-white/20'
                  }`} />
                  <div className="flex flex-col select-none">
                    <span className="text-xs font-bold text-white/90 group-hover/agent:text-brand-blue transition-colors leading-snug">{agent.name}</span>
                    <span className={`text-[9px] uppercase tracking-wider font-semibold ${
                      agent.status === 'offline' ? 'text-red-400' : 'text-white/30'
                    }`}>
                      {agent.status === 'online' ? 'Active' : agent.status === 'standby' ? 'Standby' : 'Offline'}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-mono text-white/50 leading-tight font-bold">{agent.last_run || '11:20 AM'}</div>
                  <div className="text-[8px] text-white/20 uppercase tracking-tighter">Activity</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="data-card bg-surface-muted/30">
        <div className="flex justify-between items-end mb-3">
          <div className="text-[10px] text-white/30 font-bold uppercase tracking-[0.2em]">LLM Usage</div>
          <div className="text-[9px] px-1.5 py-0.5 bg-brand-blue/10 border border-brand-blue/20 rounded text-brand-blue font-mono">
            {systemStatus?.model_name || 'Groq LLM'}
          </div>
        </div>
        <div className="flex justify-between text-[11px] font-mono mb-2">
          <span className="text-white/50">Daily Limit: {LIMIT} req</span>
          <div className="flex items-center gap-1.5">
            <span className={`font-bold ${usage >= LIMIT ? 'text-red-400' : 'text-brand-blue'}`}>{usage} used</span>
            <button 
              onClick={handleSync}
              className="p-1 hover:bg-white/10 rounded transition-colors text-white/40 hover:text-brand-blue cursor-pointer"
              title="SINKRONISASI MANUAL"
            >
              <RefreshCcw size={10} />
            </button>
          </div>
        </div>
        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ${usage >= LIMIT ? 'bg-red-500' : 'bg-brand-blue'}`} 
            style={{ width: `${percentage}%` }} 
          />
        </div>
      </div>

      <div className="p-4 bg-white/5 border border-white/10 rounded-2xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-radial-gradient from-brand-blue/5 to-transparent pointer-events-none" />
        <div className="text-[13px] font-bold mb-1 text-white leading-none">Sekilas.ai Agentic-RAG</div>
        <div className="text-[11px] text-white/40 mb-3">Sistem ini berjalan otomatis setiap hari menggunakan GitHub Actions.</div>
        <a href="https://github.com/flxhrdyn/Sekilas.ai" target="_blank" rel="noreferrer" className="text-[10px] text-brand-blue font-bold hover:underline inline-flex items-center gap-1 cursor-pointer">
          LIHAT REPOSITORY →
        </a>
      </div>
    </div>
  );
};
