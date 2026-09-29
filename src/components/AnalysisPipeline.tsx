import React from 'react';
import type { AnalysisStageStatus } from '../types/forensics';
import { 
  UploadCloud, 
  Hash, 
  FileSearch, 
  GitCommit, 
  Eye, 
  Volume2, 
  Clock, 
  Cpu,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  Zap,
  Layers,
  FileText
} from 'lucide-react';

export interface ExtendedStage {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  progress: number;
}

export const EXTENDED_STAGES: ExtendedStage[] = [
  { id: 'ingest', name: 'INGEST', icon: UploadCloud, progress: 8 },
  { id: 'hash', name: 'HASH', icon: Hash, progress: 16 },
  { id: 'metadata', name: 'METADATA', icon: FileSearch, progress: 24 },
  { id: 'provenance', name: 'PROVENANCE', icon: GitCommit, progress: 32 },
  { id: 'face-detection', name: 'FACE DETECTION', icon: Eye, progress: 40 },
  { id: 'visual', name: 'VISUAL ANALYSIS', icon: Layers, progress: 48 },
  { id: 'audio', name: 'AUDIO ANALYSIS', icon: Volume2, progress: 56 },
  { id: 'temporal', name: 'TEMPORAL ANALYSIS', icon: Clock, progress: 64 },
  { id: 'av-sync', name: 'A/V SYNC', icon: Zap, progress: 72 },
  { id: 'consensus', name: 'MODEL CONSENSUS', icon: ShieldCheck, progress: 80 },
  { id: 'risk-engine', name: 'RISK ENGINE', icon: Cpu, progress: 90 },
  { id: 'evidence', name: 'EVIDENCE GENERATION', icon: FileText, progress: 100 },
];

interface AnalysisPipelineProps {
  currentStageName: string;
  currentProgress: number;
  isAnalyzing: boolean;
}

export const AnalysisPipeline: React.FC<AnalysisPipelineProps> = ({
  currentStageName,
  currentProgress,
  isAnalyzing
}) => {
  return (
    <div className="w-full glass-panel p-6 rounded-2xl flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Cpu className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              REALISTIC FORENSIC ANALYSIS PIPELINE (12-STAGE SEQUENCE)
            </h3>
            <p className="text-xs font-mono text-slate-400">
              Multimodal ingestion, cryptographic hashing, neural feature extraction, and evidence synthesis
            </p>
          </div>
        </div>

        {isAnalyzing && (
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-400/40 text-cyan-300 font-mono text-xs animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>PROCESSING STAGE: {currentStageName}</span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="w-full space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400">
          <span>PIPELINE EXECUTION PROGRESS</span>
          <span className="text-cyan-400 font-bold">{currentProgress}%</span>
        </div>
        <div className="w-full h-2.5 rounded-full bg-slate-800/80 overflow-hidden p-0.5 border border-sky-500/20">
          <div 
            className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-sky-400 to-violet-500 shadow-[0_0_12px_#00f0ff] transition-all duration-300 ease-out"
            style={{ width: `${currentProgress}%` }}
          />
        </div>
      </div>

      {/* 12-Stage Visual Nodes Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 xl:grid-cols-12 gap-2.5 pt-2">
        {EXTENDED_STAGES.map((st, idx) => {
          const Icon = st.icon;
          const isDone = currentProgress >= st.progress;
          const isCurrent = isAnalyzing && currentProgress < st.progress && (idx === 0 || currentProgress >= EXTENDED_STAGES[idx - 1].progress);
          const stageStatus: AnalysisStageStatus = isDone ? 'COMPLETE' : isCurrent ? 'PROCESSING' : 'QUEUED';

          return (
            <div 
              key={st.id}
              className={`p-2.5 rounded-xl border flex flex-col items-center justify-between text-center gap-2 min-h-[90px] transition-all ${
                stageStatus === 'COMPLETE'
                  ? 'bg-cyan-950/40 border-cyan-500/40 text-cyan-300 shadow-[0_0_10px_rgba(0,240,255,0.1)]' 
                  : stageStatus === 'PROCESSING'
                  ? 'bg-violet-950/40 border-violet-400 text-violet-300 animate-pulse' 
                  : 'bg-slate-900/40 border-slate-800/80 text-slate-600'
              }`}
            >
              <div className="relative">
                <Icon className="w-4 h-4" />
                {stageStatus === 'COMPLETE' && (
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 absolute -top-1 -right-1 bg-slate-950 rounded-full" />
                )}
              </div>

              <span className="text-[9px] font-mono font-bold tracking-tight uppercase leading-tight line-clamp-2">
                {st.name}
              </span>

              <span className={`px-1 py-0.2 rounded text-[8px] font-mono font-bold ${
                stageStatus === 'COMPLETE' 
                  ? 'bg-emerald-500/20 text-emerald-400' 
                  : stageStatus === 'PROCESSING' 
                  ? 'bg-violet-500/20 text-violet-300' 
                  : 'bg-slate-800 text-slate-500'
              }`}>
                {stageStatus}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
