import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Sidebar } from './components/layout/Sidebar';
import { RightPanel } from './components/layout/RightPanel';
import { DigestView } from './features/digest/DigestView';
import { SearchView } from './features/search/SearchView';
import { QAView } from './features/qa/QAView';
import { apiService } from './services/api';
import { Tab, DigestData, SystemStatus } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('digest');
  const [digest, setDigest] = useState<DigestData | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  const refreshSystemStatus = () => {
    apiService.getSystemStatus()
      .then(data => setSystemStatus(data))
      .catch(err => console.error('Failed to update system status:', err));
  };

  useEffect(() => {
    apiService.getDigest()
      .then(data => setDigest(data))
      .catch(err => console.error(err));

    refreshSystemStatus();
  }, []);

  return (
    <div className="min-h-screen flex bg-brand-bg text-brand-text-main relative overflow-hidden">
      {/* Premium Background Ambient Glows */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-brand-accent/5 blur-[150px] rounded-full -z-0" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-brand-accent/5 blur-[150px] rounded-full -z-0" />

      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex-1 lg:ml-[240px] flex flex-col min-h-screen relative z-10">
        <header className="h-20 border-b border-brand-border/10 flex items-center justify-between px-10 bg-brand-bg/80 backdrop-blur-xl sticky top-0 z-50">
          <div className="flex flex-col gap-1.5">
            <span className="text-[9px] font-bold text-brand-text-dim tracking-[0.25em] uppercase">
              Status Sistem
            </span>
            <div className="flex items-center gap-2.5 text-sm font-black text-brand-text-main tracking-wider">
              <span className="w-2 h-2 rounded-full bg-brand-green shadow-[0_0_15px_rgba(16,185,129,0.3)] animate-pulse" />
              SYSTEM ONLINE
            </div>
          </div>

          <div className="flex flex-col items-end gap-1.5 text-right">
            <span className="text-[9px] font-bold text-brand-text-dim tracking-[0.25em] uppercase">
              Terakhir Diperbarui
            </span>
            <div className="text-sm font-black text-brand-text-main tracking-wide">
              {digest?.generated_at ? (
                <>
                  {new Date(digest.generated_at).toLocaleDateString('en-GB', {
                    day: '2-digit', month: 'short', year: 'numeric'
                  })}, {new Date(digest.generated_at).toLocaleTimeString('en-US', {
                    hour: '2-digit', minute: '2-digit', hour12: true
                  })} WIB
                </>
              ) : 'MEMUAT...'}
            </div>
          </div>
        </header>

        <div className="flex-1 p-8 grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-8">
          <div className="min-w-0">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                {activeTab === 'digest' && <DigestView data={digest} />}
                {activeTab === 'search' && <SearchView onSearchSuccess={refreshSystemStatus} />}
                {activeTab === 'qa' && <QAView onActionSuccess={refreshSystemStatus} />}
              </motion.div>
            </AnimatePresence>
          </div>

          <aside className="hidden lg:block pt-12">
            <RightPanel
              stats={digest?.stats}
              systemStatus={systemStatus}
              onSyncSuccess={refreshSystemStatus}
            />
          </aside>
        </div>
      </div>
    </div>
  );
}
