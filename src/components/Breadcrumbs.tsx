import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { ChevronRight, FolderKanban } from 'lucide-react';

interface BreadcrumbsProps {
  currentTabName: string;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ currentTabName }) => {
  const { activeItem, navigateTo } = useForensic();

  return (
    <div className="flex items-center gap-2 font-mono text-xs text-slate-400 mb-4 bg-slate-950/60 px-3.5 py-1.5 rounded-lg border border-slate-800/80 w-fit">
      <button 
        onClick={() => navigateTo('command-center')}
        className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
      >
        <FolderKanban className="w-3.5 h-3.5 text-cyan-400" />
        <span>Command Center</span>
      </button>

      <ChevronRight className="w-3.5 h-3.5 text-slate-600" />

      {activeItem && (
        <>
          <button 
            onClick={() => navigateTo('multimodal')}
            className="hover:text-cyan-400 transition-colors text-slate-300 font-semibold flex items-center gap-1"
          >
            <span>{activeItem.caseId || 'CASE VX-04291'}</span>
            <span className="text-slate-500 font-normal">({activeItem.filename})</span>
          </button>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
        </>
      )}

      <span className="text-cyan-400 font-bold uppercase">{currentTabName}</span>
    </div>
  );
};
