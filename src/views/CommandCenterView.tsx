import React, { useState, useRef } from 'react';
import { useForensic } from '../context/ForensicContext';
import { generateForensicExplanation } from '../services/explanationEngine';
import { uploadAndAnalyzeMedia } from '../services/api/analysisApi';
import type { ForensicCase, MediaType } from '../types/forensics';
import { 
  UploadCloud, 
  Image as ImageIcon, 
  Video as VideoIcon, 
  Volume2, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  HelpCircle, 
  ArrowRight, 
  RotateCcw, 
  Search, 
  FileText, 
  Loader2 
} from 'lucide-react';

const ACCEPTED_TYPES: Record<MediaType, { extensions: string; mime: string; label: string }> = {
  image: {
    extensions: 'JPG, JPEG, PNG, WEBP',
    mime: 'image/jpeg,image/png,image/webp,image/jpg',
    label: 'Images'
  },
  video: {
    extensions: 'MP4, MOV, WEBM, MKV, M4V',
    mime: 'video/mp4,video/quicktime,video/webm,video/x-matroska,video/x-m4v',
    label: 'Videos'
  },
  audio: {
    extensions: 'WAV, MP3, M4A, AAC',
    mime: 'audio/wav,audio/mpeg,audio/mp3,audio/x-m4a,audio/aac',
    label: 'Audio'
  }
};

const ANALYSIS_STAGES = [
  'Inspecting visual signals...',
  'Analyzing temporal patterns...',
  'Analyzing audio signals...',
  'Evaluating forensic evidence...'
];

