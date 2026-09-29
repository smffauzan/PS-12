import React, { useState } from 'react';
import type { ForensicMediaItem, TimelineMarker } from '../types/forensics';
import { Clock, Play, Pause } from 'lucide-react';

interface ForensicTimelineProps {
  item: ForensicMediaItem;
}

export const ForensicTimeline: React.FC<ForensicTimelineProps> = ({ item }) => {
  const markers = item.timelineMarkers.length > 0 ? item.timelineMarkers : [
    { id: 'tm-1', timestampSec: 0.0, formattedTime: '00:00', frameNumber: 1, visualScore: 18, audioScore: 12, avSyncScore: 95, overallRisk: 15, severity: 'LOW' as const, explanation: 'Initial anchor frame. Background scene geometry authentic.' },
    { id: 'tm-2', timestampSec: 7.3, formattedTime: '00:07', frameNumber: 219, visualScore: 68, audioScore: 78, avSyncScore: 72, overallRisk: 73, severity: 'MEDIUM' as const, explanation: 'Voice cloning pitch harmonic anomaly detected in 4kHz spectrum.' },
    { id: 'tm-3', timestampSec: 14.5, formattedTime: '00:14', frameNumber: 435, visualScore: 94, audioScore: 75, avSyncScore: 84, overallRisk: 91, severity: 'HIGH' as const, explanation: 'Peak facial manipulation anomaly. High-frequency skin texture loss.' },
    { id: 'tm-4', timestampSec: 21.0, formattedTime: '00:21', frameNumber: 630, visualScore: 91, audioScore: 82, avSyncScore: 88, overallRisk: 88, severity: 'HIGH' as const, explanation: 'Boundary blending optical flow flicker detected around facial perimeter.' },
    { id: 'tm-5', timestampSec: 30.0, formattedTime: '00:30', frameNumber: 900, visualScore: 35, audioScore: 40, avSyncScore: 90, overallRisk: 38, severity: 'LOW' as const, explanation: 'Outro sequence stabilizing. Background environment consistent.' }
  ];

  const [activeMarker, setActiveMarker] = useState<TimelineMarker>(markers[2] || markers[0]);
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="w-full glass-panel p-6 rounded-2xl flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              HIGH-RESOLUTION FORENSIC TIMELINE SCRUBBER
            </h3>
            <p className="text-xs font-mono text-slate-400">
              Per-frame anomaly tracking across visual, acoustic & temporal synchronization channels
            </p>
          </div>
        </div>

        <button 
          onClick={() => setIsPlaying(!isPlaying)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-cyan-300 font-mono text-xs transition-colors"
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          <span>{isPlaying ? 'PAUSE SCRUBBER' : 'PLAY SCRUBBER'}</span>
        </button>
      </div>

      <div className="relative bg-slate-950 p-6 rounded-xl border border-sky-500/20 flex flex-col gap-6">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-2">
          <span>00:00</span>
          <span>00:07</span>
          <span>00:14</span>
          <span>00:21</span>
          <span>00:30</span>
        </div>

        <div className="relative w-full h-3 rounded-full bg-slate-800 flex items-center">
          <div className="absolute inset-0 rounded-full bg-gradient-to-r from-emerald-500/40 via-amber-500/60 to-red-500/80 opacity-60" />

          {markers.map((marker) => {
            const positionPercent = (marker.timestampSec / 30.0) * 100;
            const isSelected = activeMarker.id === marker.id;

            return (
              <button
                key={marker.id}
                onClick={() => setActiveMarker(marker)}
                style={{ left: `${positionPercent}%` }}
                className={`absolute -translate-x-1/2 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                  marker.severity === 'HIGH' 
                    ? 'bg-red-500 border-red-300 shadow-[0_0_12px_#ff2a5f]' 
                    : marker.severity === 'MEDIUM' 
                    ? 'bg-amber-500 border-amber-300 shadow-[0_0_10px_#f59e0b]' 
                    : 'bg-emerald-500 border-emerald-300'
                } ${isSelected ? 'scale-125 ring-4 ring-cyan-400/50 z-20' : 'hover:scale-110 z-10'}`}
                title={`Marker ${marker.formattedTime} - ${marker.severity}`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-slate-950" />
              </button>
            );
          })}
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-sky-500/30 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl border flex flex-col items-center justify-center font-mono ${
              activeMarker.severity === 'HIGH' ? 'bg-red-500/10 border-red-500/40 text-red-400' : 'bg-amber-500/10 border-amber-500/40 text-amber-400'
            }`}>
              <span className="text-xl font-bold">{activeMarker.formattedTime}</span>
              <span className="text-[10px] tracking-wider uppercase font-bold">{activeMarker.severity} RISK</span>
            </div>

            <div className="flex flex-col">
              <div className="flex items-center gap-2 font-mono text-xs text-slate-400">
                <span>FRAME: <strong className="text-cyan-400">#{activeMarker.frameNumber}</strong></span>
                <span>•</span>
                <span>ANOMALY SCORE: <strong className="text-red-400">{activeMarker.overallRisk}%</strong></span>
              </div>
              <p className="mt-1 font-mono text-xs text-slate-200 leading-relaxed max-w-xl">
                {activeMarker.explanation}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs text-slate-300 bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 shrink-0">
            <div>VISUAL: <strong className="text-red-400">{activeMarker.visualScore}%</strong></div>
            <div className="h-4 w-[1px] bg-slate-800" />
            <div>AUDIO: <strong className="text-amber-400">{activeMarker.audioScore}%</strong></div>
            <div className="h-4 w-[1px] bg-slate-800" />
            <div>A/V SYNC: <strong className="text-red-400">{activeMarker.avSyncScore}%</strong></div>
          </div>
        </div>
      </div>
    </div>
  );
};
