import { ShieldCheck, Crosshair, BookOpen, Fingerprint, RefreshCcw, Database } from 'lucide-react';

export default function Features() {
  const features = [
    {
      title: 'Integrity Validation',
      description: 'Acts as a computational shield. Immediately rejects corrupted, highly blurred, or low-resolution images before compute processing.',
      icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />
    },
    {
      title: 'Type & Layout Detection',
      description: 'Routes the document to correct ML pipelines via OCR keywords, aspect ratios, and precise spatial layout analysis.',
      icon: <Crosshair className="w-6 h-6 text-blue-400" />
    },
    {
      title: 'Multi-Agent Forgery Engine',
      description: 'Parallel checks for pixel tampering, Error Level Analysis (ELA), EXIF metadata forensics, and font splicing.',
      icon: <Fingerprint className="w-6 h-6 text-purple-400" />
    },
    {
      title: 'Cross-Validation Layer',
      description: 'The moat. Correlates extracted OCR printed fields against embedded QR datasets and EXIF timestamps to unmask deeper anomalies.',
      icon: <RefreshCcw className="w-6 h-6 text-indigo-400" />
    },
    {
      title: 'Predictive Fraud Scoring',
      description: 'Aggregates multi-lateral signals into a standardized 0-100 risk score, managing dynamic confidence weights actively.',
      icon: <BookOpen className="w-6 h-6 text-rose-400" />
    },
    {
      title: 'Explainable Auditing',
      description: 'Return rich payloads, visual heatmaps, and clear categorization (Genuine, Suspicious, Fake) for strict banking compliance.',
      icon: <Database className="w-6 h-6 text-amber-400" />
    }
  ];

  return (
    <section id="features" className="py-24 relative w-full border-t border-slate-800/60 bg-slate-950/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-medium text-indigo-400 uppercase tracking-wider mb-3">Platform Capabilities</h2>
          <h3 className="text-3xl md:text-4xl font-bold text-white mb-4">Everything you need to secure onboarding, out of the box.</h3>
          <p className="text-slate-400 text-lg">Replace disjointed APIs and manual reviews with a unified intelligence engine.</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <div key={i} className="group p-8 rounded-2xl bg-gradient-to-b from-slate-800/40 to-slate-900/40 border border-slate-700/50 hover:bg-slate-800/60 hover:border-indigo-500/30 transition-all hover:-translate-y-1">
              <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center mb-6 shadow-inner border border-white/5">
                {feature.icon}
              </div>
              <h4 className="text-xl font-semibold text-slate-200 mb-3">{feature.title}</h4>
              <p className="text-slate-400 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
