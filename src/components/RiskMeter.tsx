import React from 'react';
import type { RiskLevel } from '../types/forensics';
import { ShieldAlert, ShieldCheck, AlertTriangle, HelpCircle } from 'lucide-react';

interface RiskMeterProps {
  score: number | null;
  riskTier: RiskLevel;
  confidence: number;
  size?: 'sm' | 'md' | 'lg';
  showDescription?: boolean;
}

export const RiskMeter: React.FC<RiskMeterProps> = ({ 
  score, 
  riskTier, 
  confidence, 
  size = 'md',
  showDescription = true 
}) => {
  const getColorScheme = () => {
    switch (riskTier) {
      case 'HIGH RISK':
        return {
          stroke: '#ff2a5f',
          glow: 'rgba(255, 42, 95, 0.4)',
          text: 'text-red-400',
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          icon: ShieldAlert,
          label: 'HIGH MANIPULATION RISK',
          desc: 'High manipulation risk based on detected synthetic signals.'
        };
      case 'MEDIUM RISK':
        return {
          stroke: '#f59e0b',
          glow: 'rgba(245, 158, 11, 0.4)',
          text: 'text-amber-400',
          bg: 'bg-amber-500/10',
          border: 'border-amber-500/30',
          icon: AlertTriangle,
          label: 'MEDIUM MANIPULATION RISK',
          desc: 'Evidence indicates possible synthetic or manipulated content.'
        };
      case 'LOW RISK':
        return {
          stroke: '#10b981',
          glow: 'rgba(16, 185, 129, 0.4)',
          text: 'text-emerald-400',
          bg: 'bg-emerald-500/10',
          border: 'border-emerald-500/30',
          icon: ShieldCheck,
          label: 'LOW MANIPULATION RISK',
          desc: 'Signals indicate high likelihood of authentic media.'
        };
      default:
        return {
          stroke: '#00f0ff',
          glow: 'rgba(0, 240, 255, 0.4)',
          text: 'text-cyan-400',
          bg: 'bg-cyan-500/10',
          border: 'border-cyan-500/30',
          icon: HelpCircle,
          label: 'INCONCLUSIVE ANALYSIS',
          desc: 'Additional forensic verification recommended.'
        };
    }
  };

  const scheme = getColorScheme();
  const Icon = scheme.icon;

  const radius = size === 'lg' ? 70 : size === 'sm' ? 40 : 55;
  const strokeWidth = size === 'lg' ? 10 : size === 'sm' ? 6 : 8;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = score !== null ? circumference - (score / 100) * circumference : circumference;

  const svgDimensions = radius * 2 + strokeWidth * 2 + 10;

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative flex items-center justify-center">
        <svg 
          width={svgDimensions} 
          height={svgDimensions} 
          className="transform -rotate-90 drop-shadow-[0_0_12px_var(--glow)]"
          style={{ '--glow': scheme.glow } as React.CSSProperties}
        >
          <circle
            cx={svgDimensions / 2}
            cy={svgDimensions / 2}
            r={radius}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={svgDimensions / 2}
            cy={svgDimensions / 2}
            r={radius}
            stroke={scheme.stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className={`font-mono font-bold tracking-tight ${
            size === 'lg' ? 'text-4xl' : size === 'sm' ? 'text-xl' : 'text-3xl'
          } ${scheme.text}`}>
            {score !== null ? `${score}%` : 'N/A'}
          </span>
          <span className="text-[9px] font-mono tracking-widest text-slate-400 uppercase">
            RISK SCORE
          </span>
        </div>
      </div>

      <div className="mt-3 flex flex-col items-center text-center">
        <div className={`px-3 py-1 rounded-full border ${scheme.bg} ${scheme.border} flex items-center gap-1.5`}>
          <Icon className={`w-4 h-4 ${scheme.text}`} />
          <span className={`text-xs font-mono font-bold tracking-wider ${scheme.text}`}>
            {scheme.label}
          </span>
        </div>

        {showDescription && (
          <p className="mt-2 text-xs font-mono text-slate-400 max-w-xs leading-relaxed">
            {scheme.desc}
          </p>
        )}

        <div className="mt-2 flex items-center gap-4 text-[11px] font-mono text-slate-400">
          <span>CONFIDENCE: <strong className="text-cyan-300">{confidence}%</strong></span>
          <span>MARGIN: <strong className="text-slate-300">±2.4%</strong></span>
        </div>
      </div>
    </div>
  );
};
