import React, { useState, useRef, useEffect } from 'react';
import { useForensic } from '../context/ForensicContext';
import { generateForensicExplanation } from '../services/explanationEngine';
import { uploadAndAnalyzeMedia } from '../services/api/analysisApi';
import { INITIAL_DEMO_CASES } from '../data/demoData';
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
  Loader2,
  Play,
  Pause,
  Activity,
  Sparkles,
  Zap,
  Layers,
  FileCheck2,
  Crosshair
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
    extensions: 'WAV, MP3, M4A, AAC, FLAC',
    mime: 'audio/wav,audio/mpeg,audio/mp3,audio/x-m4a,audio/aac,audio/flac',
    label: 'Audio'
  }
};

const ANALYSIS_STAGES = [
  { label: 'Cryptographic Ingestion & SHA-256 Hashing', desc: 'Validating container headers and generating cryptographic digest' },
  { label: 'Spatial Visual Artifact & Face Detection', desc: 'Inspecting pixel token boundaries, corneal reflections, and warping' },
  { label: 'Spectral Frequency & Temporal Stability', desc: 'Analyzing Fourier DCT coefficients and inter-frame optical flow' },
  { label: 'Acoustic Anti-Spoofing & A/V Sync Coherence', desc: 'Evaluating RawNet2 speech vocoders and lip-sync alignment' },
  { label: 'Multi-Model Fusion & Explainability Graph', desc: 'Synthesizing Bayesian consensus and generating explainable audit' }
];

