import React, { useState } from 'react';
import { useForensic } from '../context/ForensicContext';
import { AnalysisPipeline } from '../components/AnalysisPipeline';
import { 
  UploadCloud, 
  FileVideo, 
  FileAudio, 
  FileImage, 
  Lock, 
  Sparkles, 
  Play,
  Terminal,
  FolderKanban
} from 'lucide-react';
import { INITIAL_DEMO_CASES } from '../data/demoData';

export const MediaIntakeView: React.FC = () => {
  const { startAnalysis, isAnalyzing, analysisProgress, currentPipelineStage, analysisLogs } = useForensic();
  const [selectedPreset, setSelectedPreset] = useState(INITIAL_DEMO_CASES[0]);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      startAnalysis(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      startAnalysis(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="flex flex-col gap-1">
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
          MEDIA INTAKE & PRE-FORENSICS INGESTION
        </h1>
        <p className="font-mono text-xs text-slate-400">
          Upload media files for automated cryptographic hash generation, metadata parsing, and multimodal AI analysis.
        </p>
      </div>

      <div 
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={`relative glass-panel p-10 rounded-2xl border-2 border-dashed transition-all flex flex-col items-center justify-center text-center gap-4 group ${
          isDragOver 
            ? 'border-cyan-400 bg-cyan-950/30 scale-[1.01] shadow-[0_0_30px_rgba(0,240,255,0.2)]' 
            : 'border-sky-500/30 hover:border-cyan-400/60 bg-slate-950/60'
        }`}
      >
        <input 
          type="file" 
          accept="image/*,video/*,audio/*"
          onChange={handleFileSelect}
          className="absolute inset-0 opacity-0 cursor-pointer z-20"
        />

        <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-400/40 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform shadow-[0_0_15px_rgba(0,240,255,0.15)]">
          <UploadCloud className="w-8 h-8" />
        </div>

        <div className="space-y-1 z-10">
          <h3 className="font-mono text-base font-bold text-slate-100 uppercase tracking-wider">
            DROP MEDIA FOR FORENSIC ANALYSIS
          </h3>
          <p className="font-mono text-xs text-slate-400">
            Drag and drop target file or click anywhere to browse local filesystem
          </p>
        </div>

        <div className="flex items-center gap-6 pt-2 font-mono text-xs text-slate-400 z-10">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-900 border border-slate-800">
            <FileImage className="w-4 h-4 text-cyan-400" />
            <span>IMAGE (PNG, JPG, WEBP, RAW)</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-900 border border-slate-800">
            <FileVideo className="w-4 h-4 text-cyan-400" />
            <span>VIDEO (MP4, MOV, AVI, WEBM)</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-900 border border-slate-800">
            <FileAudio className="w-4 h-4 text-violet-400" />
            <span>AUDIO (WAV, MP3, AAC, FLAC)</span>
          </div>
        </div>
      </div>

      <div className="glass-panel p-6 rounded-2xl flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            PRESET SAMPLE INVESTIGATIONS (1-CLICK LOAD)
          </h3>
          <span className="text-[11px] font-mono text-slate-400">SELECT SAMPLE TO RUN PIPELINE</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {INITIAL_DEMO_CASES.slice(0, 4).map((sample) => (
            <div
              key={sample.id}
              onClick={() => {
                setSelectedPreset(sample);
                startAnalysis(sample);
              }}
              className={`p-4 rounded-xl border flex flex-col gap-3 cursor-pointer transition-all ${
                selectedPreset.id === sample.id
                  ? 'bg-cyan-950/40 border-cyan-400 shadow-[0_0_15px_rgba(0,240,255,0.15)]'
                  : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase bg-slate-900 text-cyan-400 border border-slate-800">
                  {sample.caseId}
                </span>
                <span className="text-[10px] font-mono text-slate-400">{sample.fileSize}</span>
              </div>

              <div className="font-mono text-xs font-bold text-slate-200 truncate">
                {sample.filename}
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-800">
                <span>RISK TIER:</span>
                <span className={sample.riskTier === 'HIGH RISK' ? 'text-red-400 font-bold' : 'text-emerald-400 font-bold'}>
                  {sample.overallRiskScore}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedPreset && (
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            <div className="md:col-span-8 space-y-3 font-mono text-xs">
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <FolderKanban className="w-4 h-4 text-cyan-400" />
                SELECTED FILE INGESTION SPECIFICATION ({selectedPreset.caseId})
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div><span className="text-slate-500">FILENAME:</span> <p className="text-slate-200 font-bold truncate">{selectedPreset.filename}</p></div>
                <div><span className="text-slate-500">FILE SIZE:</span> <p className="text-slate-200">{selectedPreset.fileSize}</p></div>
                <div><span className="text-slate-500">RESOLUTION:</span> <p className="text-slate-200">{selectedPreset.metadata.resolution || 'N/A'}</p></div>
                <div><span className="text-slate-500">DURATION:</span> <p className="text-slate-200">{selectedPreset.metadata.duration || 'N/A'}</p></div>
                <div><span className="text-slate-500">CODEC:</span> <p className="text-slate-200">{selectedPreset.metadata.codec}</p></div>
                <div><span className="text-slate-500">C2PA PROVENANCE:</span> <p className="text-amber-400 font-bold">{selectedPreset.c2paStatus}</p></div>
              </div>

              <div className="pt-2">
                <span className="text-slate-500">SHA-256 GENERATED:</span>
                <p className="text-cyan-400 text-[11px] break-all bg-slate-950 p-2 rounded border border-slate-800 mt-1">
                  {selectedPreset.sha256}
                </p>
              </div>
            </div>

            <div className="md:col-span-4 flex flex-col items-center justify-center p-4 border-t md:border-t-0 md:border-l border-slate-800 gap-4">
              <button
                disabled={isAnalyzing}
                onClick={() => startAnalysis(selectedPreset)}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-400 hover:from-cyan-400 hover:to-sky-300 text-slate-950 font-mono text-xs font-bold transition-all shadow-[0_0_20px_rgba(0,240,255,0.3)] flex items-center justify-center gap-2 hover:scale-105 disabled:opacity-50"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>START FORENSIC ANALYSIS</span>
              </button>

              <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400 text-center">
                <Lock className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span>Temporary analysis media is processed securely and can be deleted after analysis.</span>
              </div>
            </div>
          </div>

          <AnalysisPipeline 
            currentStageName={currentPipelineStage}
            currentProgress={analysisProgress}
            isAnalyzing={isAnalyzing}
          />

          <div className="glass-panel p-5 rounded-2xl space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-sky-500/15">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <h4 className="font-bold text-slate-200 uppercase tracking-wider">
                  LIVE ANALYSIS ACTIVITY STREAM
                </h4>
              </div>
              <span className="text-[10px] text-cyan-400 font-bold">STREAMING REALTIME</span>
            </div>

            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {analysisLogs.map((log, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2 rounded bg-slate-950/80 border border-slate-800/60">
                  <span className="text-slate-500 font-bold shrink-0">{log.timestamp}</span>
                  <span className="text-cyan-300 flex-1">{log.message}</span>
                  <span className="text-emerald-400 font-bold text-[10px]">EXEC OK</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
