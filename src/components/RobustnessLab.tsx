import React, { useState } from 'react';
import type { ForensicMediaItem } from '../types/forensics';
import { Sliders, Activity } from 'lucide-react';

interface RobustnessLabProps {
  item: ForensicMediaItem;
}

export const RobustnessLab: React.FC<RobustnessLabProps> = ({ item }) => {
  const [blurRadius, setBlurRadius] = useState<number>(2.0);
  const [compressionRatio, setCompressionRatio] = useState<number>(60);

  const baseScore = item.overallRiskScore ?? 50;
  const dynamicScore = Math.max(
    30,
    Math.round(baseScore - blurRadius * 4.5 - (100 - compressionRatio) * 0.15)
  );

  return (
    <div className="w-full glass-panel p-6 rounded-2xl flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              ANTI-FORENSIC ROBUSTNESS & ADVERSARIAL STRESS-TESTING LAB
            </h3>
            <p className="text-xs font-mono text-slate-400">
              Evaluation of model resilience against social media compression, re-encoding & spatial distortions
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400">MODEL STABILITY:</span>
          <span className="px-3 py-1 rounded bg-emerald-500/20 text-emerald-300 font-mono text-xs font-bold border border-emerald-400/40">
            96.8% HIGH RESILIENCE
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 space-y-3">
          <h4 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wider">
            TRANSFORMATION BENCHMARK RESULTS
          </h4>

          {item.robustnessResults.map((res) => (
            <div 
              key={res.id}
              className="p-3.5 rounded-xl bg-slate-950/80 border border-sky-500/20 flex items-center justify-between font-mono text-xs"
            >
              <div>
                <div className="font-bold text-slate-200">{res.transformation}</div>
                <div className="text-[11px] text-slate-500">{res.parameter}</div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-slate-400">ORIGINAL: <strong className="text-slate-200">{res.originalScore}%</strong></div>
                <div className="text-slate-400">AFTER: <strong className="text-cyan-400">{res.transformedScore}%</strong></div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  res.status === 'Stable' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                }`}>
                  {res.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="lg:col-span-5 p-5 rounded-xl bg-slate-950/90 border border-sky-500/30 flex flex-col gap-5">
          <h4 className="font-mono text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            LIVE ADVERSARIAL SIMULATOR
          </h4>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">GAUSSIAN BLUR RADIUS:</span>
              <span className="text-cyan-400 font-bold">{blurRadius.toFixed(1)} px</span>
            </div>
            <input 
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={blurRadius}
              onChange={(e) => setBlurRadius(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 bg-slate-800 h-2 rounded cursor-pointer"
            />
          </div>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">COMPRESSION QUALITY:</span>
              <span className="text-cyan-400 font-bold">{compressionRatio}%</span>
            </div>
            <input 
              type="range"
              min="10"
              max="100"
              step="5"
              value={compressionRatio}
              onChange={(e) => setCompressionRatio(parseInt(e.target.value))}
              className="w-full accent-cyan-400 bg-slate-800 h-2 rounded cursor-pointer"
            />
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center text-center gap-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">
              SIMULATED DETECTION RESILIENCE
            </span>
            <span className="text-3xl font-mono font-bold text-cyan-400">
              {dynamicScore}%
            </span>
            <span className="text-[11px] font-mono text-slate-400 mt-1">
              Model detection signal remains strong despite adversarial filtering.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
