import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { Waveform } from '../components/Waveform';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { Volume2 } from 'lucide-react';

export const AudioForensicsView: React.FC = () => {
  const { activeItem } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Audio Forensics" />

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Volume2 className="w-5 h-5 text-violet-400" />
          <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
            AUDIO FORENSICS & SYNTHETIC SPEECH CLONING DETECTOR
          </h1>
        </div>
        <p className="font-mono text-xs text-slate-400">
          Spectrogram waterfall analysis, Mel-frequency cepstral coefficients (MFCC), and voice cloning neural signatures.
        </p>
      </div>

      <Waveform 
        data={activeItem.audioWaveformData} 
        riskScore={activeItem.audioScore || 73}
        transcript={activeItem.transcript}
      />
    </div>
  );
};
