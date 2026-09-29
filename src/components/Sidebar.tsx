import React from 'react';
import { useForensic } from '../context/ForensicContext';
import type { NavTab } from '../context/ForensicContext';
import { 
  LayoutDashboard, 
  UploadCloud, 
  Radio, 
  Search, 
  Clock, 
  GitCommit, 
  ShieldCheck, 
  FileText,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Cpu
} from 'lucide-react';


interface NavItem {
  id: NavTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export interface NavGroup {
  title?: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'COMMAND & INTAKE',
    items: [
      { id: 'command-center', label: 'Command Center', icon: LayoutDashboard },
      { id: 'intake', label: 'Media Intake', icon: UploadCloud, badge: 'INTAKE' },
      { id: 'live', label: 'Live Forensics', icon: Radio, badge: 'LIVE' },
    ]
  },
  {
    title: 'DEEP FORENSICS',
    items: [
      { id: 'evidence', label: 'Evidence Lab', icon: Search },
      { id: 'timeline', label: 'Forensic Timeline', icon: Clock },
      { id: 'provenance', label: 'Provenance', icon: GitCommit },
      { id: 'consensus', label: 'Model Consensus', icon: ShieldCheck },
    ]
  },
  {
    title: 'ADVANCED & REPORTING',
    items: [
      { id: 'multimodal', label: 'Technical Details', icon: Cpu },
      { id: 'reports', label: 'Forensic Report', icon: FileText },
    ]
  }
];


export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, activeItem, isSidebarCollapsed, setIsSidebarCollapsed } = useForensic();

  return (
    <aside 
      className={`fixed top-0 left-0 bottom-0 z-40 bg-[#080b12]/95 backdrop-blur-xl border-r border-sky-500/15 flex flex-col transition-all duration-300 ease-in-out ${
        isSidebarCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 px-4 border-b border-sky-500/15 flex items-center justify-between">
        <div 
          onClick={() => setActiveTab('command-center')} 
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-violet-600/20 border border-cyan-400/40 group-hover:border-cyan-400 transition-colors">
            <ShieldAlert className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-cyan-400 rounded-full animate-ping" />
          </div>
          {!isSidebarCollapsed && (
            <div className="flex flex-col">
              <span className="font-mono font-bold text-lg tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-200 to-violet-400">
                VERITAS<span className="text-cyan-400">.AI</span>
              </span>
              <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase">
                Detect. Explain. Verify.
              </span>
            </div>
          )}
        </div>

        <button 
          onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          className="p-1.5 rounded-md hover:bg-slate-800/60 text-slate-400 hover:text-cyan-400 transition-colors"
          title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isSidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        {NAV_GROUPS.map((group, gIdx) => (
          <div key={gIdx} className="space-y-1">
            {!isSidebarCollapsed && group.title && (
              <div className="px-3 pt-1 pb-1 text-[9px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                {group.title}
              </div>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg font-mono text-xs text-left transition-all duration-200 group relative ${
                    isActive 
                      ? 'bg-gradient-to-r from-cyan-500/20 to-violet-600/10 text-cyan-300 border border-cyan-400/40 shadow-[0_0_12px_rgba(0,240,255,0.15)] font-semibold' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 hover:border-slate-700/50 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 transition-transform ${
                    isActive ? 'text-cyan-400 scale-110' : 'text-slate-400 group-hover:text-cyan-400'
                  }`} />
                  
                  {!isSidebarCollapsed && (
                    <span className="flex-1 truncate tracking-wide">{item.label}</span>
                  )}

                  {!isSidebarCollapsed && item.badge && (
                    <span className={`px-1.5 py-0.5 text-[9px] font-mono rounded font-bold uppercase tracking-wider ${
                      item.badge === 'LIVE' ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse' : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                    }`}>
                      {item.badge}
                    </span>
                  )}

                  {/* Tooltip when collapsed */}
                  {isSidebarCollapsed && (
                    <div className="absolute left-full ml-3 px-2.5 py-1 bg-slate-900 border border-sky-500/30 rounded text-cyan-300 text-xs font-mono shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                      {item.label}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>


      {/* Target Media Indicator */}
      {!isSidebarCollapsed && activeItem && (
        <div className="p-3 m-2 rounded-lg bg-slate-900/80 border border-sky-500/20 flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 uppercase tracking-wider">
            <span className="flex items-center gap-1"><Cpu className="w-3 h-3 text-cyan-400" /> Active Target</span>
            <span className={`px-1 rounded text-[9px] font-bold ${
              activeItem.riskTier === 'HIGH RISK' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
            }`}>
              {activeItem.overallRiskScore}%
            </span>
          </div>
          <div className="text-xs font-mono text-slate-200 truncate font-medium">
            {activeItem.filename}
          </div>
          <div className="text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>{activeItem.mediaType.toUpperCase()}</span>
            <span>{activeItem.fileSize}</span>
          </div>
        </div>
      )}
    </aside>
  );
};
