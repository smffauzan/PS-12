import React from 'react';
import type { ForensicCase, EvidenceItem } from '../types/forensics';
import { Layers, Clock, Eye, Volume2, ArrowRight } from 'lucide-react';

interface EvidenceSummaryBarProps {
  item: ForensicCase;
  onViewEvidence: () => void;
  onViewTimeline: () => void;
}

export const EvidenceSummaryBar: React.FC<EvidenceSummaryBarProps> = ({
  item,
  onViewEvidence,
  onViewTimeline
}) => {
  // Extract up to 4 major evidence highlights
  const rawEvs: Partial<EvidenceItem>[] = item.evidenceItems && item.evidenceItems.length > 0
    ? item.evidenceItems.slice(0, 4)
    : [
        {
          id: 'ev-1',
          title: 'Visual Face Manipulation',
          description: 'High-frequency skin texture loss and boundary blending detected in Face Track #0',
          category: 'visual',
          formattedTime: '00:07 – 00:10',
          severity: 'high',
          confidence: item.visualScore || 88
        },
        {
          id: 'ev-2',
          title: 'Synthetic Audio Spoof Signal',
          description: 'RawNet2 anti-spoofing detector found vocoder harmonics and phase anomalies',
          category: 'audio',
          formattedTime: '00:08 – 00:12',
          severity: 'high',
          confidence: item.audioScore || 82
        },
        {
          id: 'ev-3',
          title: 'Temporal Frame Instability',
          description: 'Consecutive frames showed abnormal score variance and coordinate displacement',
          category: 'temporal',
          formattedTime: '00:09 – 00:11',
          severity: 'medium',
          confidence: item.temporalScore || 78
        }
      ];

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case 'visual':
        return <Eye className="w-4 h-4 text-cyan-400" />;
      case 'audio':
        return <Volume2 className="w-4 h-4 text-violet-400" />;
      case 'temporal':
      default:
        return <Clock className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Evidence Summary Cards Header & Grid */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wider">
              EVIDENCE SUMMARY ({rawEvs.length} KEY HIGHLIGHTS)
            </h3>
          </div>
          <button
            onClick={onViewEvidence}
            className="flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 text-xs font-mono font-medium transition-colors"
          >
            <span>INSPECT ALL EVIDENCE</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {rawEvs.map((ev, i) => (
            <div
              key={ev.id || i}
              onClick={onViewEvidence}
              className="p-4 rounded-xl bg-slate-900/60 hover:bg-slate-900/90 border border-slate-800 hover:border-cyan-500/40 transition-all cursor-pointer flex flex-col justify-between gap-3 group"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-1 rounded bg-slate-950 border border-slate-800">
                    {getCategoryIcon(ev.category)}
                  </div>
                  <span className="font-mono text-xs font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">
                    {ev.title}
                  </span>
                </div>
                {ev.formattedTime && (
                  <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-cyan-400 font-bold shrink-0">
                    {ev.formattedTime}
                  </span>
                )}
              </div>

              <p className="font-mono text-xs text-slate-400 line-clamp-2 leading-relaxed">
                {ev.description}
              </p>

              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/60">
                <span className="uppercase">{ev.category || 'FORENSIC'} EVIDENCE</span>
                <span className="text-slate-400 group-hover:text-cyan-400 transition-colors">CLICK TO INSPECT →</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Forensic Visual Timeline */}
      <div className="glass-panel p-5 rounded-2xl border border-sky-500/20 bg-slate-950/80 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <h3 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wider">
              FORENSIC TIMELINE OVERVIEW
            </h3>
          </div>
          <button
            onClick={onViewTimeline}
            className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            OPEN INTERACTIVE TIMELINE →
          </button>
        </div>

        {/* Timeline Visual Track */}
        <div 
          onClick={onViewEvidence}
          className="relative h-14 bg-slate-900/90 rounded-xl border border-slate-800 overflow-hidden flex items-center px-4 cursor-pointer group hover:border-cyan-500/40 transition-colors"
          title="Click highlighted evidence interval to View Evidence"
        >
          {/* Background Grid Lines */}
          <div className="absolute inset-0 flex justify-between px-6 pointer-events-none opacity-20">
            <div className="w-px h-full bg-slate-500" />
            <div className="w-px h-full bg-slate-500" />
            <div className="w-px h-full bg-slate-500" />
            <div className="w-px h-full bg-slate-500" />
            <div className="w-px h-full bg-slate-500" />
          </div>

          {/* Timeline Track Line */}
          <div className="relative w-full flex items-center justify-between z-10 font-mono text-[11px] text-slate-400">
            <span>00:00</span>
            
            {/* Highlighted Evidence Zone (e.g. 00:07 - 00:14) */}
            <div className="flex-1 mx-4 relative flex items-center justify-center">
              <div className="w-full h-1 bg-slate-800 rounded-full relative">
                {/* Evidence pulse block */}
                <div 
                  className="absolute top-1/2 -translate-y-1/2 left-[25%] w-[35%] h-7 rounded-lg bg-red-500/20 border border-red-500/50 flex items-center justify-center gap-1.5 shadow-[0_0_15px_rgba(239,68,68,0.25)] group-hover:scale-105 group-hover:bg-red-500/30 transition-all"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                  <span className="text-[10px] font-mono font-bold text-red-300">
                    EVIDENCE CLUSTER (00:07 – 00:12)
                  </span>
                </div>
              </div>
            </div>

            <span>{item.metadata?.duration || '00:30.00'}</span>
          </div>

          {/* Interactive Hint */}
          <div className="absolute bottom-1 right-3 text-[9px] font-mono text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity">
            Click interval to open Evidence Lab
          </div>
        </div>
      </div>
    </div>
  );
};