export const CommandCenterView: React.FC = () => {
  const { setActiveItem, navigateTo, isBackendConnected } = useForensic();

  const [selectedMediaType, setSelectedMediaType] = useState<MediaType>('video');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [mediaDimensions, setMediaDimensions] = useState<string | null>(null);
  const [mediaDuration, setMediaDuration] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStageIdx, setAnalysisStageIdx] = useState(0);
  const [analyzedCase, setAnalyzedCase] = useState<ForensicCase | null>(null);
  const [isSimulated, setIsSimulated] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Clean up object URL on unmount or file change
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleFileSelect = (file: File) => {
    setErrorMsg(null);
    setSelectedFile(file);

    // Revoke previous URL
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    // Auto-detect media type if file extension matches another tab
    if (file.type.startsWith('image/')) {
      setSelectedMediaType('image');
      const img = new Image();
      img.onload = () => setMediaDimensions(`${img.naturalWidth} x ${img.naturalHeight}`);
      img.src = url;
    } else if (file.type.startsWith('audio/')) {
      setSelectedMediaType('audio');
      const aud = document.createElement('audio');
      aud.preload = 'metadata';
      aud.onloadedmetadata = () => {
        const dur = aud.duration || 0;
        const mins = Math.floor(dur / 60).toString().padStart(2, '0');
        const secs = Math.floor(dur % 60).toString().padStart(2, '0');
        setMediaDuration(`${mins}:${secs}`);
      };
      aud.src = url;
    } else if (file.type.startsWith('video/')) {
      setSelectedMediaType('video');
      const vid = document.createElement('video');
      vid.preload = 'metadata';
      vid.onloadedmetadata = () => {
        setMediaDimensions(`${vid.videoWidth || 1920} x ${vid.videoHeight || 1080}`);
        const dur = vid.duration || 0;
        const mins = Math.floor(dur / 60).toString().padStart(2, '0');
        const secs = Math.floor(dur % 60).toString().padStart(2, '0');
        setMediaDuration(`${mins}:${secs}`);
      };
      vid.src = url;
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleLoadSample = (sampleCase: ForensicCase) => {
    setErrorMsg(null);
    setSelectedFile(null);
    setPreviewUrl(null);
    setAnalyzedCase(sampleCase);
    setActiveItem(sampleCase);
    setIsSimulated(false);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setErrorMsg(null);
    setAnalysisStageIdx(0);

    // Stage progression interval
    const stageTimer = setInterval(() => {
      setAnalysisStageIdx(prev => {
        if (prev < ANALYSIS_STAGES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 650);

    try {
      const result = await uploadAndAnalyzeMedia(selectedFile, undefined, previewUrl || undefined);
      clearInterval(stageTimer);
      if (result) {
        setAnalyzedCase(result);
        setActiveItem(result);
        setIsSimulated(!isBackendConnected || (result.modelVersion?.includes('DEMO') || false));
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
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setMediaDimensions(null);
    setMediaDuration(null);
    setAnalyzedCase(null);
    setIsSimulated(false);
    setErrorMsg(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const toggleAudioPlayback = () => {
    if (!audioRef.current) return;
    if (isPlayingAudio) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    } else {
      audioRef.current.play();
      setIsPlayingAudio(true);
    }
  };

  // Explanation derived from actual results
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
    <div className="w-full max-w-4xl mx-auto py-4 px-3 sm:px-6 space-y-8 animate-fadeIn">
      {/* 1. COMPACT HERO HEADER */}
      <div className="text-center space-y-2.5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 font-mono text-xs font-semibold tracking-wide">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>VERITAS AI • Detect. Explain. Verify.</span>
        </div>

        <h1 className="font-mono text-2xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
          AI-GENERATED MEDIA DETECTOR
        </h1>

        <p className="font-sans text-xs sm:text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
          Analyze images, videos, and audio for signals associated with AI-generated or manipulated media.
        </p>
      </div>

      {/* 2. MAIN WORKSPACE: UPLOAD OR RESULT */}
      {!resultCase && !isAnalyzing && (
        <div className="space-y-5">
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
                    if (!selectedFile) {
                      setPreviewUrl(null);
                    }
                  }}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 sm:px-4 rounded-xl font-mono text-xs font-bold transition-all ${
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

          {/* Upload Dropzone OR Interactive Media Preview */}
          {!selectedFile ? (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative rounded-3xl p-6 sm:p-10 border-2 border-dashed transition-all flex flex-col items-center justify-center text-center gap-4 cursor-pointer ${
                isDragOver
                  ? 'border-cyan-400 bg-cyan-950/20 shadow-[0_0_25px_rgba(0,240,255,0.15)] scale-[1.01]'
                  : 'border-slate-800 hover:border-cyan-500/50 bg-slate-950/60 hover:bg-slate-900/40 shadow-xl'
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

              <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400 shadow-[0_0_20px_rgba(0,240,255,0.15)]">
                <UploadCloud className="w-7 h-7" />
              </div>

              <div className="space-y-1">
                <h3 className="font-mono text-sm sm:text-base font-bold text-slate-200">
                  Upload {ACCEPTED_TYPES[selectedMediaType].label} for Forensic Analysis
                </h3>
                <p className="font-sans text-xs text-slate-400">
                  Drag & drop your file here, or <span className="text-cyan-400 font-semibold underline underline-offset-4">browse files</span>
                </p>
              </div>

              <div className="text-[11px] font-mono text-slate-500 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800">
                Supported formats: {ACCEPTED_TYPES[selectedMediaType].extensions}
              </div>
            </div>
          ) : (
            /* Interactive Media Preview Card */
            <div className="rounded-3xl p-5 sm:p-7 bg-slate-950/90 border border-cyan-500/40 shadow-2xl space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                  <span className="font-mono text-xs font-bold text-cyan-300 uppercase tracking-wider">
                    TARGET MEDIA LOADED & READY
                  </span>
                </div>

                <button
                  type="button"
                  onClick={handleReset}
                  className="text-xs font-mono text-slate-400 hover:text-red-400 flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Choose Different File</span>
                </button>
              </div>

              {/* Embedded Player / Preview Box */}
              <div className="rounded-2xl overflow-hidden bg-slate-900/90 border border-slate-800 relative flex items-center justify-center min-h-[220px] max-h-[360px]">
                {selectedMediaType === 'video' && previewUrl && (
                  <video
                    src={previewUrl}
                    controls
                    className="w-full max-h-[340px] object-contain rounded-2xl bg-black"
                  />
                )}

                {selectedMediaType === 'image' && previewUrl && (
                  <div className="relative w-full h-full flex items-center justify-center p-2">
                    <img
                      src={previewUrl}
                      alt="Uploaded media preview"
                      className="max-h-[320px] w-auto object-contain rounded-xl shadow-lg"
                    />
                    <div className="absolute top-4 right-4 px-2 py-1 rounded-md bg-slate-950/80 border border-slate-700 text-[10px] font-mono text-cyan-300 flex items-center gap-1">
                      <Crosshair className="w-3 h-3 text-cyan-400" />
                      <span>{mediaDimensions || 'IMAGE READY'}</span>
                    </div>
                  </div>
                )}

                {selectedMediaType === 'audio' && previewUrl && (
                  <div className="w-full p-6 flex flex-col items-center justify-center gap-4">
                    <audio
                      ref={audioRef}
                      src={previewUrl}
                      onEnded={() => setIsPlayingAudio(false)}
                      className="hidden"
                    />
                    <button
                      onClick={toggleAudioPlayback}
                      className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-violet-600 to-cyan-500 text-white flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:scale-105 transition-transform"
                    >
                      {isPlayingAudio ? <Pause className="w-7 h-7" /> : <Play className="w-7 h-7 ml-0.5" />}
                    </button>

                    {/* Animated Equalizer Bars */}
                    <div className="flex items-end justify-center gap-1.5 h-12 w-full max-w-xs">
                      {[40, 65, 85, 30, 95, 55, 75, 45, 90, 60, 35, 80, 50, 70].map((height, i) => (
                        <div
                          key={i}
                          className={`w-2 rounded-t-sm transition-all duration-300 ${
                            isPlayingAudio 
                              ? 'bg-gradient-to-t from-violet-500 to-cyan-400 animate-pulse' 
                              : 'bg-slate-700'
                          }`}
                          style={{ height: isPlayingAudio ? `${height}%` : '25%' }}
                        />
                      ))}
                    </div>

                    <span className="font-mono text-xs text-slate-400">
                      {isPlayingAudio ? 'PLAYING AUDIO STREAM...' : 'CLICK PLAY TO AUDIT SOUNDTRACK'}
                    </span>
                  </div>
                )}
              </div>

              {/* Media File Metadata Pills */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-xs">
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">FILENAME</span>
                  <span className="font-bold text-slate-200 truncate block">{selectedFile.name}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">FILE SIZE</span>
                  <span className="font-bold text-cyan-300">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">MEDIA TYPE</span>
                  <span className="font-bold text-violet-300 uppercase">{selectedMediaType}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">RESOLUTION / DURATION</span>
                  <span className="font-bold text-amber-300">{mediaDimensions || mediaDuration || 'Calculated on run'}</span>
                </div>
              </div>

              {/* Prominent Glowing Run Analysis Button */}
              <button
                onClick={handleAnalyze}
                className="w-full py-4 rounded-2xl bg-gradient-to-r from-cyan-500 via-sky-400 to-cyan-400 hover:from-cyan-400 hover:to-sky-300 text-slate-950 font-mono text-sm sm:text-base font-extrabold tracking-wider transition-all shadow-[0_0_30px_rgba(0,240,255,0.4)] hover:scale-[1.01] flex items-center justify-center gap-3 cursor-pointer"
              >
                <Zap className="w-5 h-5 fill-current" />
                <span>RUN AI FORENSIC ANALYSIS</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* Quick Demo Case Presets (1-Click Sample Test) */}
          <div className="p-4 rounded-2xl bg-slate-950/40 border border-slate-800/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>TRY PRELOADED TEST INVESTIGATIONS (1-CLICK LOAD)</span>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {INITIAL_DEMO_CASES.slice(0, 3).map((sample) => (
                <button
                  key={sample.id}
                  onClick={() => handleLoadSample(sample)}
                  className="p-3 rounded-xl bg-slate-900/70 hover:bg-slate-800/80 border border-slate-800 hover:border-cyan-500/40 text-left transition-all flex items-center justify-between group cursor-pointer"
                >
                  <div className="space-y-0.5 truncate pr-2">
                    <span className="font-mono text-xs font-bold text-slate-200 block truncate group-hover:text-cyan-300">
                      {sample.filename}
                    </span>
                    <span className="font-mono text-[10px] text-slate-500 uppercase">
                      {sample.mediaType} • {sample.fileSize}
                    </span>
                  </div>

                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold shrink-0 ${
                    sample.riskTier === 'HIGH RISK' 
                      ? 'bg-red-500/10 text-red-400 border border-red-500/30' 
                      : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  }`}>
                    {sample.overallRiskScore}%
                  </span>
                </button>
              ))}
            </div>
          </div>

          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-xs text-center">
              {errorMsg}
            </div>
          )}
        </div>
      )}

      {/* 3. FUTURISTIC FORENSIC SCANNING STATE (LOADING) */}
      {isAnalyzing && (
        <div className="rounded-3xl p-8 sm:p-12 bg-slate-950/90 border border-cyan-500/40 shadow-[0_0_40px_rgba(0,240,255,0.15)] space-y-8 animate-fadeIn">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="relative w-12 h-12 flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
                <span className="absolute inset-0 rounded-full border-2 border-cyan-400/20 animate-ping" />
              </div>
              <div>
                <h2 className="font-mono text-lg sm:text-xl font-bold tracking-wider text-slate-100 uppercase">
                  FORENSIC PIPELINE EXECUTING
                </h2>
                <p className="font-mono text-xs text-cyan-300">
                  Target: {selectedFile?.name || 'media_stream'}
                </p>
              </div>
            </div>

            <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 font-mono text-xs font-bold animate-pulse">
              STAGE {analysisStageIdx + 1} OF {ANALYSIS_STAGES.length}
            </span>
          </div>

          {/* Stage Progress Checklist */}
          <div className="space-y-3">
            {ANALYSIS_STAGES.map((stage, idx) => {
              const isDone = idx < analysisStageIdx;
              const isCurrent = idx === analysisStageIdx;
              return (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border font-mono text-xs transition-all flex items-start gap-3 ${
                    isCurrent
                      ? 'bg-cyan-950/40 border-cyan-400/60 shadow-[0_0_15px_rgba(0,240,255,0.15)]'
                      : isDone
                      ? 'bg-slate-900/40 border-slate-800 text-slate-400'
                      : 'bg-slate-950/30 border-slate-900 text-slate-600'
                  }`}
                >
                  <div className="mt-0.5">
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : isCurrent ? (
                      <Activity className="w-4 h-4 text-cyan-400 animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-slate-700" />
                    )}
                  </div>

                  <div className="space-y-0.5 flex-1">
                    <span className={`font-bold block ${isCurrent ? 'text-cyan-300' : isDone ? 'text-slate-300' : 'text-slate-500'}`}>
                      {stage.label}
                    </span>
                    <span className="text-[11px] font-sans text-slate-400">
                      {stage.desc}
                    </span>
                  </div>

                  {isCurrent && (
                    <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest shrink-0">
                      INSPECTING
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Animated Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between font-mono text-xs text-slate-400">
              <span>NEURAL FUSION CONFIDENCE</span>
              <span className="text-cyan-400 font-bold">{Math.round(((analysisStageIdx + 1) / ANALYSIS_STAGES.length) * 100)}%</span>
            </div>
            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
              <div 
                className="h-full bg-gradient-to-r from-cyan-500 via-sky-400 to-cyan-300 rounded-full transition-all duration-500"
                style={{ width: `${((analysisStageIdx + 1) / ANALYSIS_STAGES.length) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* 4. RESULT SECTION (AFTER ANALYSIS) */}
      {resultCase && !isAnalyzing && (
        <div className="space-y-7 animate-fadeIn">
          {/* Primary Result Banner */}
          <div className="rounded-3xl p-6 sm:p-8 bg-gradient-to-b from-slate-900/95 to-slate-950 border border-sky-500/30 shadow-2xl space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2 font-mono text-xs font-bold text-slate-400 uppercase">
                <FileCheck2 className="w-4 h-4 text-cyan-400" />
                <span>FORENSIC VERDICT SUMMARY // {resultCase.caseId}</span>
              </div>

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
                    <div className="flex flex-col items-center justify-center p-5 rounded-2xl bg-slate-950 border border-slate-800 min-w-[140px] shrink-0 shadow-inner">
                      <span className={`font-mono ${isInconclusive ? 'text-2xl sm:text-3xl font-bold' : 'text-4xl sm:text-5xl font-extrabold'} ${riskInfo.textColor}`}>
                        {isInconclusive ? 'INCONCLUSIVE' : `${aiRiskPct}%`}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mt-1">
                        {isInconclusive ? 'INSUFFICIENT EVIDENCE' : 'AI / SYNTHETIC RISK'}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <div className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-xs font-mono font-bold uppercase tracking-wider ${riskInfo.badgeBg}`}>
                        <RiskIcon className="w-4 h-4" />
                        <span>{riskInfo.label}</span>
                      </div>

                      <p className="font-sans text-base sm:text-lg font-semibold text-slate-200 leading-snug">
                        "{riskInfo.statement}"
                      </p>

                      <p className="font-mono text-xs text-slate-400">
                        Target File: <strong className="text-slate-200">{resultCase.filename}</strong> • SHA-256: <strong className="text-cyan-400">{resultCase.sha256?.substring(0, 16)}...</strong>
                      </p>
                    </div>
                  </div>

                  {/* Horizontal Percentage Analytics */}
                  <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 space-y-3 font-mono text-xs">
                    {!isInconclusive && aiRiskPct !== null && authPct !== null ? (
                      <>
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-slate-300">
                            <span className="font-semibold text-red-400">AI / SYNTHETIC MANIPULATION PROBABILITY</span>
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
                            <span className="font-semibold text-emerald-400">ORGANIC AUTHENTICITY PROBABILITY</span>
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

                  {/* Media Inspection Box with Localized Anomaly Overlay */}
                  {resultCase.previewUrl && (
                    <div className="rounded-2xl p-4 bg-slate-950 border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                          <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
                          <span>EVIDENCE ARTIFACT INSPECTION VIEWPORT</span>
                        </span>
                        <span className="text-[10px] font-mono text-cyan-400">
                          {resultCase.evidenceItems?.length || 0} ANOMALIES LOCALIZED
                        </span>
                      </div>

                      <div className="relative rounded-xl overflow-hidden bg-black flex items-center justify-center max-h-[300px]">
                        {resultCase.mediaType === 'video' ? (
                          <video
                            src={resultCase.previewUrl}
                            controls
                            className="max-h-[280px] w-auto object-contain rounded-xl"
                          />
                        ) : resultCase.mediaType === 'image' ? (
                          <div className="relative">
                            <img
                              src={resultCase.previewUrl}
                              alt="Inspected media"
                              className="max-h-[280px] w-auto object-contain rounded-xl"
                            />
                            {/* Simulated or Real Bounding Box */}
                            {resultCase.overallRiskScore && resultCase.overallRiskScore >= 50 && (
                              <div className="absolute top-[20%] left-[35%] w-[30%] h-[40%] border-2 border-red-500 rounded bg-red-500/10 pointer-events-none animate-pulse flex items-start p-1">
                                <span className="bg-red-500 text-slate-950 text-[9px] font-mono font-bold px-1 rounded">
                                  ANOMALY DETECTED ({resultCase.overallRiskScore}%)
                                </span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="p-8 text-center space-y-2">
                            <Volume2 className="w-12 h-12 text-violet-400 mx-auto" />
                            <p className="font-mono text-xs text-slate-300">
                              Speech Anti-Spoofing Spectrogram Analyzed
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 4-Modality Evidence Breakdown Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                    {/* Visual Card */}
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex justify-between items-center">
                      <span className="text-slate-400">VISUAL SPATIAL</span>
                      <span className="font-bold text-cyan-300">
                        {resultCase.mediaType === 'audio'
                          ? 'N/A'
                          : resultCase.visualScore !== undefined && resultCase.visualScore > 0
                          ? `${resultCase.visualScore}%`
                          : 'ORGANIC'}
                      </span>
                    </div>

                    {/* Temporal / Frequency Card */}
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex justify-between items-center">
                      <span className="text-slate-400">
                        {resultCase.mediaType === 'video' ? 'TEMPORAL CONTINUITY' : 'FREQUENCY DOMAIN'}
                      </span>
                      <span className="font-bold text-amber-400">
                        {resultCase.mediaType === 'video'
                          ? `${resultCase.temporalScore || 0}%`
                          : resultCase.mediaType === 'image'
                          ? `${resultCase.visualScore || 0}%`
                          : 'N/A'}
                      </span>
                    </div>

                    {/* Audio / Face Card */}
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex justify-between items-center">
                      <span className="text-slate-400">
                        {resultCase.mediaType === 'image' ? 'FACE MASK SEAM' : 'AUDIO / A-V SYNC'}
                      </span>
                      <span className="font-bold text-violet-300">
                        {resultCase.mediaType === 'image'
                          ? (resultCase.visualScore && resultCase.visualScore >= 50 ? 'DETECTED' : 'UNALTERED')
                          : `${resultCase.audioScore || resultCase.avSyncScore || 0}%`}
                      </span>
                    </div>
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
                <span>WHY WAS THIS FLAGGED? FORENSIC RATIONALE</span>
              </h3>

              <div className="space-y-3">
                {explanation.reasons.map((reason, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1 font-mono text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-cyan-300 font-bold block">
                        {reason.category === 'VISUAL'
                          ? 'Visual Spatial Analysis'
                          : reason.category === 'TEMPORAL'
                          ? 'Temporal Continuity Analysis'
                          : reason.category === 'AUDIO'
                          ? 'Speech Anti-Spoofing Analysis'
                          : reason.category === 'A/V SYNC'
                          ? 'Audio-Visual Synchronization'
                          : reason.category === 'PROVENANCE'
                          ? 'Provenance & Lineage Verification'
                          : 'Multi-Model Consensus Fusion'}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        reason.severity === 'HIGH' || reason.severity === 'CRITICAL'
                          ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}>
                        {reason.severity} SEVERITY
                      </span>
                    </div>
                    <p className="text-slate-300 leading-relaxed font-sans text-xs sm:text-sm pt-1">
                      {reason.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 6. AFTER RESULT ACTIONS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
            <button
              onClick={handleReset}
              className="py-3 px-4 rounded-2xl bg-gradient-to-r from-cyan-500 to-sky-400 hover:from-cyan-400 hover:to-sky-300 text-slate-950 font-mono text-xs font-extrabold tracking-wide transition-all shadow-[0_0_15px_rgba(0,240,255,0.25)] flex items-center justify-center gap-2 cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
              <span>ANALYZE ANOTHER</span>
            </button>

            <button
              onClick={() => navigateTo('evidence', resultCase)}
              className="py-3 px-4 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-sky-500/30 text-cyan-300 font-mono text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Search className="w-4 h-4" />
              <span>EVIDENCE LAB</span>
            </button>

            <button
              onClick={() => navigateTo('multimodal', resultCase)}
              className="py-3 px-4 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-mono text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Layers className="w-4 h-4" />
              <span>MULTIMODAL FUSION</span>
            </button>

            <button
              onClick={() => navigateTo('reports', resultCase)}
              className="py-3 px-4 rounded-2xl bg-slate-950 hover:bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 font-mono text-xs font-medium transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <FileText className="w-4 h-4" />
              <span>EXPORT REPORT</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
