'use client';

import { motion } from 'framer-motion';
import { FileText, CheckCircle2, AlertTriangle, XCircle, Clock, Search, Filter } from 'lucide-react';

const MOCK_DOCS = [
  { name: 'aadhaar_rahul.jpg', type: 'Aadhaar', date: '30 Mar 2026', status: 'Genuine', score: 12 },
  { name: 'pan_forged_v2.png', type: 'PAN Card', date: '30 Mar 2026', status: 'Forged', score: 89 },
  { name: 'passport_ananya.pdf', type: 'Passport', date: '29 Mar 2026', status: 'Genuine', score: 8 },
  { name: 'salary_slip_march.jpg', type: 'Salary Slip', date: '29 Mar 2026', status: 'Suspicious', score: 54 },
  { name: 'utility_bill_delhi.png', type: 'Utility Bill', date: '28 Mar 2026', status: 'Genuine', score: 15 },
  { name: 'aadhaar_tampered.jpg', type: 'Aadhaar', date: '28 Mar 2026', status: 'Forged', score: 76 },
];

const statusConfig = {
  Genuine: { color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200', icon: CheckCircle2 },
  Suspicious: { color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200', icon: AlertTriangle },
  Forged: { color: 'text-red-600', bg: 'bg-red-50 border-red-200', icon: XCircle },
};

export default function DocumentsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight mb-1">Document Vault</h1>
          <p className="text-sm text-stone-500">All KYC documents processed through the forensic pipeline.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-4 py-2.5 bg-white border border-stone-200 rounded-xl text-sm text-stone-400 shadow-sm">
            <Search className="w-4 h-4" />
            <span>Search documents...</span>
          </div>
          <button className="flex items-center gap-2 px-4 py-2.5 bg-white border border-stone-200 rounded-xl text-sm text-stone-500 hover:text-stone-900 hover:border-stone-300 transition-all shadow-sm">
            <Filter className="w-4 h-4" />
            Filter
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Scanned', value: '47', sub: 'this session', color: 'text-orange-500' },
          { label: 'Auto-Approved', value: '38', sub: 'score ≤ 30', color: 'text-emerald-500' },
          { label: 'Rejected / Flagged', value: '9', sub: 'score > 30', color: 'text-red-500' },
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-5 rounded-2xl border border-stone-200 bg-white shadow-sm"
          >
            <p className="text-xs text-stone-400 uppercase tracking-wider font-bold mb-2">{stat.label}</p>
            <p className={`text-4xl font-black ${stat.color} mb-1`}>{stat.value}</p>
            <p className="text-xs text-stone-400">{stat.sub}</p>
          </motion.div>
        ))}
      </div>

      {/* Document Table */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="rounded-2xl border border-stone-200 bg-white shadow-sm overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200">
          <h2 className="text-sm font-bold text-stone-700 flex items-center gap-2">
            <FileText className="w-4 h-4 text-orange-500" />
            Recent Submissions
          </h2>
          <span className="text-xs text-stone-400">{MOCK_DOCS.length} documents</span>
        </div>
        <div className="divide-y divide-stone-100">
          {MOCK_DOCS.map((doc, i) => {
            const cfg = statusConfig[doc.status as keyof typeof statusConfig];
            const Icon = cfg.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.35 + i * 0.07 }}
                className="flex items-center justify-between px-6 py-4 hover:bg-stone-50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-9 h-9 rounded-lg bg-stone-100 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-stone-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-stone-800">{doc.name}</p>
                    <p className="text-xs text-stone-400">{doc.type} · {doc.date}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm font-bold text-stone-500 tabular-nums">
                    Score: <span className={cfg.color}>{doc.score}</span>/100
                  </span>
                  <span className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full border ${cfg.bg} ${cfg.color}`}>
                    <Icon className="w-3.5 h-3.5" />
                    {doc.status}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Footer note */}
      <p className="text-xs text-stone-400 flex items-center gap-2">
        <Clock className="w-3.5 h-3.5" />
        Documents are retained in session only. No PII is persisted to disk.
      </p>
    </div>
  );
}
