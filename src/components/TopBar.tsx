import React, { useState, useEffect } from 'react';
import { useForensic } from '../context/ForensicContext';
import { ShieldCheck, Cpu, Clock, User, Radio, Info, Server } from 'lucide-react';

export const TopBar: React.FC = () => {
  const { isSidebarCollapsed, toastMessage, isBackendConnected } = useForensic();
  const [timeString, setTimeString] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeString(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className={`fixed top-0 right-0 z-30 h-16 bg-[#080b12]/90 backdrop-blur-md border-b border-sky-500/15 px-6 flex items-center justify-between transition-all duration-300 ${
      isSidebarCollapsed ? 'left-20' : 'left-64'
    }`}>
      {/* Left status highlights */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]" />
          <span className="text-emerald-400 font-semibold tracking-wider">SYSTEM ONLINE</span>
        </div>

        {/* Dynamic Engine Status Badge */}
        {isBackendConnected ? (
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 text-[10px] font-mono font-bold uppercase tracking-wider">
            <Server className="w-3 h-3 text-emerald-400" />
            <span>LIVE ENGINE // API CONNECTED</span>
          </div>
        ) : (
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[10px] font-mono font-bold uppercase tracking-wider">
            <Info className="w-3 h-3 text-amber-400" />
            <span>DEMO MODE // SIMULATED ANALYSIS</span>
          </div>
        )}

        <div className="hidden xl:flex items-center gap-2 text-xs font-mono text-slate-400 border-l border-slate-800 pl-4">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>LATENCY: <strong className="text-slate-200">14ms</strong></span>
        </div>
      </div>

      {/* Center Toast notification alert */}
      {toastMessage && (
        <div className="absolute left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-cyan-950/90 border border-cyan-400/50 text-cyan-300 text-xs font-mono shadow-[0_0_15px_rgba(0,240,255,0.2)] animate-bounce flex items-center gap-2">
          <Radio className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Right meta details */}
      <div className="flex items-center gap-4">
        {/* Model Version Tag */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-sky-500/20 text-[11px] font-mono text-cyan-300">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>v0.9.0-PROTOTYPE</span>
        </div>

        {/* Live Clock */}
        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-400 border-l border-slate-800 pl-4">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{timeString || '2026-09-29 16:25:00 UTC'}</span>
        </div>

        {/* User Profile Area */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500/20 to-violet-600/30 border border-cyan-400/30 flex items-center justify-center text-cyan-300 shadow-md">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden sm:flex flex-col text-left">
            <span className="text-xs font-mono font-bold text-slate-200">FORENSIC ANALYST</span>
            <span className="text-[9px] font-mono text-emerald-400 tracking-wider">SESSION ACTIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
};
