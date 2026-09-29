import React from 'react';
import { ForensicProvider, useForensic } from './context/ForensicContext';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';

// Views
import { CommandCenterView } from './views/CommandCenterView';
import { MediaIntakeView } from './views/MediaIntakeView';
import { LiveForensicsView } from './views/LiveForensicsView';
import { MultimodalAnalysisView } from './views/MultimodalAnalysisView';
import { EvidenceLabView } from './views/EvidenceLabView';
import { AudioForensicsView } from './views/AudioForensicsView';
import { ForensicTimelineView } from './views/ForensicTimelineView';
import { MediaDNAView } from './views/MediaDNAView';
import { ProvenanceView } from './views/ProvenanceView';
import { ModelConsensusView } from './views/ModelConsensusView';
import { RobustnessLabView } from './views/RobustnessLabView';
import { ReportsView } from './views/ReportsView';

const MainContent: React.FC = () => {
  const { activeTab, isSidebarCollapsed } = useForensic();

  const renderActiveView = () => {
    switch (activeTab) {
      case 'command-center':
        return <CommandCenterView />;
      case 'intake':
        return <MediaIntakeView />;
      case 'live':
        return <LiveForensicsView />;
      case 'multimodal':
        return <MultimodalAnalysisView />;
      case 'evidence':
        return <EvidenceLabView />;
      case 'audio':
        return <AudioForensicsView />;
      case 'timeline':
        return <ForensicTimelineView />;
      case 'media-dna':
        return <MediaDNAView />;
      case 'provenance':
        return <ProvenanceView />;
      case 'consensus':
        return <ModelConsensusView />;
      case 'robustness':
        return <RobustnessLabView />;
      case 'reports':
        return <ReportsView />;
      default:
        return <CommandCenterView />;
    }
  };

  return (
    <div className="min-h-screen bg-[#06080d] bg-tech-grid bg-radial-glow text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      <Sidebar />
      <TopBar />
      
      <main className={`flex-1 pt-20 pb-12 px-6 lg:px-10 transition-all duration-300 ${
        isSidebarCollapsed ? 'ml-20' : 'ml-64'
      }`}>
        <div className="max-w-[1600px] mx-auto">
          {renderActiveView()}
        </div>
      </main>

      {/* Footer */}
      <footer className={`py-4 px-6 border-t border-sky-500/15 text-xs font-mono text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2 transition-all duration-300 ${
        isSidebarCollapsed ? 'ml-20' : 'ml-64'
      }`}>
        <div>
          VERITAS AI MULTIMODAL MEDIA FORENSICS • DEMO / SIMULATED ANALYSIS
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <span>SYSTEM VER: v4.2.1-prod</span>
          <span>•</span>
          <span>CLEARANCE: LEVEL 5 RESTRICTED</span>
        </div>
      </footer>
    </div>
  );
};

export function App() {
  return (
    <ForensicProvider>
      <MainContent />
    </ForensicProvider>
  );
}

export default App;
