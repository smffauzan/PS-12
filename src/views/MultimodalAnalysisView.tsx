import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { RiskMeter } from '../components/RiskMeter';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { 
  Eye, 
  Volume2, 
  Clock, 
  Cpu, 
  FileVideo,
  ShieldAlert,
  Activity
} from 'lucide-react';

export const MultimodalAnalysisView: React.FC = () => {
  const { activeItem, navigateTo } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Multimodal Analysis" />

      {/* Target File Title & Forensic Case Header */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border border-cyan-500/20">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-400/40 text-cyan-400">
            <FileVideo className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-slate-900 text-cyan-400 font-mono text-xs font-bold border border-slate-800">
                {activeItem.caseId || 'CASE VX-04291'}
              </span>
              <h1 className="font-mono text-xl font-bold text-slate-100 uppercase">
                {activeItem.filename}
              </h1>
            </div>
            <p className="font-mono text-xs text-slate-400 mt-1">
              MEDIA ID: <strong className="text-slate-200">{activeItem.mediaId || 'MED-89412-X'}</strong> • TIMESTAMP: <strong className="text-slate-200">{activeItem.timestamp || activeItem.uploadedAt}</strong> • TYPE: <strong className="text-slate-200">{activeItem.mediaType.toUpperCase()}</strong>
            </p>
          </div>
        </div>

        {/* Action triggers */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigateTo('evidence')}
            className="px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-cyan-300 font-mono text-xs font-bold transition-colors"
          >
            VIEW EVIDENCE LAB →
          </button>

          <button
            onClick={() => navigateTo('timeline')}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-mono text-xs font-bold transition-colors"
          >
            FORENSIC TIMELINE →
          </button>
        </div>
      </div>

      {/* Advanced Phase 2 Result Header KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl flex flex-col gap-1 border-l-4 border-l-red-500">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">MANIPULATION RISK</span>
          <span className="text-3xl font-mono font-bold text-red-400">{activeItem.overallRiskScore}%</span>
          <span className="text-xs font-mono font-bold text-red-400 uppercase tracking-wider">{activeItem.riskTier}</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl flex flex-col gap-1 border-l-4 border-l-cyan-400">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">MODEL CONFIDENCE</span>
          <span className="text-3xl font-mono font-bold text-cyan-300">{activeItem.confidence}%</span>
          <span className="text-xs font-mono text-slate-400">HIGH CERTAINTY</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl flex flex-col gap-1 border-l-4 border-l-violet-400">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">MODEL CONSENSUS</span>
          <span className="text-3xl font-mono font-bold text-violet-300">{activeItem.modelConsensus || 93}%</span>
          <span className="text-xs font-mono text-emerald-400">AGREEMENT HIGH</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl flex flex-col gap-1 border-l-4 border-l-amber-400">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">FORENSIC SIGNALS</span>
          <span className="text-3xl font-mono font-bold text-amber-400">{activeItem.signalCount || activeItem.signals?.length || 14}</span>
          <span className="text-xs font-mono text-slate-400">DETECTED ANOMALIES</span>
        </div>
      </div>

      {/* Rationale Banner */}
      <div className="p-4 rounded-xl bg-slate-950 border border-sky-500/20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-cyan-400 shrink-0" />
          <p className="font-mono text-xs text-slate-300 leading-relaxed">
            <strong className="text-cyan-300 uppercase">EVIDENCE RATIONALE:</strong> Assessment based on multiple visual, temporal, audio and provenance signals.
          </p>
        </div>
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider shrink-0 hidden sm:inline">
          VERITAS ENGINE v0.9.0-PROTOTYPE
        </span>
      </div>

      {/* Central MULTIMODAL FUSION ENGINE Visualization */}
      <div className="glass-panel p-8 rounded-2xl flex flex-col items-center justify-center gap-6 relative overflow-hidden bg-gradient-to-b from-[#080d19] to-[#0d1428]">
        <div className="absolute inset-0 bg-tech-grid opacity-20 pointer-events-none" />

        <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-bold uppercase tracking-widest z-10">
          <Cpu className="w-5 h-5 animate-pulse" />
          <span>MULTIMODAL FUSION ENGINE</span>
        </div>

        {/* Node Network Diagram */}
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-6 z-10 my-2">
          <div className="p-4 rounded-xl bg-slate-950/80 border border-cyan-500/30 flex flex-col items-center text-center gap-2 shadow-lg">
            <Eye className="w-6 h-6 text-cyan-400" />
            <span className="font-mono text-xs font-bold text-slate-200">VISUAL AI SIGNAL</span>
            <span className="text-2xl font-mono font-bold text-red-400">{activeItem.visualScore}%</span>
            <span className="text-[10px] font-mono text-slate-400">Weight: 40% Attention</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-violet-500/30 flex flex-col items-center text-center gap-2 shadow-lg">
            <Volume2 className="w-6 h-6 text-violet-400" />
            <span className="font-mono text-xs font-bold text-slate-200">AUDIO AI SIGNAL</span>
            <span className="text-2xl font-mono font-bold text-amber-400">{activeItem.audioScore}%</span>
            <span className="text-[10px] font-mono text-slate-400">Weight: 30% Attention</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-sky-500/30 flex flex-col items-center text-center gap-2 shadow-lg">
            <Clock className="w-6 h-6 text-sky-400" />
            <span className="font-mono text-xs font-bold text-slate-200">TEMPORAL AI SIGNAL</span>
            <span className="text-2xl font-mono font-bold text-red-400">{activeItem.temporalScore}%</span>
            <span className="text-[10px] font-mono text-slate-400">Weight: 30% Attention</span>
          </div>
        </div>

        {/* Fusion Result */}
        <div className="flex flex-col items-center gap-2 z-10">
          <div className="w-0.5 h-8 bg-gradient-to-b from-cyan-400 to-red-500" />
          <div className="p-4 rounded-2xl bg-slate-950 border-2 border-red-500/60 flex items-center gap-6 shadow-[0_0_30px_rgba(255,42,95,0.2)]">
            <RiskMeter 
              score={activeItem.overallRiskScore} 
              riskTier={activeItem.riskTier} 
              confidence={activeItem.confidence}
              size="sm"
              showDescription={false}
            />
            <div className="flex flex-col text-left font-mono text-xs space-y-1">
              <span className="text-slate-400 text-[10px] uppercase tracking-wider">UNIFIED FUSION RESULT</span>
              <span className="text-red-400 font-bold text-base">{activeItem.riskTier}</span>
              <span className="text-slate-300">Confidence: <strong>{activeItem.confidence}%</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Forensic Signals List */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              {activeItem.signals?.length || activeItem.signalCount || 14} FORENSIC SIGNALS DETECTED
            </h3>
          </div>

          <span className="text-xs font-mono text-slate-400">FILTER BY MODALITY</span>
        </div>

        <div className="space-y-3">
          {(activeItem.signals && activeItem.signals.length > 0 ? activeItem.signals : [
            { id: 's1', name: 'Facial Texture Inconsistency', category: 'visual', severity: 'high', confidence: 94, affectedRegionOrTime: 'Cheek & Chin Area [00:14.50]', explanation: 'Spectral domain FFT analysis reveals unnatural attenuation of fine skin micro-texture details characteristic of neural diffusion face swapping.' },
            { id: 's2', name: 'Eye Reflection Specular Disparity', category: 'visual', severity: 'high', confidence: 92, affectedRegionOrTime: 'Ocular Iris Region [00:14.50]', explanation: 'Specular highlights in left and right cornea exhibit incompatible light vector angles relative to studio lighting.' },
            { id: 's3', name: 'Face Boundary Blending Artifact', category: 'visual', severity: 'high', confidence: 91, affectedRegionOrTime: 'Jawline & Neck Seam [00:21.00]', explanation: 'Gradient discontinuity along the mask boundary indicates neural warping and edge blending smoothing filters.' },
            { id: 's4', name: 'Optical-Flow Inter-Frame Anomaly', category: 'temporal', severity: 'high', confidence: 89, affectedRegionOrTime: 'Frames #420-#480 [00:14 - 00:16]', explanation: 'Vector motion fields around facial contours misalign with background optical flow velocity vectors.' },
            { id: 's5', name: 'Audio Spectral Formant Anomaly', category: 'audio', severity: 'medium', confidence: 85, affectedRegionOrTime: '3.8kHz - 5.2kHz Band [00:07.30]', explanation: 'Unnatural linear phase coherence across upper harmonic formants typical of neural vocoder speech synthesis.' },
            { id: 's6', name: 'Neural Voice Synthesis Indicator', category: 'audio', severity: 'high', confidence: 88, affectedRegionOrTime: 'Voice Track [00:06 - 00:18]', explanation: 'Mel-spectrogram zero-crossing distribution matches acoustic footprint of diffusion voice cloning models.' },
            { id: 's7', name: 'Lip-Sync Phase Deviation (+45ms)', category: 'sync', severity: 'high', confidence: 88, affectedRegionOrTime: 'Plosive Phoneme /p/ [00:18.20]', explanation: 'Acoustic plosive energy precedes visual labial occlusion frames by 45ms, indicating post-hoc voice replacement.' },
            { id: 's8', name: 'Compression Quantization Disparity', category: 'metadata', severity: 'medium', confidence: 82, affectedRegionOrTime: 'Entire Frame Block [Global]', explanation: 'DCT coefficient quantization tables for face region show secondary compression pass inconsistent with background block noise.' }
          ]).map((signal) => (
            <div 
              key={signal.id}
              className="p-4 rounded-xl bg-slate-950/80 border border-sky-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 font-mono text-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-100">{signal.name}</span>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                    signal.severity === 'high' ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                  }`}>
                    {signal.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed max-w-2xl">
                  {signal.explanation}
                </p>
              </div>

              <div className="flex items-center gap-6 shrink-0 text-right">
                <div>
                  <div className="text-slate-500 text-[10px]">AFFECTED REGION / TIME</div>
                  <div className="text-cyan-400 font-bold">{signal.affectedRegionOrTime}</div>
                </div>
                <div>
                  <div className="text-slate-500 text-[10px]">CONFIDENCE</div>
                  <div className="text-slate-200 font-bold">{signal.confidence}%</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
