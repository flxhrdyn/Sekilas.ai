import React from 'react';
import { motion } from "motion/react";
import { Database, Server, Zap, Activity, HardDrive } from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';

const LATENCY_DATA = [
  { time: '08:00', value: 45 }, { time: '08:10', value: 52 }, { time: '08:20', value: 48 },
  { time: '08:30', value: 61 }, { time: '08:40', value: 55 }, { time: '08:50', value: 42 },
  { time: '09:00', value: 44 }, { time: '09:10', value: 50 }, { time: '09:20', value: 120 },
  { time: '09:30', value: 58 }, { time: '09:40', value: 49 }, { time: '09:50', value: 45 }
];

const STORAGE_DATA = [
  { name: 'News_Main', count: 12450, size: '2.4GB' },
  { name: 'Sources_Metadata', count: 48200, size: '0.8GB' },
  { name: 'Agent_Reasoning', count: 8900, size: '1.2GB' },
  { name: 'User_Context', count: 1200, size: '0.1GB' }
];

interface MetricCardProps {
  title: string;
  value: string;
  unit: string;
  trend: string;
  icon: React.ComponentType<any>;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, unit, trend, icon: Icon }) => (
  <div className="data-card p-5">
    <div className="flex items-center justify-between mb-3 text-white/40">
      <Icon className="w-4 h-4 text-brand-blue" />
      <span className="text-[10px] font-bold uppercase tracking-widest leading-none text-emerald-500">{trend}</span>
    </div>
    <div className="flex items-baseline gap-1">
      <span className="mono-stat text-3xl font-bold text-white">{value}</span>
      <span className="text-sm font-medium text-white/30">{unit}</span>
    </div>
    <p className="text-[10px] text-white/20 uppercase tracking-widest mt-2 font-display">{title}</p>
  </div>
);

export const VectorHealthView: React.FC = () => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-8 max-w-6xl mx-auto flex flex-col gap-8 font-sans"
    >
      <div className="flex items-end justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-bold flex items-center gap-3 text-white">
            <Database className="w-8 h-8 text-brand-blue" />
            Vector DB Health
          </h2>
          <p className="text-white/40 text-sm font-medium">Status infrastruktur Qdrant & Knowledge Base Retrieval.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Total Vectors" value="1.4M" unit="dims: 1536" trend="+12k/day" icon={Server} />
        <MetricCard title="Search Latency" value="42" unit="ms (p99)" trend="Stable" icon={Zap} />
        <MetricCard title="Index Refresh" value="2.4" unit="s" trend="-0.2s" icon={Activity} />
        <MetricCard title="Disk Usage" value="48" unit="GB / 128" trend="Optimize soon" icon={HardDrive} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="data-card p-0 overflow-hidden flex flex-col bg-surface-muted/30">
          <div className="p-6 border-b border-white/5">
            <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] mb-4">Indexing Latency (12H)</h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={LATENCY_DATA}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#666' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#666' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#111114', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px' }}
                    itemStyle={{ color: '#fff', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#3b82f6" fillOpacity={1} fill="url(#colorValue)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="data-card flex flex-col bg-surface-muted/30">
          <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] mb-6">Collection Metadata</h4>
          <div className="space-y-4">
            {STORAGE_DATA.map((col) => (
              <div key={col.name} className="p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all group">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-white group-hover:text-brand-blue transition-colors underline decoration-brand-blue/20">{col.name}</span>
                  <span className="text-xs font-mono text-emerald-500">HEALTHY</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex flex-col">
                    <span className="text-[9px] text-white/20 uppercase tracking-widest">Fragments</span>
                    <span className="text-xs font-mono text-white/70">{col.count.toLocaleString()}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[9px] text-white/20 uppercase tracking-widest">Storage</span>
                    <span className="text-xs font-mono text-white/70">{col.size}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
