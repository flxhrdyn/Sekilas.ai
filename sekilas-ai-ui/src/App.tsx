/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from "react";
import { 
  BarChart3, 
  Search, 
  MessageSquare, 
  Activity, 
  Database, 
  TrendingUp, 
  ShieldCheck, 
  Cpu, 
  ChevronRight, 
  Globe, 
  Clock, 
  ExternalLink,
  Zap,
  Info,
  Layers,
  Server,
  Terminal,
  AlertCircle,
  HardDrive
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from 'recharts';

// --- Types ---
type View = 'landing' | 'digest' | 'search' | 'agent' | 'pipeline' | 'vector';

// --- Mock Data ---
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

const TOP_PRIORITY_NEWS = {
  title: "Ketidakpastian gencatan senjata antara Amerika Serikat dan Iran memicu lonjakan harga minyak global sebesar 6 persen.",
  date: "20 Apr 2026, 03:32 PM WIB",
  synthesis: [
    { id: 1, text: "Harga minyak melonjak 6% akibat ketidakpastian gencatan senjata AS-Iran." },
    { id: 2, text: "Penyitaan kapal kargo Iran memicu gangguan arus logistik di Selat Hormuz." },
    { id: 3, text: "Risiko eskalasi militer di Selat Hormuz menekan stabilitas pasokan energi global." }
  ]
};

const NEWS_GRID = [
  { id: 1, title: "Penyitaan Kapal Iran oleh Marinir AS", impact: "HIGH", sources: 1, points: ["AS menyita kapal Touska milik Iran terkait pelanggaran sanksi ekonomi internasional.", "Iran mengecam penyitaan sebagai aksi pembajakan dan pelanggaran gencatan senjata regional."], category: "AL JAZEERA ENGLISH", type: "INT'L" },
  { id: 2, title: "Robot Pengganti Manusia di China", impact: "MEDIUM", sources: 1, points: ["Tiongkok mengerahkan 100+ robot humanoid dalam ajang lari setengah maraton di Beijing.", "Robot menunjukkan peningkatan kecepatan dan navigasi otonom melampaui rekor pelari manusia profesional."], category: "CNBC INDONESIA", type: "NASIONAL" },
  { id: 3, title: "Buku Memoar Aurelie Moeremans", impact: "LOW", sources: 1, points: ["Aurelie Moeremans meluncurkan buku memoar 'Broken Strings' yang mengungkap detail sensitif masa mudanya.", "Buku ini merupakan kompilasi dari narasi yang sebelumnya telah dibagikan melalui media sosial."], category: "ANTARA HIBURAN", type: "NASIONAL" },
  { id: 4, title: "Jadwal Rilis Film MCU dan Horor", impact: "LOW", sources: 1, points: ["Marvel Studios menetapkan jadwal rilis proyek MCU krusial sepanjang tahun 2026.", "Serial Wonder Man dan Daredevil: Born Again season 2 dipastikan tayang di Disney+."], category: "ANTARA HIBURAN", type: "NASIONAL" }
];

const SUPPLEMENTAL_UPDATES = [
  {
    category: "POLITIK",
    updates: [
      { id: 1, title: "Anggota DPR Minta Panglima TNI Evaluasi Satgas Habema Usai 12 Warga Sipil Tewas", source: "TEMPO NASIONAL", time: "03:00 PM" },
      { id: 2, title: "Gibran Kunjungi Papua Tengah, Cek Infrastruktur Udara", source: "TEMPO NASIONAL", time: "02:53 PM" }
    ]
  },
  {
    category: "UMUM",
    updates: [
      { id: 3, title: "Pemerintah dan UNICEF Resmikan CPAP 2026-2030: Bekal Indonesia Emas 2045", source: "CNBC INDONESIA", time: "03:25 PM" }
    ]
  },
  {
    category: "OLAHRAGA",
    updates: [
      { id: 4, title: "Mulai Hari dengan Energi Beda? FIFTY RUNNING 2026 Wajib Masuk Wishlist", source: "DETIK SPORT", time: "02:30 PM" },
      { id: 5, title: "Wembanyama makes history as Spurs defeat Blazers in Game 1", source: "AL JAZEERA ENGLISH", time: "01:17 PM" }
    ]
  },
  {
    category: "TEKNOLOGI",
    updates: [
      { id: 6, title: "Harga Flashdisk dan Kartu Memori Meroket Akibat Tren AI", source: "DETIK INET", time: "11:20 AM" },
      { id: 7, title: "OpenAI's existential questions", source: "TECHCRUNCH", time: "04:24 AM" }
    ]
  }
];

const AI_AGENTS = [
  { name: "News Scraper Agent", status: "STANDBY", time: "08:32", active: false },
  { name: "Gatekeeper Filter", status: "STANDBY", time: "08:32", active: false },
  { name: "Discovery Cluster", status: "STANDBY", time: "08:32", active: false },
  { name: "Intelligence Agent", status: "STANDBY", time: "08:32", active: false },
  { name: "Broadcast Notifier", status: "STANDBY", time: "08:32", active: false },
  { name: "Knowledge Embedder", status: "LIVE", time: "Live", active: true },
  { name: "Executive QA Agent", status: "READY", time: "Ready", active: true }
];

// --- Components ---

const MetricCard = ({ title, value, unit, trend, icon: Icon }: any) => (
  <div className="data-card p-5">
    <div className="flex items-center justify-between mb-3 text-white/40">
      <Icon className="w-4 h-4" />
      <span className="text-[10px] font-bold uppercase tracking-widest leading-none text-emerald-500">{trend}</span>
    </div>
    <div className="flex items-baseline gap-1">
      <span className="mono-stat text-3xl font-bold">{value}</span>
      <span className="text-sm font-medium text-white/30">{unit}</span>
    </div>
    <p className="text-[10px] text-white/20 uppercase tracking-widest mt-2">{title}</p>
  </div>
);

const PipelineStep = ({ name, status, metrics, delay = 0 }: any) => (
  <motion.div 
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay }}
    className="relative"
  >
    <div className="flex items-center gap-6 p-6 bg-white/5 border border-white/5 rounded-2xl hover:border-brand-blue/30 transition-colors group">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${status === 'Active' ? 'bg-brand-blue/20 text-brand-blue' : 'bg-white/5 text-white/20'}`}>
        <Layers className="w-6 h-6" />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-bold text-lg group-hover:text-brand-blue transition-colors">{name}</h3>
          <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-tighter ${status === 'Active' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-white/5 text-white/30'}`}>{status}</span>
        </div>
        <div className="flex gap-6 mt-3 font-mono text-[10px]">
          {Object.entries(metrics).map(([key, val]: any) => (
            <div key={key} className="flex flex-col">
              <span className="text-white/20 uppercase tracking-widest">{key}</span>
              <span className="text-white/60 font-bold">{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
    {/* Connector Particle */}
    <div className="absolute -bottom-8 left-12 w-0.5 h-8 bg-white/5 last:hidden">
      <motion.div 
        animate={{ top: [0, 32], opacity: [0, 1, 0] }}
        transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
        className="absolute w-1.5 h-1.5 bg-brand-blue rounded-full -left-[2.5px] blur-[1px]"
      />
    </div>
  </motion.div>
);

const SidebarItem = ({ icon: Icon, label, active, onClick }: { icon: any, label: string, active: boolean, onClick: () => void }) => (
  <button 
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
      active 
        ? "bg-brand-blue/10 text-brand-blue" 
        : "text-white/50 hover:bg-white/5 hover:text-white"
    }`}
  >
    <Icon className={`w-5 h-5 transition-transform duration-200 ${active ? "scale-110" : "group-hover:scale-110"}`} />
    <span className="text-sm font-medium">{label}</span>
    {active && <motion.div layoutId="active-pill" className="ml-auto w-1.5 h-6 bg-brand-blue rounded-full" />}
  </button>
);

const ImpactBadge = ({ level }: { level: string }) => {
  const colors = {
    HIGH: "bg-red-500/10 text-red-500 border-red-500/20",
    MEDIUM: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    LOW: "bg-blue-500/10 text-blue-500 border-blue-500/20"
  };
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${colors[level as keyof typeof colors]}`}>
      {level}
    </span>
  );
};

