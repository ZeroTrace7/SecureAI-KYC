'use client';

import { motion } from 'framer-motion';
import { Activity, TrendingUp, TrendingDown, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';

const SIGNAL_DATA = [
  { name: 'QR-OCR Cross-Validation', flagRate: 28, avgScore: 0.71, trend: 'up', weight: '25%' },
  { name: 'Structured Doc Validation', flagRate: 22, avgScore: 0.54, trend: 'up', weight: '20%' },
  { name: 'ELA Pixel Forensics', flagRate: 34, avgScore: 0.61, trend: 'up', weight: '18%' },
  { name: 'ML Image Forgery', flagRate: 18, avgScore: 0.42, trend: 'down', weight: '15%' },
  { name: 'Signature & Seal', flagRate: 14, avgScore: 0.38, trend: 'down', weight: '12%' },
  { name: 'EXIF Metadata', flagRate: 22, avgScore: 0.48, trend: 'down', weight: '10%' },
  { name: 'Text Integrity', flagRate: 11, avgScore: 0.29, trend: 'down', weight: '10%' },
  { name: 'Deepfake Detection', flagRate: 6, avgScore: 0.21, trend: 'down', weight: '7%' },
  { name: 'Blockchain Ledger', flagRate: 3, avgScore: 0.12, trend: 'down', weight: '5%' },
];

const RECENT_ALERTS = [
  { msg: 'QR payload mismatch detected on Aadhaar submission', severity: 'Critical', time: '2 min ago' },
  { msg: 'Photoshop EXIF tag on PAN card upload', severity: 'High', time: '11 min ago' },
  { msg: 'ELA anomaly in photo region — salary slip', severity: 'Medium', time: '34 min ago' },
  { msg: 'Batch of 5 documents passed integrity check', severity: 'Info', time: '1 hr ago' },
];

const severityConfig = {
  Critical: 'text-red-400 bg-red-500/10 border-red-500/20',
  High: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  Medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  Info: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
};

export default function AnalyticsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight mb-1">Risk Analytics</h1>
        <p className="text-sm text-slate-400">Forensic signal performance and fraud threat overview.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Fraud Rate', value: '19.1%', icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10' },
          { label: 'Avg Risk Score', value: '38.4', icon: Activity, color: 'text-amber-400', bg: 'bg-amber-500/10' },
          { label: 'Auto-Approved', value: '80.9%', icon: ShieldCheck, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
          { label: 'Avg Scan Time', value: '2.8s', icon: Zap, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
        ].map((kpi, i) => {
          const Icon = kpi.icon;
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="p-5 rounded-2xl border border-slate-800/80 bg-slate-900/40"
              style={{ backdropFilter: 'blur(12px)' }}
            >
              <div className={`w-9 h-9 rounded-lg ${kpi.bg} flex items-center justify-center mb-4`}>
                <Icon className={`w-5 h-5 ${kpi.color}`} />
              </div>
              <p className={`text-3xl font-black ${kpi.color} mb-1`}>{kpi.value}</p>
              <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">{kpi.label}</p>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Signal Performance */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-2xl border border-slate-800/80 overflow-hidden"
          style={{ backdropFilter: 'blur(12px)', background: 'rgba(15, 23, 42, 0.5)' }}
        >
          <div className="px-6 py-4 border-b border-slate-800/80">
            <h2 className="text-sm font-bold text-slate-300 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              Forensic Signal Performance
            </h2>
          </div>
          <div className="p-6 space-y-5">
            {SIGNAL_DATA.map((sig, i) => {
              const Trend = sig.trend === 'up' ? TrendingUp : TrendingDown;
              return (
                <div key={i}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-300 font-medium">{sig.name}</span>
                      <span className="text-[10px] text-indigo-400/60 bg-indigo-500/10 px-1.5 py-0.5 rounded font-bold">{sig.weight}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Trend className={`w-4 h-4 ${sig.trend === 'up' ? 'text-red-400' : 'text-emerald-400'}`} />
                      <span className="text-xs text-slate-500 tabular-nums">{sig.flagRate}% flag rate</span>
                    </div>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${sig.flagRate * 2}%` }}
                      transition={{ delay: 0.4 + i * 0.1, duration: 0.8, ease: 'easeOut' }}
                    />
                  </div>
                  <p className="text-xs text-slate-600 mt-1">Avg confidence score: {sig.avgScore.toFixed(2)}</p>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Recent Alerts */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="rounded-2xl border border-slate-800/80 overflow-hidden"
          style={{ backdropFilter: 'blur(12px)', background: 'rgba(15, 23, 42, 0.5)' }}
        >
          <div className="px-6 py-4 border-b border-slate-800/80">
            <h2 className="text-sm font-bold text-slate-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Live Threat Feed
            </h2>
          </div>
          <div className="divide-y divide-slate-800/60">
            {RECENT_ALERTS.map((alert, i) => {
              const cls = severityConfig[alert.severity as keyof typeof severityConfig];
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.08 }}
                  className="px-6 py-4 flex items-start gap-4"
                >
                  <span className={`mt-0.5 text-[10px] font-bold px-2 py-0.5 rounded border whitespace-nowrap ${cls}`}>
                    {alert.severity}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-300 leading-relaxed">{alert.msg}</p>
                    <p className="text-xs text-slate-600 mt-1">{alert.time}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
