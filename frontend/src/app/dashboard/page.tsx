'use client';

import DocumentUploader from '@/components/dashboard/DocumentUploader';
import { Activity } from 'lucide-react';

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-white mb-1 tracking-tight">Verify Identity Document</h1>
        <p className="text-sm text-slate-400">Upload a PAN Card, Aadhaar, Passport or Utility Bill for immediate multi-agent forensic analysis.</p>
      </div>

      {/* Main Workspace */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 w-full items-start">
        {/* Left: Uploader / Results (takes 3/4 width on XL) */}
        <div className="xl:col-span-3 min-h-[520px]">
          <DocumentUploader />
        </div>

        {/* Right: Pipeline Status (1/4 width on XL) */}
        <div className="space-y-6">
          <div className="p-6 rounded-2xl border border-slate-800/80" style={{ backdropFilter: 'blur(12px)', background: 'rgba(15, 23, 42, 0.5)' }}>
            <h2 className="text-xs font-bold text-slate-500 mb-5 uppercase tracking-widest">System Pipeline</h2>
            <div className="space-y-3">
              {[
                { name: 'Integrity Validation', status: 'Online', color: 'bg-emerald-500' },
                { name: 'Forgery Engine', status: 'Online', color: 'bg-emerald-500' },
                { name: 'EXIF Extractor', status: 'Online', color: 'bg-emerald-500' },
                { name: 'QR Cross-Val', status: 'Online', color: 'bg-emerald-500' },
                { name: 'Scoring Engine', status: 'Online', color: 'bg-emerald-500' },
              ].map((service, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-slate-800/30 border border-slate-700/40">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${service.color} animate-pulse`} />
                    <span className="text-sm text-slate-300">{service.name}</span>
                  </div>
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded font-bold uppercase">{service.status}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="p-6 rounded-2xl border border-slate-800/80" style={{ backdropFilter: 'blur(12px)', background: 'rgba(15, 23, 42, 0.5)' }}>
            <h2 className="text-xs font-bold text-slate-500 mb-5 uppercase tracking-widest">Today&apos;s Activity</h2>
            <div className="space-y-4">
              {[
                { label: 'Scans Today', value: '47', icon: Activity },
                { label: 'Auto-Approved', value: '38', icon: Activity },
                { label: 'Flagged', value: '9', icon: Activity },
              ].map((stat, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">{stat.label}</span>
                  <span className="text-lg font-bold text-slate-200">{stat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
