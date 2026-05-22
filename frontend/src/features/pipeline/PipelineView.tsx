import React from 'react';
import { motion } from "motion/react";
import { Layers, Terminal, Activity, BarChart3 } from "lucide-react";
import { 
  BarChart, 
  Bar, 
  ResponsiveContainer 
} from 'recharts';

const LATENCY_DATA = [
  { time: '08:00', value: 45 }, { time: '08:10', value: 52 }, { time: '08:20', value: 48 },
  { time: '08:30', value: 61 }, { time: '08:40', value: 55 }, { time: '08:50', value: 42 },
  { time: '09:00', value: 44 }, { time: '09:10', value: 50 }, { time: '09:20', value: 120 },
  { time: '09:30', value: 58 }, { time: '09:40', value: 49 }, { time: '09:50', value: 45 }
];

interface PipelineStepProps {
  name: string;
  status: string;
  metrics: Record<string, string>;
  delay?: number;
  isLast?: boolean;
}

const PipelineStep: React.FC<PipelineStepProps> = ({ name, status, metrics, delay = 0, isLast = false }) => (
  <motion.div 
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay }}
    className="relative"
  >
    <div className="flex items-center gap-6 p-6 bg-white/[0.02] border border-white/5 rounded-2xl hover:border-brand-blue/30 transition-colors group">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${status === 'Active' ? 'bg-brand-blue/20 text-brand-blue' : 'bg-white/5 text-white/20'}`}>
        <Layers className="w-6 h-6" />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-bold text-lg group-hover:text-brand-blue transition-colors text-white">{name}</h3>
          <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-tighter ${status === 'Active' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-white/5 text-white/30'}`}>{status}</span>
        </div>
        <div className="flex gap-6 mt-3 font-mono text-[10px]">
          {Object.entries(metrics).map(([key, val]) => (
            <div key={key} className="flex flex-col">
              <span className="text-white/20 uppercase tracking-widest">{key}</span>
              <span className="text-white/60 font-bold">{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
    {/* Connector Particle */}
    {!isLast && (
      <div className="absolute -bottom-8 left-12 w-0.5 h-8 bg-white/5">
        <motion.div 
          animate={{ top: [0, 32], opacity: [0, 1, 0] }}
          transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
          className="absolute w-1.5 h-1.5 bg-brand-blue rounded-full -left-[2.5px] blur-[1px]"
        />
      </div>
    )}
  </motion.div>
);

export const PipelineView: React.FC = () => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-8 max-w-5xl mx-auto flex flex-col gap-10"
    >
      <div className="flex items-end justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-bold flex items-center gap-3 text-white">
            <Activity className="w-8 h-8 text-brand-blue" />
            Pipeline Monitor
          </h2>
          <p className="text-white/40 text-sm">Pemantauan real-time alur kerja Agentic-RAG dari ingestion hingga sintesis.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-white/30 uppercase tracking-widest font-bold">Total Throughput</span>
            <span className="mono-stat text-xl font-bold text-white">1.2k <span className="text-xs text-white/30">req/min</span></span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Flow */}
        <div className="lg:col-span-2 flex flex-col gap-8">
          <PipelineStep 
            name="Smart Scraper" 
            status="Active" 
            metrics={{ Throughput: "420/min", Latency: "1.2s", Success: "99.8%" }}
            delay={0.1}
          />
          <PipelineStep 
            name="Gatekeeper Filter" 
            status="Active" 
            metrics={{ Throughput: "380/min", Latency: "0.8s", Success: "100%" }}
            delay={0.2}
          />
          <PipelineStep 
            name="Embedding Engine" 
            status="Active" 
            metrics={{ Throughput: "350/min", Latency: "2.4s", Success: "99.4%" }}
            delay={0.3}
          />
          <PipelineStep 
            name="Executive Synthesis" 
            status="Active" 
            metrics={{ Throughput: "120/min", Latency: "4.2s", Success: "98.9%" }}
            delay={0.4}
            isLast={true}
          />
        </div>

        {/* Right Column: Mini Stats & Logs */}
        <div className="flex flex-col gap-6 font-sans">
          <div className="data-card bg-surface-muted/30">
            <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] mb-4">Error Log Rate</h4>
            <div className="h-24">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={LATENCY_DATA.slice(-6)}>
                  <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="data-card flex-1 flex flex-col min-h-[400px]">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] flex items-center gap-2">
                <Terminal className="w-3 h-3 text-brand-blue" /> Live Logs
              </h4>
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <div className="flex-1 font-mono text-[10px] text-white/40 space-y-2 overflow-hidden">
              <p className="text-emerald-500/60">[03:32:01] SCRAPER_INIT: New bundle detected (12 sources)</p>
              <p>[03:32:04] GATEKEEPER: Filtering noise... (3 sources dropped)</p>
              <p>[03:32:08] EMBEDDER: Generating vectors for bundle #TX-192</p>
              <p className="text-brand-blue/60">[03:32:12] SYNTHESIZER: Multi-agent synthesis complete</p>
              <p>[03:32:15] BROADCAST: Notifying 1,240 subscribers</p>
              <p className="text-amber-500/40">[03:32:20] WARN: Higher latency in Node-04-SG</p>
              <p className="text-white/10 italic animate-pulse">Waiting for next event...</p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
