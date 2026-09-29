import React from 'react';
import type { ForensicMediaItem, ModelOutput } from '../types/forensics';
import { ShieldCheck, Cpu, AlertOctagon } from 'lucide-react';

interface ModelConsensusProps {
  item: ForensicMediaItem;
}

export const ModelConsensus: React.FC<ModelConsensusProps> = ({ item }) => {
  const models: ModelOutput[] = item.modelOutputs.length > 0 ? item.modelOutputs : [
    { id: 'm-1', name: 'VERITAS Spatial Deepfake Net (EfficientNet-B7)', category: 'Visual AI', riskScore: 91, confidence: 94, status: 'High Anomaly', description: 'Deep spatial convolution layers detected synthetic blending seam.', latencyMs: 38 },
    { id: 'm-2', name: 'VERITAS Video-Swin-3D Temporal Consistency Net', category: 'Temporal AI', riskScore: 84, confidence: 89, status: 'High Anomaly', description: 'Transformer optical flow tracking flagged inter-frame jitter.', latencyMs: 44 },
    { id: 'm-3', name: 'VERITAS Wav2Vec2 Synthesizer Voice Authenticator', category: 'Audio AI', riskScore: 73, confidence: 85, status: 'Moderate Anomaly', description: 'Spectral formant matched neural voice cloning signature dataset.', latencyMs: 29 },
    { id: 'm-4', name: 'A/V Sync Phoneme Alignment Transformer', category: 'Multi-Model', riskScore: 81, confidence: 91, status: 'High Anomaly', description: 'Visual lip keypoints misaligned with acoustic plosive timestamps.', latencyMs: 22 },
    { id: 'm-5', name: 'C2PA Manifest Integrity Validator', category: 'Provenance', riskScore: 95, confidence: 99, status: 'Unverified', description: 'No valid cryptographic signature found in container headers.', latencyMs: 9 }
  ];

  const totalRisk = models.reduce((acc, m) => acc + m.riskScore, 0);
  const consensusScore = Math.round(totalRisk / models.length);

  const scores = models.map(m => m.riskScore);
  const maxDiff = Math.max(...scores) - Math.min(...scores);
  const isInconclusive = maxDiff > 45;

  return (
    <div className="w-full glass-panel p-6 rounded-2xl flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              MULTI-MODEL NEURAL CONSENSUS ENGINE
            </h3>
            <p className="text-xs font-mono text-slate-400">
              Ensemble voting & cross-modality agreement analysis across 5 independent AI detectors
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400">CONSENSUS SCORE:</span>
          <span className="px-3 py-1 rounded bg-cyan-500/20 text-cyan-300 font-mono text-sm font-bold border border-cyan-400/40">
            {consensusScore}%
          </span>
        </div>
      </div>

      {isInconclusive && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/40 text-amber-300 flex items-center gap-3 font-mono text-xs animate-pulse">
          <AlertOctagon className="w-5 h-5 text-amber-400 shrink-0" />
          <span>INCONCLUSIVE — ADDITIONAL VERIFICATION RECOMMENDED (High model disagreement detected)</span>
        </div>
      )}

      <div className="space-y-3">
        {models.map((model) => (
          <div 
            key={model.id}
            className="p-4 rounded-xl bg-slate-950/80 border border-sky-500/20 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-cyan-400">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <div className="font-mono text-xs font-bold text-slate-200">
                  {model.name}
                </div>
                <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                  {model.description}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-6 font-mono text-xs shrink-0 w-full lg:w-auto justify-between lg:justify-end border-t lg:border-t-0 pt-2 lg:pt-0 border-slate-800">
              <span className="text-slate-400">LATENCY: <strong className="text-slate-200">{model.latencyMs}ms</strong></span>
              <span className="text-slate-400">CONF: <strong className="text-cyan-300">{model.confidence}%</strong></span>
              
              <span className={`px-2.5 py-1 rounded font-bold ${
                model.riskScore >= 75 ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              }`}>
                {model.riskScore}% {model.status.toUpperCase()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
