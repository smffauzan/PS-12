import React from 'react';
import type { ForensicExplanation, ExplanationReason } from '../types/forensics';
import { 
  ShieldAlert, 
  Eye, 
  Volume2, 
  Clock, 
  GitCommit, 
  Sparkles, 
  AlertTriangle,
  Info
} from 'lucide-react';

interface ExplanationCardProps {
  explanation: ForensicExplanation;
  onInspectEvidence?: (reason: ExplanationReason) => void;
}

export const ExplanationCard: React.FC<ExplanationCardProps> = ({ 
  explanation,
  onInspectEvidence 
}) => {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'VISUAL':
        return <Eye className="w-4 h-4 text-cyan-400" />;
      case 'AUDIO':
        return <Volume2 className="w-4 h-4 text-violet-400" />;
      case 'TEMPORAL':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'A/V SYNC':
        return <Sparkles className="w-4 h-4 text-pink-400" />;
      case 'PROVENANCE':
        return <GitCommit className="w-4 h-4 text-blue-400" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-slate-400" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
      case 'HIGH':
        return 'bg-red-500/15 text-red-400 border border-red-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border border-amber-500/30';
      case 'LOW':
      default:
        return 'bg-slate-800 text-slate-300 border border-slate-700';
    }
  };

  return (
    <div className="glass-panel p-6 sm:p-7 rounded-2xl border border-sky-500/20 bg-gradient-to-b from-slate-900/90 to-[#070b14]/95 flex flex-col gap-6 shadow-xl">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-sky-500/15">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center">
            <ShieldAlert className="w-4 h-4 text-red-400" />
          </div>
          <div>
            <h2 className="font-mono text-base sm:text-lg font-bold text-slate-100 uppercase tracking-wide">
              WHY WAS THIS FLAGGED?
            </h2>
            <p className="font-mono text-xs text-slate-400">
              Grounded, evidence-derived forensic explanation from actual model outputs
            </p>
          </div>
        </div>

        <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-[11px] font-mono font-bold self-start sm:self-auto">
          {explanation.reasons.length} VERIFIED SIGNALS
        </span>
      </div>

      {/* Summary Lead */}
      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-3">
        <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div className="space-y-1 font-mono text-xs">
          <span className="font-bold text-slate-200 block text-sm">
            {explanation.headline}
          </span>
          <p className="text-slate-400 leading-relaxed">
            {explanation.summary}
          </p>
        </div>
      </div>

      {/* Structured Grounded Reasons */}
      <div className="space-y-3">
        {explanation.reasons.length === 0 ? (
          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center font-mono text-xs text-slate-400">
            No forensic anomalies were flagged for this target media.
          </div>
        ) : (
          explanation.reasons.map((reason, idx) => (
            <div
              key={idx}
              onClick={() => onInspectEvidence?.(reason)}
              className="group p-4 rounded-xl bg-slate-950/70 hover:bg-slate-900/80 border border-slate-800/80 hover:border-cyan-500/40 transition-all flex flex-col gap-2.5 cursor-pointer"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-md bg-slate-900 border border-slate-800 group-hover:border-cyan-500/30 transition-colors">
                    {getCategoryIcon(reason.category)}
                  </div>
                  <span className="font-mono text-xs font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">
                    {reason.title}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {reason.timestamp_start !== undefined && (
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-cyan-400 font-bold">
                      {reason.timestamp_end !== undefined
                        ? `${formatSeconds(reason.timestamp_start)} – ${formatSeconds(reason.timestamp_end)}`
                        : formatSeconds(reason.timestamp_start)}
                    </span>
                  )}
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${getSeverityBadge(reason.severity)}`}>
                    {reason.severity}
                  </span>
                </div>
              </div>

              <p className="font-mono text-xs text-slate-400 leading-relaxed pl-8">
                {reason.description}
              </p>
            </div>
          ))
        )}
      </div>

      {/* Forensic Limitations Disclosure */}
      {explanation.limitations && explanation.limitations.length > 0 && (
        <div className="pt-3 border-t border-slate-800/80 flex flex-col gap-1.5 font-mono text-[11px] text-slate-500">
          <span className="font-bold uppercase tracking-wider text-slate-400">
            FORENSIC LIMITATIONS & PROTOCOL DISCLOSURES:
          </span>
          <ul className="list-disc list-inside space-y-0.5 text-slate-500">
            {explanation.limitations.map((lim, i) => (
              <li key={i}>{lim}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

function formatSeconds(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.floor((sec % 1) * 10);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}${ms > 0 ? `.${ms}` : ''}`;
}
