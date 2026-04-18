'use client';

import DocumentUploader from '@/components/dashboard/DocumentUploader';
import ReportGenerator from '@/components/dashboard/ReportGenerator';
import {
  Activity, Shield, ScanEye, Cpu, Fingerprint, Eye,
  PenTool, Type, FileText, Database, GitCompareArrows,
  Brain, Terminal, AlertTriangle,
} from 'lucide-react';

const PIPELINE_GROUPS = [
  {
    phase: 'Stage 1–2 · Intake',
    items: [
      { name: 'Quality Gate', icon: Shield },
      { name: 'Document Classifier', icon: ScanEye },
    ],
  },
  {
    phase: 'Stage 3 · Forensic Agents',
    items: [
      { name: 'OCR Engine', icon: FileText },
      { name: 'ELA Pixel Analysis', icon: Fingerprint },
      { name: 'EXIF Metadata', icon: Eye },
      { name: 'Deepfake Detector', icon: AlertTriangle },
      { name: 'ML Forgery Engine', icon: Cpu },
      { name: 'Signature & Seal', icon: PenTool },
      { name: 'Text Integrity', icon: Type },
      { name: 'Blockchain Ledger', icon: Database },
    ],
  },
  {
    phase: 'Stage 4–7 · Validation',
    items: [
      { name: 'QR Cross-Validator', icon: GitCompareArrows },
      { name: 'Structured Validator', icon: Terminal },
      { name: 'Scoring Engine', icon: Activity },
      { name: 'Explainability AI', icon: Brain },
    ],
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-stone-900 mb-1 tracking-tight">Verify Identity Document</h1>
        <p className="text-sm text-stone-500">Upload a PAN Card, Aadhaar, Passport or Utility Bill for immediate multi-agent forensic analysis.</p>
      </div>

      {/* Main Workspace */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 w-full items-start">
        {/* Left: Uploader / Results (takes 3/4 width on XL) */}
        <div className="xl:col-span-3 min-h-[520px]">
          <DocumentUploader />
        </div>

        {/* Right: Pipeline Status (1/4 width on XL) */}
        <div className="space-y-5">
          {/* System Pipeline — All 14 agents grouped by stage */}
          <div className="p-5 rounded-2xl border border-stone-200 bg-white shadow-sm">
            <h2 className="text-xs font-bold text-stone-400 mb-4 uppercase tracking-widest">System Pipeline</h2>
            <div className="space-y-4">
              {PIPELINE_GROUPS.map((group, gi) => (
                <div key={gi}>
                  <p className="text-[10px] font-bold text-orange-500/60 uppercase tracking-widest mb-1.5 pl-1">
                    {group.phase}
                  </p>
                  <div className="space-y-0.5">
                    {group.items.map((agent, ai) => {
                      const Icon = agent.icon;
                      return (
                        <div
                          key={ai}
                          className="flex items-center justify-between py-1.5 px-2.5 rounded-lg hover:bg-stone-50 transition-colors group/row"
                        >
                          <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0" />
                            <Icon className="w-3.5 h-3.5 text-stone-400 group-hover/row:text-stone-600 transition-colors" />
                            <span className="text-[11px] text-stone-500 group-hover/row:text-stone-700 transition-colors">
                              {agent.name}
                            </span>
                          </div>
                          <span className="text-[8px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border border-emerald-200">
                            ON
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Download Report — only visible when results ready */}
          <ReportGenerator />

          {/* Today's Activity */}
          <div className="p-5 rounded-2xl border border-stone-200 bg-white shadow-sm">
            <h2 className="text-xs font-bold text-stone-400 mb-4 uppercase tracking-widest">Today&apos;s Activity</h2>
            <div className="space-y-3">
              {[
                { label: 'Scans Today', value: '47', color: 'text-stone-800' },
                { label: 'Auto-Approved', value: '38', color: 'text-emerald-500' },
                { label: 'Flagged', value: '9', color: 'text-red-500' },
              ].map((stat, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-xs text-stone-500">{stat.label}</span>
                  <span className={`text-lg font-bold ${stat.color}`}>{stat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
