import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { EvidenceViewer } from '../components/EvidenceViewer';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { Search } from 'lucide-react';

export const EvidenceLabView: React.FC = () => {
  const { activeItem } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Evidence Lab" />

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-cyan-400" />
          <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
            EVIDENCE LAB & ARTIFACT LOCALIZATION
          </h1>
        </div>
        <p className="font-mono text-xs text-slate-400">
          Inspect visual heatmap overlays, suspicious bounding boxes, pixel frequency disparities, and explainable AI evidence.
        </p>
      </div>

      <EvidenceViewer item={activeItem} />
    </div>
  );
};
