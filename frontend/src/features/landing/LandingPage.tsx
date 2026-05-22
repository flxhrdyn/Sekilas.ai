import React, { useState, useEffect } from "react";
import { 
  Globe, 
  ShieldCheck, 
  Database, 
  Cpu, 
  Activity, 
  Zap, 
  ChevronRight, 
  Layers, 
  Terminal 
} from "lucide-react";
import { motion } from "motion/react";

interface LandingPageProps {
  onEnter: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onEnter }) => {
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
        "[03:32:05] GATEKEEPER_FILTER: 3 speculative speculative blog resources dropped",
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
      className="min-h-screen bg-[#050507] text-white overflow-y-auto relative custom-scrollbar scroll-smooth"
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
            className="bg-white/5 border border-white/10 px-6 py-2.5 rounded-xl hover:bg-white/10 transition-all font-sans cursor-pointer"
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
          <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-8 leading-[1.0] text-white">
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
              className="w-full md:w-auto bg-brand-blue text-white px-10 py-5 rounded-2xl font-bold text-lg shadow-2xl shadow-brand-blue/30 hover:scale-105 transition-all flex items-center justify-center gap-3 cursor-pointer"
            >
              Masuk ke Terminal <ChevronRight className="w-5 h-5" />
            </button>
            <button 
              onClick={() => scrollToSection('pipeline')}
              className="w-full md:w-auto bg-white/5 border border-white/10 text-white px-10 py-5 rounded-2xl font-bold text-lg hover:bg-white/10 hover:border-white/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              Pelajari Arsitektur <Activity className="w-4 h-4 text-brand-blue" />
            </button>
          </div>
        </motion.div>
      </section>

      {/* Features Bento Grid */}
      <section id="features" className="px-6 max-w-7xl mx-auto pb-24 border-b border-white/5 relative z-10">
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
                className="bg-white text-brand-blue px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all shadow-md cursor-pointer"
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
      <section id="pipeline" className="px-6 py-32 max-w-7xl mx-auto relative z-10">
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
                  className={`text-left p-6 rounded-2xl border transition-all flex gap-5 items-start relative z-10 cursor-pointer ${
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
                    <h4 className="text-xl font-bold mb-1 text-white">{step.name}</h4>
                    <p className="text-xs text-white/50 line-clamp-2 md:line-clamp-none">{step.description}</p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right Column: Tactical Console / Logs Preview */}
          <div className="lg:col-span-7 flex flex-col">
            <div className="data-card bg-[#0a0a0c] border border-white/5 p-8 flex-1 flex flex-col justify-between relative overflow-hidden">
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

                  <div className="font-mono text-xs space-y-2 bg-black/40 rounded-xl p-5 border border-white/5 min-h-[140px]">
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
                  className={`w-full sm:w-auto px-6 py-3 rounded-xl font-bold font-mono text-xs transition-all flex items-center justify-center gap-2 cursor-pointer ${
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
      <footer className="border-t border-white/5 py-20 px-10 relative z-10">
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