export const CommandCenterView: React.FC = () => {
  const { setActiveItem, navigateTo } = useForensic();

  const [selectedMediaType, setSelectedMediaType] = useState<MediaType>('video');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStageIdx, setAnalysisStageIdx] = useState(0);
  const [analyzedCase, setAnalyzedCase] = useState<ForensicCase | null>(null);
  const [isSimulated, setIsSimulated] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    setErrorMsg(null);
    setSelectedFile(file);

    // Auto-detect media type if file extension matches another tab
    if (file.type.startsWith('image/')) {
      setSelectedMediaType('image');
    } else if (file.type.startsWith('audio/')) {
      setSelectedMediaType('audio');
    } else if (file.type.startsWith('video/')) {
      setSelectedMediaType('video');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setErrorMsg(null);
    setAnalysisStageIdx(0);

    // Stage progression interval
    const stageTimer = setInterval(() => {
      setAnalysisStageIdx(prev => (prev + 1) % ANALYSIS_STAGES.length);
    }, 500);

    try {
      const result = await uploadAndAnalyzeMedia(selectedFile);
      clearInterval(stageTimer);
      if (result) {
        setAnalyzedCase(result);
        setActiveItem(result);
        setIsSimulated(result.modelVersion?.includes('DEMO') || false);
      }
    } catch (err: any) {
      clearInterval(stageTimer);
      const msg = err?.message || 'ANALYSIS ERROR: Media analysis request failed.';
      setErrorMsg(msg);
      setAnalyzedCase(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setAnalyzedCase(null);
    setIsSimulated(false);
    setErrorMsg(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Explanation derived from actual backend results
  const resultCase = analyzedCase;
  const explanation = resultCase ? generateForensicExplanation(resultCase) : null;

  const getRiskClassification = (caseItem: ForensicCase) => {
    const score = caseItem.overallRiskScore;
    const tier = caseItem.riskTier;

    if (tier === 'INCONCLUSIVE' || score === null) {
      return {
        label: 'INCONCLUSIVE',
        textColor: 'text-slate-400',
        badgeBg: 'bg-slate-800/80 text-slate-300 border-slate-700',
        statement: 'The available evidence is insufficient to determine manipulation risk reliably.',
        icon: HelpCircle
      };
    }
    if (score >= 80 || tier === 'HIGH RISK') {
      return {
        label: 'HIGH MANIPULATION RISK',
        textColor: 'text-red-400',
        badgeBg: 'bg-red-500/15 text-red-400 border-red-500/40 shadow-[0_0_15px_rgba(239,68,68,0.2)]',
        statement: 'Multiple forensic signals indicate elevated risk of AI-generated or manipulated media.',
        icon: ShieldAlert
      };
    }
    if (score >= 45 || tier === 'MEDIUM RISK') {
      return {
        label: 'MEDIUM MANIPULATION RISK',
        textColor: 'text-amber-400',
        badgeBg: 'bg-amber-500/15 text-amber-400 border-amber-500/40',
        statement: 'Some forensic signals indicate possible synthetic or manipulated media.',
        icon: AlertTriangle
      };
    }
    return {
      label: 'LOW MANIPULATION RISK',
      textColor: 'text-emerald-400',
      badgeBg: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40',
      statement: 'No strong synthetic-media signals were detected by the available analysis.',
      icon: CheckCircle2
    };
  };

  return (
    <div className="w-full max-w-3xl mx-auto py-6 px-4 sm:px-6 space-y-10 animate-fadeIn">
      {/* 1. CLEAN HERO HEADER */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 font-mono text-xs font-semibold tracking-wide">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>VERITAS AI • Detect. Explain. Verify.</span>
        </div>

        <h1 className="font-mono text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
          AI-GENERATED MEDIA DETECTOR
        </h1>

        <p className="font-sans text-sm sm:text-base text-slate-400 max-w-xl mx-auto leading-relaxed">
          Analyze images, videos, and audio for signals associated with AI-generated or manipulated media.
        </p>
      </div>

      {/* 2. MAIN WORKSPACE: UPLOAD OR RESULT */}
      {!resultCase && !isAnalyzing && (
        <div className="space-y-6">
          {/* Media Type Selection Tabs */}
          <div className="flex items-center justify-center gap-2 p-1.5 rounded-2xl bg-slate-900/90 border border-slate-800 max-w-md mx-auto shadow-inner">
            {(['image', 'video', 'audio'] as MediaType[]).map((type) => {
              const isSelected = selectedMediaType === type;
              const Icon = type === 'image' ? ImageIcon : type === 'video' ? VideoIcon : Volume2;
              return (
                <button
                  key={type}
                  onClick={() => {
                    setSelectedMediaType(type);
                    setSelectedFile(null);
                  }}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-mono text-xs font-bold transition-all ${
                    isSelected
                      ? 'bg-gradient-to-r from-cyan-500 to-sky-400 text-slate-950 shadow-[0_0_12px_rgba(0,240,255,0.25)]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="uppercase">{type}</span>
                </button>
              );
            })}
          </div>

          {/* Large Upload Box */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => !selectedFile && fileInputRef.current?.click()}
            className={`relative rounded-3xl p-8 sm:p-12 border-2 border-dashed transition-all flex flex-col items-center justify-center text-center gap-5 cursor-pointer ${
              isDragOver
                ? 'border-cyan-400 bg-cyan-950/20 shadow-[0_0_25px_rgba(0,240,255,0.15)] scale-[1.01]'
                : selectedFile
                ? 'border-cyan-500/40 bg-slate-950/80'
                : 'border-slate-800 hover:border-slate-700 bg-slate-950/50 hover:bg-slate-900/40 shadow-xl'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_TYPES[selectedMediaType].mime}
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileSelect(e.target.files[0]);
                }
              }}
            />

            {!selectedFile ? (
              <>
                <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400 shadow-[0_0_20px_rgba(0,240,255,0.15)]">
                  <UploadCloud className="w-8 h-8" />
                </div>

                <div className="space-y-1.5">
                  <h3 className="font-mono text-base sm:text-lg font-bold text-slate-200">
                    Upload {ACCEPTED_TYPES[selectedMediaType].label}
                  </h3>
                  <p className="font-sans text-xs sm:text-sm text-slate-400">
                    Drag & drop your file here, or <span className="text-cyan-400 font-semibold underline underline-offset-4">browse files</span>
                  </p>
                </div>

                <div className="text-[11px] font-mono text-slate-500 px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
                  Supported formats: {ACCEPTED_TYPES[selectedMediaType].extensions}
                </div>
              </>
            ) : (
              <div className="w-full max-w-md space-y-4 text-center">
                <div className="w-14 h-14 rounded-2xl bg-cyan-500/15 border border-cyan-400/40 flex items-center justify-center text-cyan-300 mx-auto">
                  {selectedMediaType === 'image' ? (
                    <ImageIcon className="w-7 h-7" />
                  ) : selectedMediaType === 'video' ? (
                    <VideoIcon className="w-7 h-7" />
                  ) : (
                    <Volume2 className="w-7 h-7" />
                  )}
                </div>

                <div className="space-y-1">
                  <span className="font-mono text-sm font-bold text-slate-100 block truncate">
                    {selectedFile.name}
                  </span>
                  <p className="font-mono text-xs text-slate-400">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedMediaType.toUpperCase()}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                  className="text-xs font-mono text-cyan-400 hover:text-cyan-300 underline underline-offset-4 transition-colors"
                >
                  Choose a different file
                </button>
              </div>
            )}
          </div>

          {/* Prominent Analyze Button */}
          {selectedFile && (
            <button
              onClick={handleAnalyze}
              className="w-full py-4 rounded-2xl bg-gradient-to-r from-cyan-500 to-sky-400 hover:from-cyan-400 hover:to-sky-300 text-slate-950 font-mono text-sm sm:text-base font-extrabold tracking-wide transition-all shadow-[0_0_25px_rgba(0,240,255,0.35)] hover:scale-[1.01] flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>ANALYZE MEDIA</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          )}

          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-xs text-center">
              {errorMsg}
            </div>
          )}
        </div>
      )}

      {/* 3. CLEAN ANALYSIS STATE (LOADING) */}
      {isAnalyzing && (
        <div className="rounded-3xl p-10 sm:p-14 bg-slate-950/80 border border-sky-500/30 shadow-2xl flex flex-col items-center justify-center text-center gap-6 animate-pulse">
          <div className="relative w-20 h-20 flex items-center justify-center">
            <Loader2 className="w-16 h-16 text-cyan-400 animate-spin" />
            <span className="absolute inset-0 rounded-full border-2 border-cyan-400/20 animate-ping" />
          </div>

          <div className="space-y-2">
            <h2 className="font-mono text-xl sm:text-2xl font-bold tracking-wider text-slate-100 uppercase">
              ANALYZING MEDIA
            </h2>
            <p className="font-mono text-sm text-cyan-400 font-medium">
              {ANALYSIS_STAGES[analysisStageIdx]}
            </p>
          </div>

          <div className="w-48 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-cyan-500 to-sky-400 w-full animate-progress" />
          </div>
        </div>
      )}

      {/* 4. RESULT SECTION (AFTER ANALYSIS) */}
      {resultCase && !isAnalyzing && (
        <div className="space-y-8 animate-fadeIn">
          {/* Primary Result Banner */}
          <div className="rounded-3xl p-6 sm:p-8 bg-gradient-to-b from-slate-900/90 to-slate-950 border border-sky-500/25 shadow-2xl space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <span className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">
                ANALYSIS RESULT
              </span>
              {isSimulated ? (
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  DEMO MODE // SIMULATED ANALYSIS
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                  REAL FORENSIC ANALYSIS
                </span>
              )}
            </div>

            {/* Dominant Result Layout */}
            {(() => {
              const riskInfo = getRiskClassification(resultCase);
              const RiskIcon = riskInfo.icon;
              const isInconclusive = resultCase.riskTier === 'INCONCLUSIVE' || resultCase.overallRiskScore === null;
              const aiRiskPct = resultCase.overallRiskScore;
              const authPct = aiRiskPct !== null ? Math.max(0, 100 - aiRiskPct) : null;

              return (
                <div className="space-y-6">
                  {/* Big Percentage & Classification */}
                  <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
                    <div className="flex flex-col items-center justify-center p-5 rounded-2xl bg-slate-950 border border-slate-800 min-w-[130px] shrink-0">
                      <span className={`font-mono ${isInconclusive ? 'text-2xl sm:text-3xl font-bold' : 'text-4xl sm:text-5xl font-extrabold'} ${riskInfo.textColor}`}>
                        {isInconclusive ? 'INCONCLUSIVE' : `${aiRiskPct}%`}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mt-1">
                        {isInconclusive ? 'INSUFFICIENT EVIDENCE' : 'AI / SYNTHETIC RISK'}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-mono font-bold uppercase tracking-wider ${riskInfo.badgeBg}`}>
                        <RiskIcon className="w-4 h-4" />
                        <span>{riskInfo.label}</span>
                      </div>

                      <p className="font-sans text-base sm:text-lg font-semibold text-slate-200 leading-snug">
                        "{riskInfo.statement}"
                      </p>

                      <p className="font-mono text-xs text-slate-400">
                        Target: <strong className="text-slate-300">{resultCase.filename}</strong>
                      </p>
                    </div>
                  </div>

                  {/* Horizontal Percentage Analytics */}
                  <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 space-y-3 font-mono text-xs">
                    {!isInconclusive && aiRiskPct !== null && authPct !== null ? (
                      <>
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-slate-300">
                            <span className="font-semibold text-red-400">AI / SYNTHETIC RISK</span>
                            <span className="font-bold text-red-400">{aiRiskPct}%</span>
                          </div>
                          <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                            <div 
                              className="h-full bg-gradient-to-r from-amber-500 to-red-500 rounded-full transition-all duration-1000"
                              style={{ width: `${aiRiskPct}%` }}
                            />
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          <div className="flex justify-between text-slate-300">
                            <span className="font-semibold text-emerald-400">AUTHENTICITY SIGNAL</span>
                            <span className="font-bold text-emerald-400">{authPct}%</span>
                          </div>
                          <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                            <div 
                              className="h-full bg-gradient-to-r from-sky-500 to-emerald-400 rounded-full transition-all duration-1000"
                              style={{ width: `${authPct}%` }}
                            />
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="py-2 text-center space-y-1">
                        <div className="flex justify-between text-slate-400 font-semibold">
                          <span>ASSESSMENT CONFIDENCE</span>
                          <span className="text-slate-500">INSUFFICIENT DATA</span>
                        </div>
                        <p className="text-[11px] text-slate-500 font-sans">
                          Evidence in target media is insufficient to establish a reliable manipulation probability.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Media-Aware Evidence Breakdown */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                    {/* Visual Card */}
                    <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                      <span className="text-slate-400">VISUAL SIGNALS</span>
                      <span className="font-bold text-cyan-300">
                        {resultCase.mediaType === 'audio'
                          ? 'NOT APPLICABLE'
                          : resultCase.visualScore !== undefined && resultCase.visualScore !== null && resultCase.visualScore > 0
                          ? `${resultCase.visualScore}%`
                          : 'ANALYZED'}
                      </span>
                    </div>

                    {/* Temporal / Frequency Card */}
                    {resultCase.mediaType === 'video' ? (
                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                        <span className="text-slate-400">TEMPORAL SIGNALS</span>
                        <span className="font-bold text-amber-400">
                          {resultCase.temporalScore !== undefined && resultCase.temporalScore !== null && resultCase.temporalScore > 0
                            ? `${resultCase.temporalScore}%`
                            : 'ANALYZED'}
                        </span>
                      </div>
                    ) : (
                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                        <span className="text-slate-400">FREQUENCY FORENSICS</span>
                        <span className="font-bold text-amber-400">
                          {resultCase.mediaType === 'image' ? 'ANALYZED' : 'NOT APPLICABLE'}
                        </span>
                      </div>
                    )}

                    {/* Audio / Face Card */}
                    {resultCase.mediaType === 'image' ? (
                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                        <span className="text-slate-400">FACE ANALYSIS</span>
                        <span className="font-bold text-violet-300">
                          {resultCase.evidenceItems?.some(e => e.id.includes('face') || e.title?.toLowerCase().includes('face'))
                            ? 'FACE DETECTED'
                            : 'NO FACE (GLOBAL)'}
                        </span>
                      </div>
                    ) : resultCase.mediaType === 'video' ? (
                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                        <span className="text-slate-400">AUDIO SIGNALS</span>
                        <span className="font-bold text-violet-300">
                          {resultCase.audioScore !== undefined && resultCase.audioScore !== null && resultCase.audioScore > 0
                            ? `${resultCase.audioScore}%`
                            : 'NOT AVAILABLE'}
                        </span>
                      </div>
                    ) : (
                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                        <span className="text-slate-400">AUDIO SIGNALS</span>
                        <span className="font-bold text-violet-300">
                          {resultCase.audioScore !== undefined && resultCase.audioScore !== null && resultCase.audioScore > 0
                            ? `${resultCase.audioScore}%`
                            : 'ANALYZED'}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}
          </div>

          {/* 5. WHY WAS THIS FLAGGED? */}
          {explanation && (
            <div className="rounded-3xl p-6 sm:p-8 bg-slate-950/90 border border-sky-500/20 shadow-xl space-y-4">
              <h3 className="font-mono text-sm sm:text-base font-bold text-slate-100 uppercase tracking-wide flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-cyan-400" />
                <span>WHY WAS THIS FLAGGED?</span>
              </h3>

              <div className="space-y-3">
                {explanation.reasons.map((reason, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1 font-mono text-xs"
                  >
                    <span className="text-cyan-300 font-bold block">
                      {reason.category === 'VISUAL'
                        ? 'Visual Analysis'
                        : reason.category === 'TEMPORAL'
                        ? 'Temporal Analysis'
                        : reason.category === 'AUDIO'
                        ? 'Audio Analysis'
                        : reason.category === 'A/V SYNC'
                        ? 'A/V Synchronization'
                        : reason.category === 'PROVENANCE'
                        ? 'Provenance'
                        : 'Consensus Analysis'}
                    </span>
                    <p className="text-slate-400 leading-relaxed font-sans text-xs sm:text-sm">
                      {reason.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 6. AFTER RESULT ACTIONS */}
          <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <button
              onClick={handleReset}
              className="w-full sm:flex-1 py-3.5 px-6 rounded-2xl bg-gradient-to-r from-cyan-500 to-sky-400 hover:from-cyan-400 hover:to-sky-300 text-slate-950 font-mono text-xs font-extrabold tracking-wide transition-all shadow-[0_0_15px_rgba(0,240,255,0.25)] flex items-center justify-center gap-2 cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
              <span>ANALYZE ANOTHER</span>
            </button>

            <button
              onClick={() => navigateTo('evidence', resultCase)}
              className="w-full sm:w-auto py-3.5 px-6 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-sky-500/30 text-cyan-300 font-mono text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Search className="w-4 h-4" />
              <span>VIEW DETAILED EVIDENCE</span>
            </button>

            <button
              onClick={() => navigateTo('reports', resultCase)}
              className="w-full sm:w-auto py-3.5 px-6 rounded-2xl bg-slate-950 hover:bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 font-mono text-xs font-medium transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <FileText className="w-4 h-4" />
              <span>FULL REPORT</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
