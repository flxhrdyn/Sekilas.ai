import React from 'react';
import {
  Newspaper,
  Search,
  MessageSquare,
  TrendingUp,
  Layers,
  Zap
} from 'lucide-react';
import { Tab } from '../../types';

interface SidebarProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
}

const SidebarItem = ({ icon: Icon, label, active, onClick }: { icon: any, label: string, active: boolean, onClick: () => void }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-6 py-3 transition-all duration-200 border-l-4 ${active
        ? 'bg-brand-accent/5 text-brand-accent border-brand-accent'
        : 'text-brand-text-dim border-transparent hover:text-brand-text-main hover:bg-white/5'
      }`}
  >
    <Icon size={18} />
    <span className="text-sm font-medium">{label}</span>
  </button>
);

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <aside className="w-[240px] bg-brand-sidebar border-r border-brand-border flex flex-col fixed h-full z-20">
      <div className="px-6 py-8 flex items-center gap-4">
        <div className="w-10 h-10 bg-brand-accent rounded-xl flex items-center justify-center text-white shadow-[0_0_20px_rgba(59,130,246,0.2)]">
          <Zap size={22} fill="white" />
        </div>
        <div className="flex flex-col">
          <span className="font-black text-xl tracking-tighter leading-none">sekilas.ai</span>
          <span className="text-[7px] font-bold text-brand-text-dim tracking-[0.3em] uppercase mt-1.5 opacity-60">
            Intelligence Engine
          </span>
        </div>
      </div>

      <nav className="flex-1 flex flex-col">
        <SidebarItem
          icon={Newspaper}
          label="Digest Harian"
          active={activeTab === 'digest'}
          onClick={() => setActiveTab('digest')}
        />
        <SidebarItem
          icon={Search}
          label="Cari Berita"
          active={activeTab === 'search'}
          onClick={() => setActiveTab('search')}
        />
        <SidebarItem
          icon={MessageSquare}
          label="Tanya AI Agent"
          active={activeTab === 'qa'}
          onClick={() => setActiveTab('qa')}
        />

        <div className="mt-8 px-6 text-[11px] font-bold uppercase text-slate-500 tracking-widest mb-2">Sistem</div>
        <SidebarItem icon={TrendingUp} label="Pipeline Monitor" active={false} onClick={() => { }} />
        <SidebarItem icon={Layers} label="Vector DB Health" active={false} onClick={() => { }} />
      </nav>
    </aside>
  );
};
