import React from 'react';
import { 
  Newspaper, 
  Search, 
  MessageSquare, 
  TrendingUp, 
  Layers 
} from 'lucide-react';
import { Tab } from '../../types';

interface SidebarProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
}

const SidebarItem = ({ icon: Icon, label, active, onClick }: { icon: any, label: string, active: boolean, onClick: () => void }) => (
  <button 
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-6 py-3 transition-all duration-200 border-l-4 ${
      active 
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
      <div className="px-6 py-8 flex items-center gap-3">
        <div className="w-8 h-8 bg-brand-accent rounded-lg flex items-center justify-center text-brand-bg font-extrabold text-lg">
          S
        </div>
        <span className="font-bold text-xl tracking-tight">sekilas.ai</span>
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
        <SidebarItem icon={TrendingUp} label="Pipeline Monitor" active={false} onClick={() => {}} />
        <SidebarItem icon={Layers} label="Vector DB Health" active={false} onClick={() => {}} />
      </nav>
    </aside>
  );
};
