import React from 'react';
import { Layers, Zap, RefreshCcw } from 'lucide-react';
import { SystemStatus } from '../../types';
import { apiService } from '../../services/api';

export const RightPanel: React.FC<{ 
  stats?: Record<string, number>, 
  systemStatus: SystemStatus | null,
  onSyncSuccess?: () => void
}> = ({ stats, systemStatus, onSyncSuccess }) => {
  const LIMIT = 500;
  const usage = systemStatus?.gemini_usage || 0;
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
  <div className="flex flex-col gap-6">
    <div className="metric-group">
      <div className="text-[11px] text-brand-text-dim uppercase tracking-wider mb-2">Artikel Diproses (24J)</div>
      <div className="text-3xl font-black text-white mb-1">
        {new Intl.NumberFormat('en-US').format(stats?.total_in_qdrant || 0)}
      </div>
      <div className={`text-[11px] font-bold ${
        (stats?.qdrant_change_percent || 0) > 0 
          ? 'text-brand-green' 
          : (stats?.qdrant_change_percent || 0) < 0 
            ? 'text-red-400' 
            : 'text-brand-text-dim'
      }`}>
        {stats?.qdrant_change_percent !== undefined 
          ? `${stats.qdrant_change_percent > 0 ? '+' : ''}${stats.qdrant_change_percent}% vs Kemarin`
          : 'Stabil vs Kemarin'
        }
      </div>
    </div>

    <div className="metric-group">
      <div className="text-[11px] text-brand-text-dim uppercase tracking-wider mb-3">Statistik Terakhir</div>
      <div className="space-y-3">
        {[
          { label: 'Raw Ingested', value: stats?.raw_articles || 0, color: 'bg-brand-accent' },
          { label: 'Cleaned', value: stats?.filtered_articles || 0, color: 'bg-brand-green' },
          { label: 'Deduplicated', value: stats?.duplicate_discarded || 0, color: 'bg-red-400' },
        ].map((item, i) => (
          <div key={i} className="flex items-center justify-between text-[13px]">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${item.color}`} />
              <span>{item.label}</span>
            </div>
            <span className="text-[10px] font-mono opacity-70">{item.value}</span>
          </div>
        ))}
      </div>
    </div>

    {systemStatus?.agents && (
      <div className="metric-group">
        <div className="text-[11px] text-brand-text-dim uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>AI Agents Pulse</span>
          <div className="flex items-center gap-1.5">
             <div className="w-1 h-1 rounded-full bg-brand-green animate-ping" />
             <span className="text-[7px] text-brand-green font-black tracking-widest">ORCHESTRATED</span>
          </div>
        </div>
        <div className="space-y-3">
          {systemStatus.agents.map((agent) => (
            <div key={agent.id} className="flex items-center justify-between group/agent">
              <div className="flex items-center gap-3">
                <div className={`w-1.5 h-1.5 rounded-full ${
                  agent.status === 'online' ? 'bg-brand-green shadow-[0_0_8px_rgba(16,185,129,0.4)]' :
                  agent.status === 'standby' ? 'bg-brand-accent shadow-[0_0_8px_rgba(59,130,246,0.4)]' :
                  agent.status === 'offline' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]' :
                  'bg-brand-text-dim'
                } ${agent.status !== 'offline' ? 'animate-pulse' : ''}`} />
                <div className="flex flex-col select-none">
                  <span className="text-[13px] font-bold text-white/90 group-hover/agent:text-brand-accent transition-colors leading-snug">{agent.name}</span>
                  <span className={`text-[10px] uppercase tracking-wider font-medium ${
                    agent.status === 'offline' ? 'text-red-400' : 'text-brand-text-dim'
                  }`}>
                    {agent.status === 'online' ? 'Active' : agent.status === 'standby' ? 'Standby' : 'Offline'}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[11px] font-mono text-white/70 leading-tight">{agent.last_run}</div>
                <div className="text-[9px] text-brand-text-dim uppercase tracking-tighter">Activity</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}

    <div className="metric-group">
      <div className="flex justify-between items-end mb-3">
        <div className="text-[11px] text-brand-text-dim uppercase tracking-wider">Gemini Usage</div>
        <div className="text-[9px] px-1.5 py-0.5 bg-brand-accent/10 border border-brand-accent/20 rounded text-brand-accent font-mono">
          {systemStatus?.model_name || 'Gemini Flash'}
        </div>
      </div>
      <div className="flex justify-between text-[11px] font-mono mb-2">
        <span>Daily Limit: {LIMIT} req</span>
        <div className="flex items-center gap-1.5">
          <span className={usage >= LIMIT ? 'text-red-400' : 'text-brand-accent'}>{usage} used</span>
          <button 
            onClick={handleSync}
            className="p-1 hover:bg-white/10 rounded transition-colors text-brand-text-dim hover:text-brand-accent"
            title="SINKRONISASI MANUAL"
          >
            <RefreshCcw size={10} />
          </button>
        </div>
      </div>
      <div className="h-1 bg-white/10 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-500 ${usage >= LIMIT ? 'bg-red-400' : 'bg-brand-accent'}`} 
          style={{ width: `${percentage}%` }} 
        />
      </div>
    </div>

    <div className="mt-auto p-4 bg-brand-accent/10 border border-brand-accent/30 rounded-xl">
      <div className="text-[13px] font-bold mb-1">Sekilas.ai Agentic-RAG</div>
      <div className="text-[11px] text-brand-text-dim mb-3">Sistem ini berjalan otomatis setiap hari menggunakan GitHub Actions.</div>
      <a href="https://github.com/flxhrdyn/Sekilas.ai" target="_blank" rel="noreferrer" className="text-[10px] text-brand-accent font-bold hover:underline">
        LIHAT REPOSITORY →
      </a>
    </div>
  </div>
  );
};
