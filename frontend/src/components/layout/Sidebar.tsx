import React from 'react';
import {
  Newspaper,
  Search,
  MessageSquare,
  TrendingUp,
  Layers,
  Zap,
  Globe,
  Cpu
} from 'lucide-react';
import { motion } from 'motion/react';
import { Tab, View } from '../../types';

interface SidebarProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  activeView: View;
  setActiveView: (view: View) => void;
}

const SidebarItem = ({ 
  icon: Icon, 
  label, 
  active, 
  onClick 
}: { 
  icon: React.ComponentType<any>, 
  label: string, 
  active: boolean, 
  onClick: () => void 
}) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative cursor-pointer ${
      active 
        ? "bg-brand-blue/10 text-brand-blue" 
        : "text-white/50 hover:bg-white/5 hover:text-white"
    }`}
  >
    <Icon size={18} className={`transition-transform duration-200 ${active ? "scale-110 text-brand-blue" : "group-hover:scale-110"}`} />
    <span className="text-sm font-medium">{label}</span>
    {active && (
      <motion.div 
        layoutId="sidebar-active-pill" 
        className="ml-auto w-1 h-5 bg-brand-blue rounded-full absolute right-3" 
        transition={{ type: "spring", stiffness: 380, damping: 30 }}
      />
    )}
  </button>
);

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeTab, 
  setActiveTab, 
  activeView, 
  setActiveView 
}) => {
  return (
    <aside className="w-[260px] bg-brand-sidebar border-r border-white/5 flex flex-col p-6 gap-8 fixed h-full z-20">
      <div 
        onClick={() => setActiveView('landing')}
        className="flex items-center gap-3 px-2 cursor-pointer hover:opacity-80 transition-opacity group"
      >
        <div className="w-9 h-9 bg-brand-blue rounded-xl flex items-center justify-center shadow-lg shadow-brand-blue/20 group-hover:scale-110 transition-transform">
          <Zap size={18} className="text-white" fill="white" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white m-0">sekilas.ai</h1>
          <p className="text-[9px] text-white/40 uppercase tracking-widest font-mono">Intelligence Engine</p>
        </div>
      </div>

      <nav className="flex-1 flex flex-col gap-2 font-sans">
        <SidebarItem 
          icon={Globe} 
          label="Beranda" 
          active={activeView === 'landing'} 
          onClick={() => setActiveView('landing')} 
        />
        <div className="h-px bg-white/5 my-2 mx-4" />
        
        <SidebarItem
          icon={Newspaper}
          label="Digest Harian"
          active={activeView === 'dashboard' && activeTab === 'digest'}
          onClick={() => {
            setActiveView('dashboard');
            setActiveTab('digest');
          }}
        />
        <SidebarItem
          icon={Search}
          label="Cari Berita"
          active={activeView === 'dashboard' && activeTab === 'search'}
          onClick={() => {
            setActiveView('dashboard');
            setActiveTab('search');
          }}
        />
        <SidebarItem
          icon={MessageSquare}
          label="Tanya AI Agent"
          active={activeView === 'dashboard' && activeTab === 'qa'}
          onClick={() => {
            setActiveView('dashboard');
            setActiveTab('qa');
          }}
        />

        <div className="mt-6 flex flex-col gap-2">
          <h4 className="px-4 text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] py-2">Sistem</h4>
          <SidebarItem 
            icon={TrendingUp} 
            label="Pipeline Monitor" 
            active={activeView === 'dashboard' && activeTab === 'pipeline'} 
            onClick={() => {
              setActiveView('dashboard');
              setActiveTab('pipeline');
            }} 
          />
          <SidebarItem 
            icon={Layers} 
            label="Vector DB Health" 
            active={activeView === 'dashboard' && activeTab === 'vector'} 
            onClick={() => {
              setActiveView('dashboard');
              setActiveTab('vector');
            }} 
          />
        </div>
      </nav>

      <div className="mt-auto p-4 bg-white/5 rounded-2xl border border-white/10 font-sans">
        <div className="flex items-center gap-2 mb-3 select-none">
          <Cpu size={14} className="text-brand-blue" />
          <span className="text-xs font-semibold text-white/80">Gemini Nano 3.1</span>
        </div>
        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden mb-2">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: "47%" }}
            className="h-full bg-brand-blue" 
          />
        </div>
        <p className="text-[10px] text-white/40 font-mono">Quota: 237/500 used</p>
      </div>
    </aside>
  );
};
