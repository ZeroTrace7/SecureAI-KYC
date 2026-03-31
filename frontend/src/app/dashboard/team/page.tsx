'use client';

import { motion } from 'framer-motion';
import { Users, ExternalLink, Globe, Shield, Code2, Brain, Database } from 'lucide-react';

const TEAM = [
  {
    name: 'Astha Singh',
    role: 'Frontend Engineer',
    focus: 'Next.js · UI/UX · Dashboard Design',
    icon: Code2,
    color: 'from-indigo-500 to-purple-500',
    glow: 'bg-indigo-500',
    initials: 'AS',
  },
  {
    name: 'Yash Raj',
    role: 'AI / ML Engineer',
    focus: 'ELA Forensics · EXIF Analysis · Fraud Models',
    icon: Brain,
    color: 'from-purple-500 to-pink-500',
    glow: 'bg-purple-500',
    initials: 'YR',
  },
  {
    name: 'Shreyash Gupta',
    role: 'Backend Engineer',
    focus: 'FastAPI · Python · Pipeline Architecture',
    icon: Database,
    color: 'from-cyan-500 to-indigo-500',
    glow: 'bg-cyan-500',
    initials: 'SG',
  },
  {
    name: 'Neha Jamulla',
    role: 'Security & Compliance',
    focus: 'KYC Regulation · QR Cryptography · RBI Audit',
    icon: Shield,
    color: 'from-emerald-500 to-cyan-500',
    glow: 'bg-emerald-500',
    initials: 'NJ',
  },
];

const HACKATHON = {
  name: 'BITS Pilani Goa × IIT Madras',
  event: 'National AI Hackathon 2026',
  project: 'SecureAI-KYC',
  domain: 'FinTech · Document Forensics · Fraud Detection',
  jury: 'NPCI · DoT · Goa Police',
};

export default function TeamPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight mb-1">Team Hub</h1>
        <p className="text-sm text-slate-400">The minds behind SecureAI-KYC — BITS Pilani Goa × IIT Madras 2026.</p>
      </div>

      {/* Team Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
        {TEAM.map((member, i) => {
          const Icon = member.icon;
          return (
            <motion.div
              key={member.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="relative p-6 rounded-2xl border border-slate-800/80 overflow-hidden group hover:border-slate-600 transition-all duration-300"
              style={{ backdropFilter: 'blur(12px)', background: 'rgba(15, 23, 42, 0.6)' }}
            >
              {/* Glow on hover */}
              <div className={`absolute top-0 right-0 w-32 h-32 ${member.glow}/10 blur-[60px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none`} />

              {/* Avatar */}
              <div className="relative mb-5">
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${member.color} flex items-center justify-center shadow-lg mb-1`}>
                  <span className="text-xl font-black text-white">{member.initials}</span>
                </div>
                <div className={`absolute -bottom-1 -right-1 w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center`}>
                  <Icon className="w-3.5 h-3.5 text-slate-300" />
                </div>
              </div>

              {/* Info */}
              <h3 className="text-base font-bold text-white mb-1">{member.name}</h3>
              <p className={`text-xs font-bold bg-gradient-to-r ${member.color} bg-clip-text text-transparent mb-3`}>
                {member.role}
              </p>
              <p className="text-xs text-slate-500 leading-relaxed">{member.focus}</p>

              {/* Social links (placeholder, keep it clean) */}
              <div className="flex items-center gap-2 mt-5">
                <button className="p-1.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-slate-500 hover:text-slate-300 hover:border-slate-500 transition-colors">
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
                <button className="p-1.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-slate-500 hover:text-slate-300 hover:border-slate-500 transition-colors">
                  <Globe className="w-3.5 h-3.5" />
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Hackathon Info Card */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="p-6 rounded-2xl border border-indigo-500/20 bg-indigo-500/5 relative overflow-hidden"
        style={{ backdropFilter: 'blur(12px)' }}
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-[80px] rounded-full pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-indigo-400" />
              <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">Hackathon Info</span>
            </div>
            <h2 className="text-xl font-bold text-white mb-1">{HACKATHON.project}</h2>
            <p className="text-sm text-slate-400">{HACKATHON.event}</p>
            <p className="text-sm text-slate-500 mt-0.5">{HACKATHON.name}</p>
          </div>
          <div className="grid grid-cols-2 gap-4 md:text-right">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Domain</p>
              <p className="text-sm text-slate-300 leading-relaxed">{HACKATHON.domain}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Jury Panel</p>
              <p className="text-sm text-slate-300">{HACKATHON.jury}</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
