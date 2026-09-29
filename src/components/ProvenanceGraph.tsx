import React from 'react';
import type { ForensicMediaItem, ProvenanceNode } from '../types/forensics';
import { GitCommit, ShieldCheck, AlertTriangle, Info } from 'lucide-react';

interface ProvenanceGraphProps {
  item: ForensicMediaItem;
}

export const ProvenanceGraph: React.FC<ProvenanceGraphProps> = ({ item }) => {
  const nodes: ProvenanceNode[] = item.provenanceGraph.length > 0 ? item.provenanceGraph : [
    { id: 'p-1', title: 'Captured Raw Feed', type: 'source', status: 'UNKNOWN', deviceOrSoftware: 'Sony FX6 Broadcast Cam (Unverified)', timestamp: '2026-09-28 19:00:12', details: 'Initial recording source lacking hardware C2PA key chip.' },
    { id: 'p-2', title: 'Neural Model Pipeline', type: 'creation', status: 'UNVERIFIED', deviceOrSoftware: 'DeepFaceLive + Synthesizer v3.1', timestamp: '2026-09-28 21:14:02', details: 'Synthetic facial replacement & neural audio overlay generated.' },
    { id: 'p-3', title: 'Video Post Editing', type: 'edit', status: 'UNVERIFIED', deviceOrSoftware: 'Adobe Premiere Pro 24.2', timestamp: '2026-09-29 01:20:00', details: 'Color grading and audio track composition.' },
    { id: 'p-4', title: 'Social Stream Export', type: 'export', status: 'UNVERIFIED', deviceOrSoftware: 'FFmpeg H.264 Encoder', timestamp: '2026-09-29 02:40:11', details: 'Re-encoded container without content credentials.' },
    { id: 'p-5', title: 'VERITAS Intake', type: 'current', status: 'UNVERIFIED', deviceOrSoftware: 'VERITAS Forensic Node #09', timestamp: '2026-09-29 14:22:08', details: 'Ingested for multimodal synthetic media verification.' }
  ];

  return (
    <div className="w-full glass-panel p-6 rounded-2xl flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <GitCommit className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              C2PA CONTENT CREDENTIALS & PROVENANCE GRAPH
            </h3>
            <p className="text-xs font-mono text-slate-400">
              Cryptographic chain of custody, manifest verification & device lineage tracking
            </p>
          </div>
        </div>

        <div className={`px-3 py-1.5 rounded-full border font-mono text-xs font-bold flex items-center gap-1.5 ${
          item.c2paStatus === 'VERIFIED' 
            ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400' 
            : 'bg-amber-500/10 border-amber-500/40 text-amber-400'
        }`}>
          {item.c2paStatus === 'VERIFIED' ? <ShieldCheck className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
          <span>C2PA MANIFEST: {item.c2paStatus}</span>
        </div>
      </div>

      <div className="p-3.5 rounded-xl bg-slate-900/80 border border-sky-500/30 flex items-start gap-3">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <p className="text-xs font-mono text-slate-300 leading-relaxed">
          <strong className="text-cyan-300 uppercase">IMPORTANT PROVENANCE POLICY:</strong> Absence of C2PA provenance metadata indicates unverified lineage, not definitive AI generation. Model signals are evaluated independently.
        </p>
      </div>

      <div className="relative py-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative z-10">
          {nodes.map((node, idx) => {
            const isVerified = node.status === 'VERIFIED';
            const isUnverified = node.status === 'UNVERIFIED';

            return (
              <div 
                key={node.id}
                className={`p-4 rounded-xl border flex flex-col gap-3 transition-all relative ${
                  isVerified 
                    ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300' 
                    : isUnverified 
                    ? 'bg-amber-950/20 border-amber-500/40 text-amber-300' 
                    : 'bg-slate-900/60 border-slate-800 text-slate-400'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase font-bold tracking-widest text-slate-400">
                    STEP 0{idx + 1}
                  </span>
                  <span className={`px-2 py-0.5 text-[9px] font-mono font-bold rounded ${
                    isVerified ? 'bg-emerald-500/20 text-emerald-400' : isUnverified ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {node.status}
                  </span>
                </div>

                <div className="font-mono text-xs font-bold text-slate-100">
                  {node.title}
                </div>

                <div className="text-[11px] font-mono text-slate-400 leading-tight">
                  {node.deviceOrSoftware}
                </div>

                <div className="text-[10px] font-mono text-slate-500 mt-auto pt-2 border-t border-slate-800/60">
                  {node.timestamp}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
