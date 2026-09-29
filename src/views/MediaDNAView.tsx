import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { MediaDNA } from '../components/MediaDNA';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { Dna } from 'lucide-react';

export const MediaDNAView: React.FC = () => {
  const { activeItem } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Media DNA" />

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Dna className="w-5 h-5 text-cyan-400" />
          <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
            MEDIA DNA & CRYPTOGRAPHIC FILE FORENSICS
          </h1>
        </div>
        <p className="font-mono text-xs text-slate-400">
          Immutable SHA-256 fingerprinting, container atom structure, bitstream codec validation, and stripped EXIF inspection.
        </p>
      </div>

      <MediaDNA item={activeItem} />
    </div>
  );
};
