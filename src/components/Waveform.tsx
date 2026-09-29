import React, { useState } from 'react';
import { Play, Pause, Volume2, Mic } from 'lucide-react';

interface WaveformProps {
  data?: number[];
  riskScore?: number;
  transcript?: { time: string; speaker: string; text: string; suspicious: boolean }[];
}

export const Waveform: React.FC<WaveformProps> = ({ 
  data = [25, 45, 60, 85, 95, 70, 40, 30, 50, 90, 100, 80, 60, 35, 55, 75, 90, 85, 40, 20, 65, 80, 95, 70, 45, 30, 60, 85, 50, 25],
  riskScore = 73,
  transcript = []
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  return (
    <div className="w-full glass-panel p-5 rounded-2xl flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-violet-500/10 border border-violet-500/30 text-violet-400">
            <Volume2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              SPECTRAL AUDIO WAVEFORM & CLONING DETECTOR
            </h3>
            <p className="text-xs font-mono text-slate-400">
              High-frequency formant analysis, pitch phase tracking & deepfake voice synthesis detection
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400">AUDIO RISK:</span>
          <span className={`px-2.5 py-1 rounded font-mono text-xs font-bold ${
            riskScore >= 75 ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
          }`}>
            {riskScore}% (HIGH)
          </span>
        </div>
      </div>

      <div className="relative bg-slate-950/80 p-4 rounded-xl border border-sky-500/20 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-cyan-300 font-mono text-xs transition-colors"
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'PAUSE AUDIO' : 'PLAY AUDIO'}</span>
          </button>

          <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
            <span>FORMAT: <strong className="text-slate-200">PCM 48.0 kHz 24-bit</strong></span>
            <span>NOISE FLOOR: <strong className="text-slate-200">-54 dB</strong></span>
          </div>
        </div>

        <div className="h-32 flex items-center justify-between gap-1.5 px-2 bg-[#080b12] rounded-lg border border-slate-800/80 overflow-hidden relative group">
          {isPlaying && (
            <div className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 shadow-[0_0_10px_#00f0ff] animate-scanline z-10" />
          )}

          {data.map((height, idx) => {
            const isSuspiciousBar = idx > 8 && idx < 20;
            return (
              <div
                key={idx}
                onMouseEnter={() => setHoverIndex(idx)}
                onMouseLeave={() => setHoverIndex(null)}
                className="flex-1 flex flex-col items-center justify-center gap-1 cursor-pointer h-full py-2 group/bar"
              >
                <div 
                  className={`w-full rounded-sm transition-all duration-200 ${
                    isSuspiciousBar 
                      ? 'bg-gradient-to-t from-red-500 to-rose-400 shadow-[0_0_8px_rgba(255,42,95,0.4)]' 
                      : 'bg-gradient-to-t from-cyan-500 to-sky-300'
                  } ${hoverIndex === idx ? 'brightness-125 scale-y-110' : ''}`}
                  style={{ height: `${height}%` }}
                />
              </div>
            );
          })}
        </div>

        <div className="h-12 w-full rounded-lg overflow-hidden border border-slate-800 flex relative">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-950 via-purple-900 to-pink-900/60 opacity-80" />
          <div className="absolute inset-0 bg-tech-grid opacity-30" />
          <div className="relative z-10 w-full h-full flex items-center justify-between px-4 text-[10px] font-mono text-cyan-300">
            <span>20 Hz</span>
            <span className="text-red-400 font-bold">SYNTHETIC HARMONIC ANOMALY (3.8 - 5.2 kHz)</span>
            <span>20 kHz</span>
          </div>
        </div>
      </div>

      {transcript.length > 0 && (
        <div className="flex flex-col gap-2 pt-1">
          <h4 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Mic className="w-4 h-4 text-cyan-400" />
            SYNCHRONIZED TRANSCRIPT ANALYSIS
          </h4>
          <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
            {transcript.map((item, idx) => (
              <div 
                key={idx} 
                className={`p-3 rounded-lg border flex items-start gap-3 font-mono text-xs transition-colors ${
                  item.suspicious 
                    ? 'bg-red-500/10 border-red-500/30 text-red-300' 
                    : 'bg-slate-900/60 border-slate-800 text-slate-300'
                }`}
              >
                <span className="text-slate-500 font-bold shrink-0">{item.time}</span>
                <span className="text-cyan-400 font-semibold shrink-0">{item.speaker}:</span>
                <p className="flex-1">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
