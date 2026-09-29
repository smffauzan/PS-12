import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { ModelConsensus } from '../components/ModelConsensus';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { ShieldCheck } from 'lucide-react';

export const ModelConsensusView: React.FC = () => {
  const { activeItem } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Model Consensus" />

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-cyan-400" />
          <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
            MODEL CONSENSUS & DETECTOR COMPARISON
          </h1>
        </div>
        <p className="font-mono text-xs text-slate-400">
          Ensemble detector output comparison across spatial convolution, temporal transformers, and audio vocoders.
        </p>
      </div>

      <ModelConsensus item={activeItem} />
    </div>
  );
};
