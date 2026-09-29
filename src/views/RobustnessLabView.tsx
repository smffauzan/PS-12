import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { RobustnessLab } from '../components/RobustnessLab';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { Sliders } from 'lucide-react';

export const RobustnessLabView: React.FC = () => {
  const { activeItem } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Robustness Lab" />

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-cyan-400" />
          <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
            ROBUSTNESS LAB & ADVERSARIAL STRESS TESTING
          </h1>
        </div>
        <p className="font-mono text-xs text-slate-400">
          Simulate social media compression, spatial cropping, noise injection, and re-encoding to verify model stability.
        </p>
      </div>

      <RobustnessLab item={activeItem} />
    </div>
  );
};
