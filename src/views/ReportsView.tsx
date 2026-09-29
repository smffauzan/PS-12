import React from 'react';
import { useForensic } from '../context/ForensicContext';
import { ReportViewer } from '../components/ReportViewer';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { FileText } from 'lucide-react';

export const ReportsView: React.FC = () => {
  const { activeItem } = useForensic();

  return (
    <div className="space-y-6 animate-fadeIn">
      <Breadcrumbs currentTabName="Verification Reports" />

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-cyan-400" />
          <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-slate-100">
            VERIFICATION REPORTS & AUDIT CERTIFICATES
          </h1>
        </div>
        <p className="font-mono text-xs text-slate-400">
          Official forensic report generation, PDF export, QR-code cryptographic audit ledger links.
        </p>
      </div>

      <ReportViewer item={activeItem} />
    </div>
  );
};
