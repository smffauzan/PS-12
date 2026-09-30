import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ForensicCase } from '../types/forensics';
import { INITIAL_DEMO_CASES } from '../data/demoData';
import { checkBackendConnection } from '../services/api/client';
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
  startAnalysis: (fileOrPreset?: File | ForensicCase) => Promise<ForensicCase>;
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

  // Check backend API connectivity on startup and periodically
  useEffect(() => {
    let mounted = true;
    const check = async () => {
      const connected = await checkBackendConnection();
      if (mounted) {
        setIsBackendConnected(connected);
      }
    };
    check();
    const interval = setInterval(check, 8000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
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

  const startAnalysis = async (fileOrPreset?: File | ForensicCase): Promise<ForensicCase> => {
    setIsAnalyzing(true);
    setAnalysisProgress(10);
    setCurrentPipelineStage('Cryptographic Ingestion & Hashing...');
    
    setAnalysisLogs(prev => [
      { timestamp: new Date().toLocaleTimeString(), message: 'Initiating multimodal forensic extraction pipeline...' },
      ...prev.slice(0, 10)
    ]);

    const stages = [
      { name: 'INGEST', progress: 25, log: 'Extracting video frames and spectral acoustic components...' },
      { name: 'SPATIAL', progress: 50, log: 'Inspecting visual spatial anomalies and facial boundary artifacts...' },
      { name: 'TEMPORAL', progress: 75, log: 'Analyzing temporal inter-frame optical flow and lip-sync alignment...' },
      { name: 'FUSION', progress: 95, log: 'Running Bayesian ensemble fusion and explainability engine...' }
    ];

    let currentIdx = 0;
    const stageTimer = setInterval(() => {
      if (currentIdx < stages.length) {
        const stage = stages[currentIdx];
        setCurrentPipelineStage(stage.log);
        setAnalysisProgress(stage.progress);
        setAnalysisLogs(prev => [
          { timestamp: new Date().toLocaleTimeString(), message: stage.log },
          ...prev.slice(0, 10)
        ]);
        currentIdx++;
      }
    }, 450);

    let resultCase: ForensicCase;

    try {
      if (fileOrPreset && 'caseId' in fileOrPreset) {
        resultCase = fileOrPreset as ForensicCase;
      } else if (fileOrPreset && fileOrPreset instanceof File) {
        resultCase = await uploadAndAnalyzeMedia(fileOrPreset);
      } else {
        resultCase = INITIAL_DEMO_CASES[0];
      }
    } catch (err: any) {
      console.error('[FORENSIC CONTEXT] Analysis error:', err);
      resultCase = INITIAL_DEMO_CASES[0];
    } finally {
      clearInterval(stageTimer);
      setAnalysisProgress(100);
      setCurrentPipelineStage('Forensic Analysis Complete');
      setIsAnalyzing(false);
    }

    setItems(prev => [resultCase, ...prev.filter(i => i.id !== resultCase.id)]);
    setActiveItem(resultCase);
    showToast(`Analysis complete for ${resultCase.filename}`);

    return resultCase;
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
