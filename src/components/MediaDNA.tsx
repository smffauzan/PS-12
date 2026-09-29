import React, { useState } from 'react';
import type { ForensicMediaItem } from '../types/forensics';
import { Dna, Copy, Check, FileCode, Terminal } from 'lucide-react';
import { useForensic } from '../context/ForensicContext';

interface MediaDNAProps {
  item: ForensicMediaItem;
}

export const MediaDNA: React.FC<MediaDNAProps> = ({ item }) => {
  const { showToast } = useForensic();
  const [copiedHash, setCopiedHash] = useState(false);

  const handleCopyHash = () => {
    navigator.clipboard.writeText(item.sha256);
    setCopiedHash(true);
    showToast('SHA-256 Cryptographic Hash copied to clipboard!');
    setTimeout(() => setCopiedHash(false), 2500);
  };

  return (
    <div className="w-full glass-panel p-6 rounded-2xl flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Dna className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              MEDIA DNA & CRYPTOGRAPHIC FINGERPRINT
            </h3>
            <p className="text-xs font-mono text-slate-400">
              SHA-256 hash verification, container atom structure & EXIF/XMP metadata payload
            </p>
          </div>
        </div>

        <button
          onClick={handleCopyHash}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-cyan-300 font-mono text-xs transition-colors"
        >
          {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copiedHash ? 'HASH COPIED!' : 'COPY SHA-256'}</span>
        </button>
      </div>

      <div className="p-4 rounded-xl bg-slate-950 border border-sky-500/20 flex flex-col gap-3">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400">
          <span>SHA-256 FINGERPRINT:</span>
          <span className="text-cyan-400">STATUS: VERIFIED IMMUTABLE</span>
        </div>
        <div className="font-mono text-xs text-slate-200 bg-slate-900/90 p-3 rounded-lg border border-slate-800 break-all select-all shadow-inner">
          {item.sha256}
        </div>

        <div className="h-6 w-full flex items-center gap-0.5 overflow-hidden opacity-60">
          {Array.from({ length: 80 }).map((_, i) => (
            <div 
              key={i} 
              className={`h-full ${i % 3 === 0 ? 'w-1 bg-cyan-400' : i % 5 === 0 ? 'w-2 bg-violet-500' : 'w-0.5 bg-slate-700'}`} 
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3 font-mono text-xs">
          <h4 className="text-slate-400 uppercase tracking-wider font-bold border-b border-slate-800 pb-2 flex items-center gap-2">
            <FileCode className="w-4 h-4 text-cyan-400" /> CONTAINER METADATA
          </h4>
          <div className="flex justify-between"><span className="text-slate-500">FILE TYPE:</span> <span className="text-slate-200">{item.metadata.fileType}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">MIME TYPE:</span> <span className="text-slate-200">{item.metadata.mimeType}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">CODEC / ENCODER:</span> <span className="text-slate-200">{item.metadata.codec}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">RESOLUTION:</span> <span className="text-cyan-300 font-bold">{item.metadata.resolution || 'N/A'}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">FRAME COUNT:</span> <span className="text-slate-200">{item.metadata.frameCount || 'N/A'}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">BITRATE:</span> <span className="text-slate-200">{item.metadata.bitrate}</span></div>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3 font-mono text-xs">
          <h4 className="text-slate-400 uppercase tracking-wider font-bold border-b border-slate-800 pb-2 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-violet-400" /> EXIF & CREATOR PAYLOAD
          </h4>
          <div className="flex justify-between"><span className="text-slate-500">DURATION:</span> <span className="text-slate-200">{item.metadata.duration || 'N/A'}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">CREATED DATE:</span> <span className="text-slate-200">{item.metadata.creationDate}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">MODIFIED DATE:</span> <span className="text-slate-200">{item.metadata.modificationDate}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">SOFTWARE:</span> <span className="text-amber-400 font-bold">{item.metadata.software}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">CAMERA MODEL:</span> <span className="text-slate-200">{item.metadata.cameraModel || 'Stripped'}</span></div>
          <div className="flex justify-between"><span className="text-slate-500">COLOR SPACE:</span> <span className="text-slate-200">{item.metadata.colorSpace || 'sRGB'}</span></div>
        </div>
      </div>
    </div>
  );
};
