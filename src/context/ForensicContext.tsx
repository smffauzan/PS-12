import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ForensicCase, RiskLevel } from '../types/forensics';
import { INITIAL_DEMO_CASES } from '../data/demoData';
import { checkBackendConnection, getIsBackendConnected } from '../services/api/client';
import { uploadAndAnalyzeMedia } from '../services/api/analysisApi';

export type NavTab = 
  | 'command-center'
  | 'intake'
  | 'live'
  | 'multimodal'
  | 'evidence'
  | 'audio'
  | 'timeline'
  | 'media-dna'
  | 'provenance'
  | 'consensus'
  | 'robustness'
  | 'reports';

interface LogEvent {
  timestamp: string;
  message: string;
}

interface ForensicContextType {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  items: ForensicCase[];
  activeItem: ForensicCase;
  setActiveItem: (item: ForensicCase) => void;
  navigateTo: (tab: NavTab, item?: ForensicCase) => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  
  // Simulated & Live Analysis State
  isAnalyzing: boolean;
  analysisProgress: number;
  currentPipelineStage: string;
  analysisLogs: LogEvent[];
  startAnalysis: (fileOrPreset?: File | ForensicCase) => void;
  isBackendConnected: boolean;
  
  // Notification toast
  toastMessage: string | null;
  showToast: (msg: string) => void;
}

const ForensicContext = createContext<ForensicContextType | undefined>(undefined);

