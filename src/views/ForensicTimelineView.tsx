import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { ForensicTimeline } from '../components/ForensicTimeline';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { Clock } from 'lucide-react';

export const ForensicTimelineView: React.FC = () => {
  const { activeItem } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Forensic Timeline" />

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-cyan-400" />
          <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
            HIGH-RESOLUTION FORENSIC TIMELINE
          </h1>
        </div>
        <p className="font-mono text-xs text-slate-400">
          Horizontal scrubber tracking flagged frame markers, visual anomalies, acoustic spikes, and lip-sync delays.
        </p>
      </div>

      <ForensicTimeline item={activeItem} />
    </div>
  );
};
