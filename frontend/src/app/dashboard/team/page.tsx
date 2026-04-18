'use client';

import { motion } from 'framer-motion';
import { Users, ExternalLink, Globe, Shield, Code2, Brain, Database } from 'lucide-react';

const TEAM = [
  {
    name: 'Astha Singh',
    role: 'Frontend Engineer',
    focus: 'Next.js · UI/UX · Dashboard Design',
    icon: Code2,
    color: 'from-orange-500 to-red-500',
    glow: 'bg-orange-500',
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
    color: 'from-cyan-500 to-blue-500',
    glow: 'bg-cyan-500',
    initials: 'SG',
  },
  {
    name: 'Neha Jamulla',
    role: 'Security & Compliance',
    focus: 'KYC Regulation · QR Cryptography · RBI Audit',
    icon: Shield,
    color: 'from-emerald-500 to-teal-500',
    glow: 'bg-emerald-500',
    initials: 'NJ',
  },
];

const HACKATHON = {
  name: 'National Hackathon',
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
        <h1 className="text-2xl font-bold text-stone-900 tracking-tight mb-1">Team Hub</h1>
        <p className="text-sm text-stone-500">The minds behind SecureAI-KYC — National Hackathon 2026.</p>
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
              className="relative p-6 rounded-2xl border border-stone-200 bg-white shadow-sm overflow-hidden group hover:border-stone-300 hover:shadow-md transition-all duration-300"
            >
              {/* Glow on hover */}
              <div className={`absolute top-0 right-0 w-32 h-32 ${member.glow}/5 blur-[60px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none`} />

              {/* Avatar */}
              <div className="relative mb-5">
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${member.color} flex items-center justify-center shadow-lg mb-1`}>
                  <span className="text-xl font-black text-white">{member.initials}</span>
                </div>
                <div className={`absolute -bottom-1 -right-1 w-7 h-7 rounded-lg bg-white border border-stone-200 flex items-center justify-center shadow-sm`}>
                  <Icon className="w-3.5 h-3.5 text-stone-600" />
                </div>
              </div>

              {/* Info */}
              <h3 className="text-base font-bold text-stone-900 mb-1">{member.name}</h3>
              <p className={`text-xs font-bold bg-gradient-to-r ${member.color} bg-clip-text text-transparent mb-3`}>
                {member.role}
              </p>
              <p className="text-xs text-stone-500 leading-relaxed">{member.focus}</p>

              {/* Social links (placeholder, keep it clean) */}
              <div className="flex items-center gap-2 mt-5">
                <button className="p-1.5 rounded-lg bg-stone-50 border border-stone-200 text-stone-400 hover:text-stone-700 hover:border-stone-300 transition-colors">
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
                <button className="p-1.5 rounded-lg bg-stone-50 border border-stone-200 text-stone-400 hover:text-stone-700 hover:border-stone-300 transition-colors">
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
        className="p-6 rounded-2xl border border-orange-200 bg-orange-50 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/5 blur-[80px] rounded-full pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-orange-500" />
              <span className="text-xs font-bold text-orange-600 uppercase tracking-widest">Hackathon Info</span>
            </div>
            <h2 className="text-xl font-bold text-stone-900 mb-1">{HACKATHON.project}</h2>
            <p className="text-sm text-stone-600">{HACKATHON.event}</p>
            <p className="text-sm text-stone-500 mt-0.5">{HACKATHON.name}</p>
          </div>
          <div className="grid grid-cols-2 gap-4 md:text-right">
            <div>
              <p className="text-xs text-stone-400 uppercase tracking-wider font-bold mb-1">Domain</p>
              <p className="text-sm text-stone-700 leading-relaxed">{HACKATHON.domain}</p>
            </div>
            <div>
              <p className="text-xs text-stone-400 uppercase tracking-wider font-bold mb-1">Jury Panel</p>
              <p className="text-sm text-stone-700">{HACKATHON.jury}</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