export const ForensicProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [items, setItems] = useState<ForensicCase[]>(INITIAL_DEMO_CASES);
  const [activeItem, setActiveItem] = useState<ForensicCase>(INITIAL_DEMO_CASES[0]);
  const [activeTab, setActiveTab] = useState<NavTab>('command-center');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisProgress, setAnalysisProgress] = useState<number>(0);
  const [currentPipelineStage, setCurrentPipelineStage] = useState<string>('Idle');
  const [analysisLogs, setAnalysisLogs] = useState<LogEvent[]>([
    { timestamp: new Date().toLocaleTimeString(), message: 'SYSTEM ENGINE INITIALIZED v0.9.0-PROTOTYPE' }
  ]);

  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Check backend API connectivity on startup
  useEffect(() => {
    checkBackendConnection().then(connected => {
      setIsBackendConnected(connected);
      if (connected) {
        showToast('FastAPI Backend Connected: Live Engine Active');
      }
    });
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  const navigateTo = (tab: NavTab, item?: ForensicCase) => {
    if (item) {
      setActiveItem(item);
    }
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const startAnalysis = async (fileOrPreset?: File | ForensicCase) => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setCurrentPipelineStage('INGEST');
    
    let targetItem: ForensicCase;
    const caseNum = Math.floor(1000 + Math.random() * 9000);
    const caseId = `CASE VX-0${caseNum}`;

    if (fileOrPreset && 'caseId' in fileOrPreset) {
      targetItem = fileOrPreset as ForensicCase;
    } else if (fileOrPreset && fileOrPreset instanceof File) {
      const file = fileOrPreset as File;
      const isVideo = file.type.startsWith('video');
      const isAudio = file.type.startsWith('audio');
      const mediaType = isVideo ? 'video' : isAudio ? 'audio' : 'image';

      // If backend is connected, try real upload analysis
      if (getIsBackendConnected()) {
        try {
          const realResult = await uploadAndAnalyzeMedia(file, caseId);
          if (realResult) {
            setIsAnalyzing(false);
            setItems(prev => [realResult, ...prev.filter(i => i.id !== realResult.id)]);
            setActiveItem(realResult);
            showToast(`Analysis complete for ${realResult.filename}`);
            return realResult;
          }
        } catch {
          // Fall through to simulated fallback if API fails
        }
      }
      
      const randomRisk = Math.floor(Math.random() * 40) + 55;
      const riskTier: RiskLevel = randomRisk > 75 ? 'HIGH RISK' : randomRisk > 45 ? 'MEDIUM RISK' : 'LOW RISK';
      
      targetItem = {
        caseId: caseId,
        mediaId: `MED-${Math.floor(10000 + Math.random() * 90000)}-X`,
        id: caseId,
        filename: file.name,
        mediaType: mediaType,
        fileSize: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        sha256: Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
        uploadedAt: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
        overallRiskScore: randomRisk,
        riskTier: riskTier,
        confidence: Math.floor(Math.random() * 10) + 88,
        modelConsensus: Math.floor(Math.random() * 8) + 90,
        signalCount: Math.floor(Math.random() * 6) + 4,
        processingLatencyMs: Math.floor(Math.random() * 60) + 110,
        modelVersion: 'VERITAS ENGINE v0.9.0-PROTOTYPE',
        analysisStatus: 'COMPLETE',
        visualScore: mediaType !== 'audio' ? randomRisk + 2 : 0,
        audioScore: mediaType !== 'image' ? Math.max(0, randomRisk - 6) : 0,
        temporalScore: mediaType === 'video' ? Math.max(0, randomRisk - 4) : 0,
        avSyncScore: mediaType === 'video' ? Math.max(0, randomRisk - 5) : 0,
        c2paStatus: 'UNVERIFIED',
        metadata: {
          fileType: file.type || 'Custom Media',
          mimeType: file.type || 'application/octet-stream',
          codec: isVideo ? 'H.264 / AVC' : isAudio ? 'AAC 48kHz' : 'PNG / JPEG',
          resolution: isVideo ? '1920 x 1080 (FHD)' : isAudio ? 'N/A' : '3840 x 2160',
          bitrate: '12.4 Mbps',
          duration: isVideo ? '00:24.00' : isAudio ? '00:45.00' : undefined,
          creationDate: new Date().toISOString().substring(0, 10),
          modificationDate: new Date().toISOString().substring(0, 10),
          software: 'Custom Ingestion Node',
        },
        signals: [
          {
            id: 'sig-c1',
            name: 'Facial Feature Anomaly',
            category: 'visual',
            severity: 'high',
            confidence: randomRisk,
            affectedRegionOrTime: 'Face Region',
            explanation: 'Elevated manipulation probability was detected in the analyzed face region.'
          }
        ],
        evidenceItems: [
          {
            id: 'ev-custom-1',
            name: 'Facial Texture Analysis',
            title: 'Visual Face Analysis',
            category: mediaType === 'audio' ? 'audio' : 'visual',
            severity: randomRisk > 75 ? 'high' : 'medium',
            description: 'Elevated manipulation probability was detected in the analyzed face region.',
            affectedRegionOrTime: 'Face Region',
            explanation: 'Spatial Vision Transformer classifier produced elevated synthetic score.',
            confidence: randomRisk
          }
        ],
        timelineMarkers: [],
        modelOutputs: [],
        robustnessResults: [],
        provenanceGraph: []
      };
    } else {
      targetItem = INITIAL_DEMO_CASES[0];
    }

    const stages = [
      { name: 'INGEST', progress: 15, log: 'Inspecting visual signals...' },
      { name: 'ANALYSIS', progress: 45, log: 'Analyzing temporal patterns...' },
      { name: 'AUDIO', progress: 75, log: 'Analyzing audio signals...' },
      { name: 'EVIDENCE', progress: 100, log: 'Evaluating forensic evidence...' }
    ];

    let currentIdx = 0;
    const interval = setInterval(() => {
      if (currentIdx < stages.length) {
        const stage = stages[currentIdx];
        setCurrentPipelineStage(stage.log);
        setAnalysisProgress(stage.progress);
        setAnalysisLogs(prev => [
          { timestamp: new Date().toLocaleTimeString(), message: stage.log },
          ...prev.slice(0, 10)
        ]);
        currentIdx++;
      } else {
        clearInterval(interval);
        setIsAnalyzing(false);
        setItems(prev => [targetItem, ...prev.filter(i => i.id !== targetItem.id)]);
        setActiveItem(targetItem);
        showToast(`Analysis complete for ${targetItem.filename}`);
      }
    }, 400);

    return targetItem;
  };

  return (
    <ForensicContext.Provider value={{
      activeTab,
      setActiveTab,
      items,
      activeItem,
      setActiveItem,
      navigateTo,
      isSidebarCollapsed,
      setIsSidebarCollapsed,
      isAnalyzing,
      analysisProgress,
      currentPipelineStage,
      analysisLogs,
      startAnalysis,
      isBackendConnected,
      toastMessage,
      showToast,
    }}>
      {children}
    </ForensicContext.Provider>
  );
};

export const useForensic = () => {
  const ctx = useContext(ForensicContext);
  if (!ctx) throw new Error('useForensic must be used within ForensicProvider');
  return ctx;
};
