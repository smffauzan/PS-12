import React, { useState } from 'react';
import type { ForensicMediaItem, EvidenceItem } from '../types/forensics';
import { Eye, ZoomIn, ZoomOut, ShieldAlert, Sparkles, Layers } from 'lucide-react';

interface EvidenceViewerProps {
  item: ForensicMediaItem;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ item }) => {
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showBoundingBox, setShowBoundingBox] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(
    item.evidenceItems[0] || null
  );

  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div className="lg:col-span-7 glass-panel p-5 rounded-2xl flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              FORENSIC VISUAL INSPECTOR
            </h3>
          </div>

          <div className="flex items-center gap-2 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setShowHeatmap(!showHeatmap)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                showHeatmap ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>HEATMAP {showHeatmap ? 'ON' : 'OFF'}</span>
            </button>

            <button
              onClick={() => setShowBoundingBox(!showBoundingBox)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                showBoundingBox ? 'bg-violet-500/20 text-violet-300 border border-violet-400/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>BOXES</span>
            </button>

            <div className="h-4 w-[1px] bg-slate-800" />

            <button
              onClick={() => setZoomLevel(prev => Math.min(prev + 25, 200))}
              className="p-1 rounded text-slate-400 hover:text-cyan-400 transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <span className="text-[11px] font-mono text-cyan-400 px-1">{zoomLevel}%</span>
            <button
              onClick={() => setZoomLevel(prev => Math.max(prev - 25, 100))}
              className="p-1 rounded text-slate-400 hover:text-cyan-400 transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="relative w-full h-[400px] bg-slate-950 rounded-xl border border-sky-500/20 overflow-hidden flex items-center justify-center group">
          <div 
            className="relative transition-transform duration-300 flex items-center justify-center w-full h-full"
            style={{ transform: `scale(${zoomLevel / 100})` }}
          >
            <div className="w-full h-full bg-[#0b0f19] flex flex-col items-center justify-center p-6 relative">
              <div className="w-64 h-64 rounded-2xl bg-gradient-to-tr from-slate-900 via-slate-800 to-indigo-950 border border-slate-700/60 flex flex-col items-center justify-center relative shadow-2xl overflow-hidden">
                <div className="w-28 h-28 rounded-full bg-slate-700/50 border border-slate-600 flex items-center justify-center relative">
                  <div className="w-10 h-10 rounded-full bg-slate-600/40" />
                </div>
                <div className="w-44 h-20 mt-4 rounded-t-full bg-slate-700/40" />

                {showHeatmap && (
                  <div className="absolute inset-0 bg-gradient-to-tr from-red-600/40 via-amber-500/20 to-transparent mix-blend-color-dodge animate-pulse pointer-events-none" />
                )}

                {showBoundingBox && (
                  <>
                    <div className="absolute top-10 left-12 w-40 h-44 border-2 border-dashed border-red-500/80 rounded-lg shadow-[0_0_15px_rgba(255,42,95,0.5)] flex flex-col justify-between p-1">
                      <span className="text-[9px] font-mono font-bold text-red-400 bg-slate-950/80 px-1 rounded self-start">
                        ANOMALY #1 [94%]
                      </span>
                      <span className="text-[8px] font-mono text-red-400 bg-slate-950/80 px-1 rounded self-end">
                        FACE SWAP SEAM
                      </span>
                    </div>

                    <div className="absolute bottom-12 left-20 w-24 h-12 border border-amber-400 rounded shadow-[0_0_10px_rgba(245,158,11,0.5)] p-0.5">
                      <span className="text-[8px] font-mono text-amber-400 bg-slate-950/80 px-0.5 rounded">
                        LIP SYNC DISPARITY
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="absolute inset-0 bg-tech-grid opacity-25 pointer-events-none" />
            <div className="animate-scanline pointer-events-none" />
          </div>

          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[10px] font-mono text-slate-400 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
            <span>RES: <strong className="text-slate-200">{item.metadata.resolution || '3840 x 2160'}</strong></span>
            <span>FRAME: <strong className="text-cyan-400">#435 / 900</strong></span>
            <span>TIMESTAMP: <strong className="text-cyan-400">00:14.500</strong></span>
          </div>
        </div>
      </div>

      <div className="lg:col-span-5 glass-panel p-5 rounded-2xl flex flex-col gap-4">
        <div className="flex items-center gap-2 pb-2 border-b border-sky-500/15">
          <ShieldAlert className="w-5 h-5 text-red-400" />
          <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
            WHY WAS THIS FLAGGED?
          </h3>
        </div>

        <p className="text-xs font-mono text-slate-400">
          Multimodal neural models identified {item.evidenceItems.length} specific forensic anomalies in this target:
        </p>

        <div className="space-y-3 flex-1 overflow-y-auto max-h-[360px] pr-1">
          {item.evidenceItems.map((ev) => (
            <div
              key={ev.id}
              onClick={() => setSelectedEvidence(ev)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col gap-2 ${
                selectedEvidence?.id === ev.id
                  ? 'bg-gradient-to-r from-red-950/40 to-slate-900 border-red-500/50 shadow-[0_0_12px_rgba(255,42,95,0.15)]'
                  : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-mono text-xs font-bold text-slate-200">
                  {ev.title}
                </span>
                <span className={`px-2 py-0.5 text-[9px] font-mono font-bold rounded shrink-0 ${
                  ev.severity === 'high' ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                }`}>
                  {ev.severity.toUpperCase()} ({ev.confidence}%)
                </span>
              </div>

              <p className="text-xs font-mono text-slate-400 leading-relaxed">
                {ev.description}
              </p>

              {ev.location && (
                <div className="text-[10px] font-mono text-cyan-400/80 bg-slate-950/60 px-2 py-1 rounded border border-slate-800">
                  LOCATION: {ev.location}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
