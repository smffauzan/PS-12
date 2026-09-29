import React, { useState, useEffect } from 'react';
import { useForensic } from '../context/ForensicContext';
import { 
  Radio, 
  Camera, 
  Play, 
  Pause, 
  Clock
} from 'lucide-react';

export const LiveForensicsView: React.FC = () => {
  const { showToast } = useForensic();
  const [isPlaying, setIsPlaying] = useState(true);
  const [showMesh, setShowMesh] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [liveRisk, setLiveRisk] = useState(84);
  const [fps, setFps] = useState(60);
  const [logs, setLogs] = useState<{ time: string; msg: string; risk: number }[]>([
    { time: '14:52:01', msg: 'Face detection locked on Subject #1 [Mesh ID: #4812]', risk: 18 },
    { time: '14:52:04', msg: 'Optical flow variance anomaly detected in eye reflection', risk: 68 },
    { time: '14:52:08', msg: 'HIGH RISK: Lip-sync phoneme mismatch (+42ms lag)', risk: 84 },
  ]);

  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      const jitter = Math.floor(Math.random() * 7) - 3;
      setLiveRisk(prev => Math.min(96, Math.max(70, prev + jitter)));
      setFps(Math.floor(Math.random() * 3) + 59);

      if (Math.random() > 0.6) {
        const timeStr = new Date().toLocaleTimeString();
        const events = [
          'Inter-frame spatial blurring detected along jaw perimeter',
          'Spectral pitch contour harmonic anomaly in 4.2kHz band',
          'Eyeblink frequency rate below natural human baseline',
          'Temporal luminance inconsistency between background and subject'
        ];
        const randomEv = events[Math.floor(Math.random() * events.length)];
        setLogs(prev => [{ time: timeStr, msg: randomEv, risk: Math.floor(Math.random() * 20) + 75 }, ...prev.slice(0, 10)]);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [isPlaying]);

  const handleCaptureSnapshot = () => {
    showToast('Live forensic frame snapshot captured and saved to Evidence Lab!');
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-red-500 animate-pulse" />
            <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
              REALTIME LIVE FORENSIC STREAM
            </h1>
          </div>
          <p className="font-mono text-xs text-slate-400">
            Sub-millisecond frame-by-frame face mesh tracking, optical flow analysis & live speech synthesis authentication
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              isPlaying 
                ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse' 
                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
            }`}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>{isPlaying ? 'LIVE STREAM ACTIVE' : 'STREAM PAUSED'}</span>
          </button>

          <button
            onClick={handleCaptureSnapshot}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-cyan-300 font-mono text-xs font-bold transition-colors"
          >
            <Camera className="w-4 h-4" />
            <span>CAPTURE SNAPSHOT</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 glass-panel p-5 rounded-2xl flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
              <span>SOURCE: <strong className="text-cyan-400">CAMERA NODE #01 (LIVE UDP STREAM)</strong></span>
            </div>

            <div className="flex items-center gap-2 bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs font-mono">
              <button
                onClick={() => setShowMesh(!showMesh)}
                className={`px-2.5 py-1 rounded transition-colors ${showMesh ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400'}`}
              >
                FACE MESH {showMesh ? 'ON' : 'OFF'}
              </button>

              <button
                onClick={() => setShowHeatmap(!showHeatmap)}
                className={`px-2.5 py-1 rounded transition-colors ${showHeatmap ? 'bg-violet-500/20 text-violet-300 border border-violet-500/40' : 'text-slate-400'}`}
              >
                HEATMAP {showHeatmap ? 'ON' : 'OFF'}
              </button>
            </div>
          </div>

          <div className="relative w-full h-[450px] bg-slate-950 rounded-xl border border-sky-500/20 overflow-hidden flex items-center justify-center">
            <div className="w-full h-full bg-[#080c16] flex items-center justify-center relative">
              <div className="w-72 h-72 rounded-3xl bg-gradient-to-tr from-slate-900 via-indigo-950 to-slate-900 border border-slate-700/60 flex flex-col items-center justify-center relative shadow-2xl overflow-hidden">
                <div className="w-32 h-32 rounded-full bg-slate-700/40 border border-cyan-500/40 flex items-center justify-center relative">
                  {showMesh && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-24 h-24 border border-cyan-400/60 rounded-full animate-ping opacity-30" />
                      <div className="w-16 h-16 border border-violet-400/60 rounded-full" />
                      <div className="absolute top-6 left-6 w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#00f0ff]" />
                      <div className="absolute top-6 right-6 w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#00f0ff]" />
                      <div className="absolute bottom-8 w-2 h-1 rounded bg-red-400 shadow-[0_0_6px_#ff2a5f]" />
                    </div>
                  )}
                </div>
                <div className="w-52 h-24 mt-4 rounded-t-full bg-slate-700/30" />

                {showHeatmap && (
                  <div className="absolute inset-0 bg-gradient-to-tr from-red-600/50 via-amber-500/30 to-transparent mix-blend-screen pointer-events-none" />
                )}

                <div className="absolute top-8 left-12 w-48 h-52 border-2 border-red-500/80 rounded-lg shadow-[0_0_15px_rgba(255,42,95,0.4)] flex flex-col justify-between p-2">
                  <div className="flex items-center justify-between text-[9px] font-mono font-bold text-red-400 bg-slate-950/90 px-1.5 py-0.5 rounded border border-red-500/40">
                    <span>LIVE RISK: {liveRisk}%</span>
                    <span>ID: #4812</span>
                  </div>
                  <div className="text-[8px] font-mono text-red-400 bg-slate-950/90 px-1 py-0.5 rounded self-end">
                    SYNTHETIC SEAM DETECTED
                  </div>
                </div>
              </div>

              <div className="absolute inset-0 bg-tech-grid opacity-25 pointer-events-none" />
              {isPlaying && <div className="animate-scanline pointer-events-none" />}
            </div>

            <div className="absolute top-3 left-3 px-3 py-1 rounded-md bg-slate-950/90 border border-red-500/40 text-red-400 text-xs font-mono font-bold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
              <span>LIVE RECOGNITION ACTIVE</span>
            </div>

            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[11px] font-mono text-slate-300 bg-slate-950/90 px-4 py-2 rounded-lg border border-slate-800">
              <div className="flex items-center gap-4">
                <span>FPS: <strong className="text-cyan-400">{fps}</strong></span>
                <span>LATENCY: <strong className="text-cyan-400">14 ms</strong></span>
              </div>
              <div className="flex items-center gap-4">
                <span>FACE TRACKING: <strong className="text-emerald-400">LOCKED (100%)</strong></span>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-6">
          <div className="glass-panel p-5 rounded-2xl flex flex-col items-center justify-center text-center">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">
              LIVE SYNTHETIC RISK METER
            </span>
            <div className="text-5xl font-mono font-extrabold text-red-400 my-2 shadow-sm">
              {liveRisk}%
            </div>
            <div className="px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 font-mono text-xs font-bold uppercase">
              HIGH MANIPULATION RISK
            </div>

            <div className="w-full space-y-2 mt-4 pt-4 border-t border-slate-800 font-mono text-xs text-slate-400">
              <div className="flex justify-between"><span>VISUAL SCORE:</span> <strong className="text-red-400">89%</strong></div>
              <div className="flex justify-between"><span>TEMPORAL SCORE:</span> <strong className="text-amber-400">78%</strong></div>
              <div className="flex justify-between"><span>AUDIO SCORE:</span> <strong className="text-red-400">84%</strong></div>
              <div className="flex justify-between"><span>A/V SYNC SCORE:</span> <strong className="text-red-400">81%</strong></div>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-sky-500/15">
              <h3 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                REALTIME ANOMALY LOG
              </h3>
              <span className="text-[10px] font-mono text-cyan-400">STREAMING</span>
            </div>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {logs.map((log, idx) => (
                <div key={idx} className="p-2.5 rounded bg-slate-950/80 border border-slate-800/80 flex flex-col gap-1 font-mono text-[11px]">
                  <div className="flex items-center justify-between text-slate-500">
                    <span>{log.time}</span>
                    <span className={log.risk >= 75 ? 'text-red-400 font-bold' : 'text-amber-400'}>RISK: {log.risk}%</span>
                  </div>
                  <p className="text-slate-300 leading-tight">{log.msg}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
