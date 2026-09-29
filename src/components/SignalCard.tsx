import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface SignalCardProps {
  title: string;
  score: number;
  confidence: number;
  icon: LucideIcon;
  category: 'visual' | 'audio' | 'temporal' | 'sync' | 'provenance';
  details: string;
  onClick?: () => void;
}

export const SignalCard: React.FC<SignalCardProps> = ({
  title,
  score,
  confidence,
  icon: Icon,
  category,
  details,
  onClick
}) => {
  const getStatusColor = () => {
    if (category === 'provenance') {
      return score < 50 
        ? { text: 'text-amber-400', bar: 'bg-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/30' }
        : { text: 'text-emerald-400', bar: 'bg-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' };
    }
    if (score >= 75) return { text: 'text-red-400', bar: 'bg-gradient-to-r from-red-500 to-rose-400', bg: 'bg-red-500/10', border: 'border-red-500/30' };
    if (score >= 50) return { text: 'text-amber-400', bar: 'bg-gradient-to-r from-amber-500 to-yellow-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30' };
    return { text: 'text-emerald-400', bar: 'bg-gradient-to-r from-emerald-500 to-teal-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' };
  };

  const status = getStatusColor();

  return (
    <div 
      onClick={onClick}
      className={`glass-panel-interactive p-4 rounded-xl flex flex-col gap-3 cursor-pointer group`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg ${status.bg} border ${status.border} text-cyan-400 group-hover:scale-105 transition-transform`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="font-mono text-xs font-semibold text-slate-200 uppercase tracking-wide">
            {title}
          </span>
        </div>
        
        <span className={`font-mono text-base font-bold ${status.text}`}>
          {score}%
        </span>
      </div>

      <div className="w-full h-1.5 rounded-full bg-slate-800/80 overflow-hidden relative">
        <div 
          className={`h-full ${status.bar} transition-all duration-700 ease-out`}
          style={{ width: `${score}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
        <span className="truncate max-w-[200px]">{details}</span>
        <span className="shrink-0 text-slate-400">
          CONF: <strong className="text-cyan-300">{confidence}%</strong>
        </span>
      </div>
    </div>
  );
};