const Header = () => (
  <header className="flex items-center justify-between py-6 px-8 border-b border-white/5 backdrop-blur-sm sticky top-0 z-10 bg-surface-dark/80">
    <div className="flex flex-col gap-1">
      <span className="text-[10px] text-white/40 uppercase tracking-widest font-mono">Status Sistem</span>
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
        <span className="text-sm font-medium">SYSTEM ONLINE</span>
      </div>
    </div>
    <div className="flex items-center gap-6">
      <div className="flex flex-col items-end">
        <span className="text-[10px] text-white/40 uppercase tracking-widest font-mono">Terakhir Diperbarui</span>
        <span className="text-sm font-medium">20 Apr 2026, 03:32 PM WIB</span>
      </div>
    </div>
  </header>
);

interface NewsCardProps {
  news: typeof NEWS_GRID[0];
}

const NewsCard: React.FC<NewsCardProps> = ({ news }) => (
  <motion.div 
    initial={{ opacity: 0, y: 10 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    whileHover={{ y: -4 }}
    className="data-card flex flex-col gap-4 group h-full glow-on-hover transition-all"
  >
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <ImpactBadge level={news.impact} />
        <span className="text-[10px] bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-1.5 py-0.5 rounded font-mono font-bold">SKOR: 0.88</span>
      </div>
      <span className="text-[10px] text-white/40 font-mono uppercase">{news.sources} Sourced Report</span>
    </div>
    <h3 className="text-xl font-bold group-hover:text-brand-blue transition-colors leading-tight">
      {news.title}
    </h3>
    <ul className="flex flex-col gap-3">
      {news.points.map((point, idx) => (
        <li key={idx} className="flex gap-2 text-sm text-white/60 leading-relaxed">
          <div className="w-1 h-1 rounded-full bg-brand-blue/40 mt-2 shrink-0" />
          {point}
        </li>
      ))}
    </ul>
    <div className="mt-auto pt-4 flex items-center justify-between border-t border-white/5">
      <div className="flex items-center gap-2">
        <span className="text-[10px] bg-brand-blue/10 text-brand-blue px-2 py-0.5 rounded font-bold">{news.category}</span>
        <span className="text-[10px] text-white/30 font-mono italic">{news.type}</span>
      </div>
      <ExternalLink className="w-3 h-3 text-white/20 group-hover:text-white transition-colors" />
    </div>
  </motion.div>
);

const ChatMessage = ({ role, content, thoughts }: { role: 'user' | 'assistant', content: string, thoughts?: string[] }) => (
  <motion.div 
    initial={{ opacity: 0, x: role === 'user' ? 20 : -20 }}
    animate={{ opacity: 1, x: 0 }}
    className={`flex flex-col gap-3 ${role === 'user' ? 'items-end' : 'items-start'}`}
  >
    <div className="flex items-center gap-2">
      <div className={`w-6 h-6 rounded-lg flex items-center justify-center ${role === 'user' ? 'bg-white/10' : 'bg-brand-blue'}`}>
        {role === 'user' ? <Info className="w-3 h-3" /> : <Zap className="w-3 h-3 text-white" />}
      </div>
      <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">{role === 'user' ? 'Anda' : 'Sekilas Agent'}</span>
    </div>
    
    <div className={`max-w-[80%] p-4 rounded-2xl ${role === 'user' ? 'bg-brand-blue/20 text-white rounded-tr-none' : 'bg-surface-muted text-white/90 rounded-tl-none border border-white/5'}`}>
      <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
    </div>

    {thoughts && role === 'assistant' && (
      <div className="flex flex-col gap-2 ml-8 border-l border-white/10 pl-4 py-2">
        <div className="flex items-center gap-2 text-[10px] text-white/30 uppercase tracking-widest font-bold">
          <Activity className="w-3 h-3" />
          Reasoning Process
        </div>
        {thoughts.map((thought, i) => (
          <div key={i} className="flex gap-2 text-[11px] text-white/40 italic">
            <span className="text-brand-blue opacity-50">›</span>
            {thought}
          </div>
        ))}
      </div>
    )}
  </motion.div>
);const LandingPage = ({ onEnter }: { onEnter: () => void }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationProgress, setSimulationProgress] = useState(0);

  // Auto-simulation step trigger
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isSimulating) {
      interval = setInterval(() => {
        setSimulationProgress((prev) => {
          if (prev >= 100) {
            setIsSimulating(false);
            return 100;
          }
          const nextVal = prev + 1.5;
          // Sync activeStep based on progress ranges
          if (nextVal < 25) setActiveStep(0);
          else if (nextVal < 50) setActiveStep(1);
          else if (nextVal < 75) setActiveStep(2);
          else setActiveStep(3);
          return nextVal;
        });
      }, 60);
    }
    return () => clearInterval(interval);
  }, [isSimulating]);

  const startSimulation = () => {
    setSimulationProgress(0);
    setActiveStep(0);
    setIsSimulating(true);
  };

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const pipelineSteps = [
    {
      icon: Globe,
      name: "Smart Scraper",
      tagline: "Global Intel Extraction",
      description: "Melakukan penambangan data otonom dari ratusan outlet berita bereputasi internasional secara paralel.",
      telemetry: "Scraping rate: 420 sources/min • Raw ingest latency: 1.2s • TLS verification: 100%",
      logs: [
        "[03:32:01] SCRAPER_INIT: New news bundle detected",
        "[03:32:02] SCRAPER_INGEST: 12 raw source feeds incoming...",
        "[03:32:03] SCRAPER_PARSED: Standardized metadata structures compiled"
      ]
    },
    {
      icon: ShieldCheck,
      name: "Gatekeeper Filter",
      tagline: "Bias & Rumor Elimination",
      description: "Menyaring duplikasi, rumor spekulatif, spam iklan, dan bias berita menggunakan evaluasi kesamaan semantik.",
      telemetry: "Deduplication match: 99.8% • Rumor score: < 0.12 • Noise reduction: 74%",
      logs: [
        "[03:32:04] GATEKEEPER_ACTIVE: Analyzing similarity matrix",
        "[03:32:05] GATEKEEPER_FILTER: 3 speculative blog resources dropped",
        "[03:32:06] GATEKEEPER_VERIFIED: Cross-verified facts verified across remaining articles"
      ]
    },
    {
      icon: Database,
      name: "Embedding Engine",
      tagline: "1.4M Dimension Mapping",
      description: "Mengonversi konten berita ke dalam vektor dimensi tinggi dan menyimpannya di basis data vektor untuk pencarian RAG terarah.",
      telemetry: "Vector schema: 1536-dim • Cosine threshold: > 0.82 • Vector write: 1.4ms",
      logs: [
        "[03:32:07] EMBEDDER_ACTIVE: Invoking semantic model for #TX-192",
        "[03:32:08] EMBEDDER_VECTOR: Dense vector embeddings successfully computed",
        "[03:32:09] EMBEDDER_STORAGE: Storage indexing finalized in news_main cluster"
      ]
    },
    {
      icon: Cpu,
      name: "Executive Synthesis",
      tagline: "RAG Multi-Agent Consensus",
      description: "Memicu perdebatan multi-agen AI untuk menyimpulkan inti berita secara objektif, menyusun sintesis analitik, dan menerbitkan laporan.",
      telemetry: "Reasoning path: COT-Agent • Consensus score: 94% • Compilation: 3.8s",
      logs: [
        "[03:32:10] AGENT_SYNTHESIS: Multi-agent debate initiated for core summary",
        "[03:32:11] AGENT_CONVERGENCE: Reached consensus with 94% reliability score",
        "[03:32:12] AGENT_PUBLISH: Dashboard refreshed and dispatching notifications"
      ]
    }
  ];

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-[#050505] text-white overflow-hidden relative"
    >
      {/* Background Glows */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-brand-blue/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-brand-blue/5 blur-[120px] rounded-full pointer-events-none" />

      {/* Navigation */}
      <nav className="relative z-20 flex items-center justify-between px-10 py-8 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-brand-blue rounded-xl flex items-center justify-center shadow-lg shadow-brand-blue/20">
            <Zap className="w-6 h-6 text-white fill-current" />
          </div>
          <span className="text-2xl font-bold tracking-tight">sekilas.ai</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-white/50">
          <a 
            href="#features" 
            onClick={(e) => { e.preventDefault(); scrollToSection('features'); }}
            className="hover:text-white transition-colors"
          >
            Features
          </a>
          <a 
            href="#pipeline" 
            onClick={(e) => { e.preventDefault(); scrollToSection('pipeline'); }}
            className="hover:text-white transition-colors text-brand-blue font-bold"
          >
            Architecture
          </a>
          <button 
            onClick={onEnter}
            className="bg-white/5 border border-white/10 px-6 py-2.5 rounded-xl hover:bg-white/10 transition-all"
          >
            Developer Console
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 pt-20 pb-32 px-6 max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <span className="glass-pill text-brand-blue mb-6 px-4 py-1.5 inline-flex items-center gap-2">
            <Activity className="w-3 h-3" />
            Next-Gen News Intelligence
          </span>
          <h1 className="text-6xl md:text-8xl font-bold tracking-tighter mb-8 leading-[0.9]">
            The Intelligence <br />
            <span className="text-brand-blue italic">Engine</span> for News.
          </h1>
          <p className="text-lg md:text-xl text-white/40 max-w-2xl mx-auto mb-12 font-medium leading-relaxed">
            Sintesis berita global secara real-time dengan transparansi penuh. 
            Dibangun di atas arsitektur Agentic-RAG untuk akurasi tanpa kompromi.
          </p>
          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <button 
              onClick={onEnter}
              className="w-full md:w-auto bg-brand-blue text-white px-10 py-5 rounded-2xl font-bold text-lg shadow-2xl shadow-brand-blue/30 hover:scale-105 transition-all flex items-center justify-center gap-3"
            >
              Masuk ke Terminal <ChevronRight className="w-5 h-5" />
            </button>
            <button 
              onClick={() => scrollToSection('pipeline')}
              className="w-full md:w-auto bg-white/5 border border-white/10 text-white px-10 py-5 rounded-2xl font-bold text-lg hover:bg-white/10 hover:border-white/20 transition-all flex items-center justify-center gap-2"
            >
              Pelajari Arsitektur <Activity className="w-4 h-4 text-brand-blue" />
            </button>
          </div>
        </motion.div>
      </section>

      {/* Features Bento Grid */}
      <section id="features" className="px-6 max-w-7xl mx-auto pb-24 border-b border-white/5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 data-card p-12 bg-surface-muted/30 flex flex-col justify-end min-h-[350px]">
            <div className="w-14 h-14 bg-brand-blue/20 rounded-2xl flex items-center justify-center text-brand-blue mb-8">
              <Layers className="w-8 h-8" />
            </div>
            <h3 className="text-3xl font-bold mb-4">Agentic-RAG Architecture</h3>
            <p className="text-white/40 leading-relaxed max-w-lg text-lg">
              Bukan sekadar pencarian. Agen AI kami melakukan pengambilan, penyaringan, 
              dan validasi silang pada ribuan sumber untuk memberikan sintesis yang jujur.
            </p>
          </div>
          <div className="data-card p-12 bg-white/5 overflow-hidden flex flex-col group justify-end">
            <div className="flex-1">
              <Activity className="w-10 h-10 text-brand-blue mb-6 group-hover:scale-110 transition-transform" />
              <h3 className="text-2xl font-bold mb-4">Real-time Pipeline</h3>
              <p className="text-white/40 leading-relaxed">
                Pantau setiap detik proses intelijen melalui Pipeline Monitor yang transparan.
              </p>
            </div>
            <div className="mt-8 flex gap-2">
              <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                <motion.div 
                  animate={{ x: ["-100%", "100%"] }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  className="h-full w-1/2 bg-brand-blue"
                />
              </div>
            </div>
          </div>
          <div className="data-card p-12 bg-white/5">
            <Database className="w-10 h-10 text-brand-blue mb-6" />
            <h3 className="text-2xl font-bold mb-4">Semantic Context</h3>
            <p className="text-white/40 leading-relaxed">
              Dipetakan ke dalam 1.4M dimensi vektor untuk pemahaman konteks yang tak tertandingi.
            </p>
          </div>
          <div className="md:col-span-2 data-card p-12 bg-brand-blue flex flex-col md:flex-row items-center gap-10">
            <div className="flex-1">
              <h3 className="text-3xl font-bold mb-4 text-white">Siap untuk Intelijen Baru?</h3>
              <p className="text-white/80 leading-relaxed text-lg mb-8">
                Mulai membedah berita hari ini dengan Agentic-RAG berkekuatan penuh.
              </p>
              <button 
                onClick={onEnter}
                className="bg-white text-brand-blue px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all shadow-md"
              >
                Coba Sekarang
              </button>
            </div>
            <div className="w-48 h-48 bg-white/10 rounded-full flex items-center justify-center shrink-0">
              <Zap className="w-24 h-24 text-white fill-current" />
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Architecture Section */}
      <section id="pipeline" className="px-6 py-32 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <span className="glass-pill text-brand-blue mb-4 px-4 py-1.5 inline-flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5" />
            Live Schema Explorer
          </span>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">Arsitektur Agentic-RAG Kami</h2>
          <p className="text-white/40 max-w-2xl mx-auto">
            Klik pada setiap node atau jalankan simulator taktis di bawah untuk memahami bagaimana berita disaring, dipetakan secara matematis, hingga akhirnya disatukan.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-stretch">
          {/* Left Column: Vertical Interactive Nodes */}
          <div className="lg:col-span-5 flex flex-col gap-4 relative">
            {/* Visual connecting pipe */}
            <div className="absolute left-[47px] top-[48px] bottom-[48px] w-0.5 bg-gradient-to-b from-brand-blue via-brand-blue/30 to-brand-blue/10 pointer-events-none hidden md:block">
              {isSimulating && (
                <motion.div 
                  initial={{ top: "0%" }}
                  animate={{ top: `${simulationProgress}%` }}
                  className="absolute left-[-2px] right-[-2px] h-20 bg-gradient-to-b from-transparent via-brand-blue to-transparent shadow-[0_0_15px_rgba(59,130,246,0.8)]"
                />
              )}
            </div>

            {pipelineSteps.map((step, index) => {
              const IconComponent = step.icon;
              const isActive = activeStep === index;
              return (
                <button
                  key={step.name}
                  onClick={() => {
                    if (!isSimulating) {
                      setActiveStep(index);
                    }
                  }}
                  className={`text-left p-6 rounded-2xl border transition-all flex gap-5 items-start relative z-10 ${
                    isActive 
                      ? 'bg-surface-muted/60 border-brand-blue/50 shadow-[0_0_20px_rgba(59,130,246,0.1)]' 
                      : 'bg-white/[0.02] border-white/5 hover:bg-white/[0.04] hover:border-white/10'
                  }`}
                >
                  <div className={`p-3 rounded-xl flex items-center justify-center shrink-0 transition-all ${
                    isActive ? 'bg-brand-blue text-white' : 'bg-white/5 text-white/40'
                  }`}>
                    <IconComponent className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-brand-blue tracking-widest uppercase block mb-1">STAGE {index + 1} • {step.tagline}</span>
                    <h4 className="text-xl font-bold mb-1">{step.name}</h4>
                    <p className="text-xs text-white/50 line-clamp-2 md:line-clamp-none">{step.description}</p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right Column: Tactical Console / Logs Preview */}
          <div className="lg:col-span-7 flex flex-col">
            <div className="data-card bg-[#0a0a0a] border border-white/5 p-8 flex-1 flex flex-col justify-between relative overflow-hidden">
              {/* Telemetry screen background overlay */}
              <div className="absolute inset-0 bg-radial-gradient from-brand-blue/5 to-transparent pointer-events-none" />
              
              <div>
                <div className="flex items-center justify-between border-b border-white/5 pb-5 mb-6">
                  <div className="flex items-center gap-3">
                    <Terminal className="w-5 h-5 text-brand-blue" />
                    <div>
                      <span className="text-[10px] font-mono tracking-widest text-white/30 block">SYSTEM CONSOLE</span>
                      <h3 className="font-mono text-xs font-bold text-white/80 uppercase">Telemetry: {pipelineSteps[activeStep].name}</h3>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[9px] font-mono text-emerald-500 uppercase font-bold">NODE ONLINE</span>
                  </div>
                </div>

                {/* Sub logs panel */}
                <div className="space-y-4 mb-8">
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                    <span className="text-[9px] font-mono text-white/40 uppercase block mb-2">Metrics Data</span>
                    <p className="font-mono text-xs text-brand-blue font-semibold">{pipelineSteps[activeStep].telemetry}</p>
                  </div>

                  <div className="font-mono text-xs space-y-2 bg-black/40 rounded-xl p-5 border border-white/5 min-h-[120px]">
                    <span className="text-[9px] text-white/20 uppercase block border-b border-white/5 pb-2 mb-2">Simulation Logs</span>
                    {pipelineSteps[activeStep].logs.map((log, i) => (
                      <p key={i} className="text-emerald-500/80 leading-relaxed">
                        <span className="text-white/20 mr-2">›</span>
                        {log}
                      </p>
                    ))}
                    {isSimulating && (
                      <p className="text-brand-blue animate-pulse italic text-[11px] mt-2">Simulating high-load processes... {Math.round(simulationProgress)}%</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Simulation Activator Row */}
              <div className="border-t border-white/5 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-left w-full sm:w-auto">
                  <span className="text-[9px] font-mono text-white/30 block uppercase tracking-wider mb-1">Simulation Control</span>
                  <p className="text-xs text-white/50">Simulasikan aliran paket berita dari awal hingga sintesis akhir.</p>
                </div>
                <button
                  onClick={startSimulation}
                  disabled={isSimulating}
                  className={`w-full sm:w-auto px-6 py-3 rounded-xl font-bold font-mono text-xs transition-all flex items-center justify-center gap-2 ${
                    isSimulating 
                      ? 'bg-white/5 text-white/20 border border-white/5 cursor-not-allowed' 
                      : 'bg-brand-blue hover:bg-brand-blue/80 text-white shadow-lg shadow-brand-blue/10 active:scale-95'
                  }`}
                >
                  <Activity className={`w-4 h-4 ${isSimulating ? 'animate-spin' : ''}`} />
                  {isSimulating ? 'SIMULATION IN PROGRESS...' : 'RUN PIPELINE SIMULATOR'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-20 px-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-10">
          <div className="flex items-center gap-3 opacity-50">
            <Zap className="w-5 h-5" />
            <span className="font-bold tracking-tight">sekilas.ai</span>
          </div>
          <p className="text-white/20 text-sm font-mono">
            © 2026 SEKILAS INTELLIGENCE ENGINE. ALL RIGHTS RESERVED.
          </p>
          <div className="flex gap-8 text-white/30 text-sm">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terminal Terms</a>
            <a href="#" className="hover:text-white transition-colors">API Docs</a>
          </div>
        </div>
      </footer>
    </motion.div>
  );
};

export default function App() {
  const [activeView, setActiveView] = useState<View>('landing');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  if (activeView === 'landing') {
    return (
      <AnimatePresence mode="wait">
        <LandingPage onEnter={() => setActiveView('digest')} />
      </AnimatePresence>
    );
  }

  return (
    <div className="flex min-h-screen font-sans selection:bg-brand-blue selection:text-white">
      {/* Sidebar */}
      <aside className="w-72 border-r border-white/5 flex flex-col p-6 gap-8 shrink-0 bg-[#050505]">
        <div 
          onClick={() => setActiveView('landing')}
          className="flex items-center gap-3 px-2 cursor-pointer hover:opacity-80 transition-opacity group"
        >
          <div className="w-9 h-9 bg-brand-blue rounded-xl flex items-center justify-center shadow-lg shadow-brand-blue/20 group-hover:scale-110 transition-transform">
            <Zap className="w-5 h-5 text-white fill-current" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white m-0">sekilas.ai</h1>
            <p className="text-[9px] text-white/40 uppercase tracking-widest font-mono">Intelligence Engine</p>
          </div>
        </div>

        <nav className="flex flex-col gap-2">
          <SidebarItem icon={Globe} label="Beranda" active={false} onClick={() => setActiveView('landing')} />
          <div className="h-px bg-white/5 my-2 mx-4" />
          <SidebarItem icon={BarChart3} label="Digest Harian" active={activeView === 'digest'} onClick={() => setActiveView('digest')} />
          <SidebarItem icon={Search} label="Cari Berita" active={activeView === 'search'} onClick={() => setActiveView('search')} />
          <SidebarItem icon={MessageSquare} label="Tanya AI Agent" active={activeView === 'agent'} onClick={() => setActiveView('agent')} />
        </nav>

        <div className="mt-6 flex flex-col gap-2">
          <h4 className="px-4 text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] py-2">Sistem</h4>
          <SidebarItem icon={Activity} label="Pipeline Monitor" active={activeView === 'pipeline'} onClick={() => setActiveView('pipeline')} />
          <SidebarItem icon={Database} label="Vector DB Health" active={activeView === 'vector'} onClick={() => setActiveView('vector')} />
        </div>

        <div className="mt-auto p-4 bg-white/5 rounded-2xl border border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <Cpu className="w-4 h-4 text-brand-blue" />
            <span className="text-xs font-semibold">Gemini Nano 3.1</span>
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

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <Header />
        
        <div className="flex-1 overflow-y-auto bg-surface-dark custom-scrollbar">
          <AnimatePresence mode="wait">
            {activeView === 'digest' ? (
              <motion.div 
                key="digest"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-8 max-w-7xl mx-auto flex gap-8"
              >
                {/* Center Content */}
                <div className="flex-1 flex flex-col gap-10">
                  {/* Hero Headline */}
                  <section className="relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-brand-blue/20 to-transparent blur-3xl opacity-0 group-hover:opacity-50 transition-opacity duration-700" />
                    <div className="relative p-10 bg-surface-muted border border-white/5 rounded-[2rem] overflow-hidden">
                      <div className="glass-pill absolute top-6 left-1/2 -translate-x-1/2 flex items-center gap-2">
                        <Globe className="w-3 h-3 text-brand-blue" />
                        <span className="tracking-widest uppercase text-[9px]">Today's Global Headline</span>
                      </div>
                      <h2 className="text-4xl md:text-5xl font-bold text-center mt-12 mb-8 leading-[1.1] tracking-tight">
                        {TOP_PRIORITY_NEWS.title}
                      </h2>
                    </div>
                  </section>

                  {/* Curated Feed */}
                  <section>
                    <div className="flex items-center justify-between mb-8">
                      <div className="flex items-center gap-3">
                        <TrendingUp className="w-6 h-6 text-brand-blue" />
                        <h2 className="text-2xl font-bold tracking-tight italic">TOP CURATED INTELLIGENCE</h2>
                      </div>
                      <div className="flex gap-2">
                        <span className="glass-pill text-brand-blue">ELITE TOP 5</span>
                      </div>
                    </div>

                    <div className="data-card bg-surface-muted/30 p-10 mb-8 border-white/5 relative overflow-hidden">
                      <div className="flex flex-wrap items-center gap-4 mb-8">
                        <span className="bg-brand-blue text-white px-3 py-1 rounded text-[10px] font-bold uppercase tracking-widest shadow-lg shadow-brand-blue/30">Top Priority</span>
                        <span className="bg-white/5 text-white/50 px-3 py-1 rounded text-[10px] font-bold uppercase tracking-widest border border-white/5">1 Sourced Reports</span>
                        <span className="bg-red-500/10 text-red-500 px-3 py-1 rounded text-[10px] font-bold uppercase tracking-widest border border-red-500/10">High Impact</span>
                        <div className="ml-auto">
                          <span className="flex items-center gap-2 bg-white/5 px-3 py-1 rounded-lg border border-white/10">
                            <Zap className="w-3 h-3 text-brand-blue" />
                            <span className="text-[9px] font-bold uppercase text-white/30 tracking-widest">AI Synthesized</span>
                          </span>
                        </div>
                      </div>

                      <h3 className="text-4xl font-bold mb-10 tracking-tight leading-tight">
                        Lonjakan Harga Minyak Global
                      </h3>

                      <div className="p-8 bg-white/[0.02] border border-white/5 rounded-3xl relative">
                        <div className="absolute top-6 right-8 flex items-center gap-4">
                          <div className="flex flex-col items-end">
                            <span className="text-[9px] font-bold text-white/30 uppercase tracking-widest mb-1">Reliability Index</span>
                            <div className="w-24 h-1 bg-white/5 rounded-full overflow-hidden">
                              <motion.div initial={{ width: 0 }} animate={{ width: "94%" }} className="h-full bg-brand-blue" />
                            </div>
                          </div>
                          <span className="text-xl font-mono font-bold text-brand-blue">94%</span>
                        </div>
                        <div className="flex items-center gap-3 mb-8">
                          <Activity className="w-5 h-5 text-brand-blue opacity-50" />
                          <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-brand-blue/80">Analyst Synthesis</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-x-12 gap-y-10">
                          {TOP_PRIORITY_NEWS.synthesis.map((item) => (
                            <div key={item.id} className="flex gap-5 group">
                              <span className="flex items-center justify-center w-10 h-10 rounded-xl bg-brand-blue/10 text-brand-blue font-mono text-xl font-bold shrink-0">{item.id}</span>
                              <p className="text-base leading-relaxed text-white/70 group-hover:text-white transition-colors">{item.text}</p>
                            </div>
                          ))}
                        </div>

                        {/* Source Ribbon */}
                        <div className="mt-12 pt-6 border-t border-white/5 flex items-center gap-4">
                          <span className="text-[10px] font-bold text-white/20 uppercase tracking-widest uppercase">Verified Sources:</span>
                          <div className="flex gap-4 overflow-hidden overflow-x-auto custom-scrollbar pb-1">
                            {['Al Jazeera', 'BBC News', 'Reuters', 'CNBC', 'CNN', 'Tempo', 'Antara'].map((source) => (
                              <span key={source} className="text-[10px] font-mono text-white/40 whitespace-nowrap px-2 py-1 rounded bg-white/5 border border-white/5 hover:border-brand-blue/30 transition-colors cursor-default">
                                {source}.int
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {NEWS_GRID.map((news) => (
                        <NewsCard key={news.id} news={news} />
                      ))}
                    </div>
                  </section>

                  {/* Supplemental Updates */}
                  <section className="mt-12 pt-12 border-t border-white/5">
                    <div className="flex items-center gap-3 mb-10">
                      <Layers className="w-6 h-6 text-brand-blue" />
                      <h2 className="text-2xl font-bold tracking-tight italic uppercase">Supplemental Updates</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                      {SUPPLEMENTAL_UPDATES.map((group) => (
                        <div key={group.category} className="flex flex-col gap-6">
                          <div className="flex items-center justify-between border-b border-white/5 pb-2">
                            <h4 className="text-xs font-bold text-brand-blue tracking-[0.2em]">{group.category}</h4>
                            <span className="text-[9px] text-white/20 font-mono italic">{group.updates.length} UPDATES</span>
                          </div>
                          <div className="flex flex-col gap-8">
                            {group.updates.map((update) => (
                              <div key={update.id} className="flex flex-col gap-2 group cursor-pointer">
                                <h5 className="text-base font-bold leading-snug group-hover:text-brand-blue transition-colors">
                                  {update.title}
                                </h5>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] font-bold text-white/30 uppercase tracking-widest">{update.source}</span>
                                  <span className="w-1 h-1 rounded-full bg-white/10" />
                                  <div className="flex items-center gap-1 text-[10px] text-white/30 font-mono">
                                    <Clock className="w-3 h-3" />
                                    {update.time}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>

                {/* Right Panel */}
                <div className="w-80 flex flex-col gap-6 shrink-0">
                  <div className="data-card">
                    <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] mb-4">Artikel Diproses (24J)</h4>
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="mono-stat text-5xl font-bold tracking-tighter">27</span>
                    </div>
                    <span className="text-xs font-bold text-emerald-500">+80% vs Kemarin</span>
                  </div>

                  <div className="data-card">
                    <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] mb-6">Statistik Terakhir</h4>
                    <div className="space-y-4">
                      {[
                        { label: "Raw Ingested", value: 18, color: "bg-blue-500" },
                        { label: "Cleaned", value: 15, color: "bg-emerald-500" },
                        { label: "Deduplicated", value: 0, color: "bg-red-500" }
                      ].map((stat) => (
                        <div key={stat.label} className="flex items-center justify-between group">
                          <div className="flex items-center gap-2">
                            <div className={`w-1.5 h-1.5 rounded-full ${stat.color}`} />
                            <span className="text-sm text-white/60 group-hover:text-white transition-colors">{stat.label}</span>
                          </div>
                          <span className="mono-stat text-sm font-semibold">{stat.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="data-card">
                    <div className="flex items-center justify-between mb-6">
                      <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">AI Agents Pulse</h4>
                      <span className="text-[8px] px-1.5 py-0.5 rounded border border-emerald-500/30 text-emerald-500 font-mono">ORCHESTRATED</span>
                    </div>
                    <div className="space-y-5">
                      {AI_AGENTS.map((agent) => (
                        <div key={agent.name} className="flex items-center justify-between group">
                          <div className="flex items-center gap-3">
                            <div className={`w-1.5 h-1.5 rounded-full ${agent.active ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-white/20"}`} />
                            <div className="flex flex-col">
                              <span className="text-xs font-bold group-hover:text-brand-blue transition-colors">{agent.name}</span>
                              <span className="text-[9px] text-white/30 tracking-widest">{agent.status}</span>
                            </div>
                          </div>
                          <div className="flex flex-col items-end">
                            <span className="text-[9px] font-mono font-bold text-white/40">{agent.time}</span>
                            <span className="text-[8px] text-white/20 uppercase tracking-tighter">Activity</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : activeView === 'search' ? (
              <motion.div 
                key="search"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="p-8 max-w-5xl mx-auto flex flex-col gap-8"
              >
                <div className="flex flex-col gap-2">
                  <h2 className="text-3xl font-bold">Cari Berita</h2>
                  <p className="text-white/40 text-sm">Gunakan pencarian semantik untuk menemukan berita berdasarkan makna mendalam.</p>
                </div>

                <div className="relative">
                  <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                  <input 
                    type="text" 
                    placeholder="Apa yang ingin Anda telusuri hari ini?" 
                    className="w-full bg-surface-muted border border-white/10 rounded-2xl py-6 pl-16 pr-8 text-xl focus:outline-none focus:ring-2 focus:ring-brand-blue/30 focus:border-brand-blue/50 transition-all placeholder:text-white/10"
                  />
                  <div className="absolute right-4 top-1/2 -translate-y-1/2">
                    <button className="bg-brand-blue hover:bg-brand-blue/90 text-white px-6 py-2 rounded-xl text-sm font-bold shadow-lg shadow-brand-blue/20 transition-all flex items-center gap-2">
                      Cari <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="data-card bg-surface-muted/20 border-dashed">
                  <div className="flex items-center gap-3 text-white/40 mb-2">
                    <Info className="w-4 h-4" />
                    <span className="text-xs">Hasil pencarian diurutkan berdasarkan relevansi kontekstual.</span>
                  </div>
                </div>
              </motion.div>
            ) : activeView === 'pipeline' ? (
              <motion.div 
                key="pipeline"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-8 max-w-5xl mx-auto flex flex-col gap-10"
              >
                <div className="flex items-end justify-between">
                  <div className="flex flex-col gap-2">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                      <Activity className="w-8 h-8 text-brand-blue" />
                      Pipeline Monitor
                    </h2>
                    <p className="text-white/40 text-sm">Pemantauan real-time alur kerja Agentic-RAG dari ingestion hingga sintesis.</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end">
                      <span className="text-[10px] text-white/30 uppercase tracking-widest font-bold">Total Throughput</span>
                      <span className="mono-stat text-xl font-bold">1.2k <span className="text-xs text-white/30">req/min</span></span>
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
                    />
                  </div>

                  {/* Right Column: Mini Stats & Logs */}
                  <div className="flex flex-col gap-6">
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
                          <Terminal className="w-3 h-3" /> Live Logs
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
                        <p className="text-white/10 italic">Waiting for next event...</p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : activeView === 'vector' ? (
              <motion.div 
                key="vector"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-8 max-w-6xl mx-auto flex flex-col gap-8"
              >
                <div className="flex items-end justify-between">
                  <div className="flex flex-col gap-2">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                      <Database className="w-8 h-8 text-brand-blue" />
                      Vector DB Health
                    </h2>
                    <p className="text-white/40 text-sm">Status infrastruktur Qdrant & Knowledge Base Retrieval.</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <MetricCard title="Total Vectors" value="1.4M" unit="dims: 1536" trend="+12k/day" icon={Server} />
                  <MetricCard title="Search Latency" value="42" unit="ms (p99)" trend="Stable" icon={Zap} />
                  <MetricCard title="Index Refresh" value="2.4" unit="s" trend="-0.2s" icon={Activity} />
                  <MetricCard title="Disk Usage" value="48" unit="GB / 128" trend="Optimize soon" icon={HardDrive} />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="data-card p-0 overflow-hidden flex flex-col">
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
                              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                              itemStyle={{ color: '#fff', fontSize: '12px' }}
                            />
                            <Area type="monotone" dataKey="value" stroke="#3b82f6" fillOpacity={1} fill="url(#colorValue)" strokeWidth={2} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  <div className="data-card flex flex-col">
                    <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] mb-6">Collection Metadata</h4>
                    <div className="space-y-4">
                      {STORAGE_DATA.map((col) => (
                        <div key={col.name} className="p-4 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-all group">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-bold group-hover:text-brand-blue transition-colors underline decoration-brand-blue/20">{col.name}</span>
                            <span className="text-xs font-mono text-emerald-500">HEALTHY</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex flex-col">
                              <span className="text-[9px] text-white/20 uppercase tracking-widest">Fragments</span>
                              <span className="text-xs font-mono">{col.count.toLocaleString()}</span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-[9px] text-white/20 uppercase tracking-widest">Storage</span>
                              <span className="text-xs font-mono">{col.size}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : activeView === 'agent' ? (
              <motion.div 
                key="agent"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col"
              >
                <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
                  <ChatMessage 
                    role="assistant" 
                    content="Halo! Saya asisten cerdas Sekilas.ai. Saya baru saja mensintesis berita hari ini menggunakan Agentic-RAG. Ada topik spesifik yang ingin Anda bedah lebih dalam?"
                    thoughts={[
                      "Retrieving global energy news from Vector DB",
                      "Filtering irrelevant sources using Gatekeeper Agent",
                      "Synthesizing oil price surge context",
                      "Validating sources across multiple international outlets"
                    ]}
                  />
                  <ChatMessage 
                    role="user" 
                    content="Jelaskan dampak kenaikan harga minyak ini bagi ekonomi domestik Indonesia." 
                  />
                  <ChatMessage 
                    role="assistant" 
                    content="Berdasarkan analisis RAG saya dari 12 sumber valid:\n\n1. Kenaikan 6% harga minyak dunia dapat memberikan tekanan pada subsidi BBM nasional.\n2. BI diprediksi akan memantau ketat inflasi core akibat biaya logistik yang mungkin naik.\n3. Namun, sebagai eksportir komoditas tertentu, terdapat potensi offset dari penerimaan negara bukan pajak (PNBP)."
                    thoughts={[
                      "Accessing Knowledge Embedder for ID context",
                      "Retrieving financial reports from CNBC & Detik",
                      "Applying cross-reference check on subsidy data"
                    ]}
                  />
                </div>
                
                <div className="p-6 bg-surface-muted/50 border-t border-white/5">
                  <div className="max-w-4xl mx-auto relative">
                    <input 
                      type="text" 
                      placeholder="Tanyakan analisis lebih lanjut..." 
                      className="w-full bg-surface-dark border border-white/10 rounded-2xl py-4 pl-6 pr-16 focus:outline-none focus:ring-2 focus:ring-brand-blue/30 transition-all"
                    />
                    <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-brand-blue rounded-xl text-white shadow-lg shadow-brand-blue/20">
                      <Zap className="w-4 h-4 fill-current" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="h-full flex items-center justify-center text-white/5 font-mono uppercase tracking-[0.3em]">
                System Analytics Placeholder
              </div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
