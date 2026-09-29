import React, { useEffect, useRef, useState } from 'react';
import type { ForensicMediaItem } from '../types/forensics';
import { FileText, Link, QrCode, ShieldAlert, Printer, Check } from 'lucide-react';
import QRCode from 'qrcode';
import { useForensic } from '../context/ForensicContext';

interface ReportViewerProps {
  item: ForensicMediaItem;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ item }) => {
  const { showToast } = useForensic();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);

  useEffect(() => {
    if (canvasRef.current) {
      QRCode.toCanvas(
        canvasRef.current,
        `https://veritas.ai/verify/${item.id}`,
        { width: 140, margin: 1, color: { dark: '#00f0ff', light: '#080b12' } },
        (error) => {
          if (error) console.error('QR code render error', error);
        }
      );
    }
  }, [item.id, showQrModal]);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(`https://veritas.ai/verify/${item.id}`);
    setCopiedLink(true);
    showToast('Verification URL copied to clipboard!');
    setTimeout(() => setCopiedLink(false), 2500);
  };

  const handlePrintPdf = () => {
    window.print();
  };

  return (
    <div className="w-full glass-panel p-8 rounded-2xl flex flex-col gap-8 print:p-0 print:bg-white print:text-black">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-sky-500/15 print:hidden">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-mono text-base font-bold text-slate-100 uppercase tracking-wider">
              VERIFICATION REPORT GENERATOR
            </h2>
            <p className="text-xs font-mono text-slate-400">
              Official forensic analysis summary certificate & cryptographic audit log
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleCopyLink}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-mono text-xs transition-colors"
          >
            {copiedLink ? <Check className="w-4 h-4 text-emerald-400" /> : <Link className="w-4 h-4 text-cyan-400" />}
            <span>{copiedLink ? 'LINK COPIED' : 'COPY VERIFICATION LINK'}</span>
          </button>

          <button
            onClick={() => setShowQrModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 border border-violet-500/40 text-violet-300 font-mono text-xs transition-colors"
          >
            <QrCode className="w-4 h-4 text-violet-400" />
            <span>SHOW QR</span>
          </button>

          <button
            onClick={handlePrintPdf}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono text-xs font-bold transition-colors shadow-[0_0_15px_rgba(0,240,255,0.3)]"
          >
            <Printer className="w-4 h-4" />
            <span>GENERATE PDF / PRINT</span>
          </button>
        </div>
      </div>

      <div className="p-8 rounded-2xl bg-[#080b12] border border-sky-500/20 flex flex-col gap-6 font-mono text-xs relative overflow-hidden">
        <div className="flex items-center justify-between pb-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div className="flex flex-col">
              <span className="font-mono font-bold text-xl text-slate-100 tracking-wider">
                VERITAS<span className="text-cyan-400">.AI</span>
              </span>
              <span className="text-[10px] text-slate-400 tracking-widest uppercase">
                MEDIA AUTHENTICITY FORENSIC REPORT
              </span>
            </div>
          </div>

          <div className="flex flex-col text-right">
            <span className="text-slate-400">REPORT ID: <strong className="text-cyan-400">{item.id}</strong></span>
            <span className="text-slate-400">TIMESTAMP: <strong className="text-slate-200">{item.uploadedAt}</strong></span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 p-6 rounded-xl bg-slate-950 border border-slate-800 items-center">
          <div className="md:col-span-4 flex flex-col items-center justify-center p-4 border-b md:border-b-0 md:border-r border-slate-800">
            <span className="text-[10px] text-slate-400 tracking-widest uppercase">OVERALL RISK SCORE</span>
            <span className={`text-5xl font-bold mt-1 ${item.overallRiskScore !== null && item.overallRiskScore >= 75 ? 'text-red-400' : item.overallRiskScore === null ? 'text-slate-400' : 'text-emerald-400'}`}>
              {item.overallRiskScore !== null ? `${item.overallRiskScore}%` : 'N/A'}
            </span>
            <span className={`mt-2 px-3 py-1 rounded-full text-xs font-bold ${
              item.overallRiskScore !== null && item.overallRiskScore >= 75 ? 'bg-red-500/20 text-red-400 border border-red-500/40' : item.overallRiskScore === null ? 'bg-slate-800 text-slate-300' : 'bg-emerald-500/20 text-emerald-400'
            }`}>
              {item.riskTier}
            </span>
          </div>

          <div className="md:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-slate-500 text-[10px]">VISUAL AI</div>
              <div className="text-lg font-bold text-slate-200">{item.visualScore}%</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-slate-500 text-[10px]">AUDIO AI</div>
              <div className="text-lg font-bold text-slate-200">{item.audioScore}%</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-slate-500 text-[10px]">TEMPORAL AI</div>
              <div className="text-lg font-bold text-slate-200">{item.temporalScore}%</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-slate-500 text-[10px]">A/V SYNC</div>
              <div className="text-lg font-bold text-slate-200">{item.avSyncScore}%</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <h4 className="text-slate-400 font-bold uppercase tracking-wider border-b border-slate-800 pb-1">FILE IDENTIFICATION</h4>
            <div className="flex justify-between"><span className="text-slate-500">FILENAME:</span> <span className="text-slate-200 font-bold">{item.filename}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">FILE SIZE:</span> <span className="text-slate-200">{item.fileSize}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">FORMAT / CODEC:</span> <span className="text-slate-200">{item.metadata.codec}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">C2PA PROVENANCE:</span> <span className="text-amber-400 font-bold">{item.c2paStatus}</span></div>
          </div>

          <div className="space-y-2">
            <h4 className="text-slate-400 font-bold uppercase tracking-wider border-b border-slate-800 pb-1">AUDIT SUMMARY</h4>
            <div className="flex justify-between"><span className="text-slate-500">MODEL ENGINE:</span> <span className="text-cyan-400">{item.modelVersion}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">PROCESSING TIME:</span> <span className="text-slate-200">{item.processingLatencyMs} ms</span></div>
            <div className="flex justify-between"><span className="text-slate-500">CONFIDENCE INDEX:</span> <span className="text-cyan-300 font-bold">{item.confidence}%</span></div>
            <div className="flex justify-between"><span className="text-slate-500">ANOMALY COUNT:</span> <span className="text-red-400 font-bold">{item.evidenceItems.length} DETECTED</span></div>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <canvas ref={canvasRef} className="rounded border border-slate-800" />
            <div className="flex flex-col text-[11px] text-slate-400">
              <span className="font-bold text-cyan-300">CRYPTOGRAPHIC PROOF URL</span>
              <span>Scan QR code to verify immutable record on VERITAS ledger</span>
            </div>
          </div>

          <div className="text-right text-[10px] text-slate-500">
            <div>AUTHORIZED FORENSIC AGENT</div>
            <div className="font-bold text-slate-300 mt-1">VERITAS INTELLIGENCE NODE #09</div>
          </div>
        </div>
      </div>

      {showQrModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel p-6 rounded-2xl max-w-sm w-full flex flex-col items-center gap-4 border border-cyan-400/40">
            <h3 className="font-mono text-sm font-bold text-slate-100 uppercase tracking-wider">
              VERIFICATION QR CODE
            </h3>
            <canvas ref={canvasRef} className="rounded-lg p-2 bg-slate-950 border border-cyan-500/30" />
            <p className="text-xs font-mono text-slate-400 text-center">
              Scan with mobile device to access encrypted authenticity report.
            </p>
            <button
              onClick={() => setShowQrModal(false)}
              className="w-full py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 font-mono text-xs border border-slate-700 transition-colors"
            >
              CLOSE MODAL
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
