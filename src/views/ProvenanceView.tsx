import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { ProvenanceGraph } from '../components/ProvenanceGraph';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { GitCommit } from 'lucide-react';

export const ProvenanceView: React.FC = () => {
  const { activeItem } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Provenance" />

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <GitCommit className="w-5 h-5 text-cyan-400" />
          <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
            PROVENANCE INTELLIGENCE & C2PA CREDENTIALS
          </h1>
        </div>
        <p className="font-mono text-xs text-slate-400">
          Content Credentials validation, device hardware root key signatures, and lineage history tracking.
        </p>
      </div>

      <ProvenanceGraph item={activeItem} />
    </div>
  );
};
