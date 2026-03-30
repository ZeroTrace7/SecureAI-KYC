import DashboardPreview from './DashboardPreview';
import { ArrowRight, Play } from 'lucide-react';

export default function Hero() {
  return (
    <section className="relative pt-32 pb-20 lg:pt-48 overflow-hidden z-10 w-full">
      <div className="max-w-7xl mx-auto px-6 text-center">
        
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-8">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
          </span>
          Next-Gen Document Intelligence Layer
        </div>
        
        {/* Main Headline */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6">
          The operating system for <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
            modern KYC & Fraud Detection
          </span>
        </h1>
        
        {/* Subtitle */}
        <p className="max-w-2xl mx-auto text-lg text-slate-400 mb-10 leading-relaxed">
          AI Spark centralizes document verification, forgery detection, and multi-agent cross-validation in one seamless pipeline. Replace manual checks with instant, intelligent certainty.
        </p>
        
        {/* Calls to Action */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <button className="group px-8 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-all w-full sm:w-auto flex items-center justify-center gap-2">
            Start Free Trial
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
          
          <button className="px-8 py-3 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 text-slate-300 font-medium transition-all w-full sm:w-auto flex items-center justify-center gap-2">
            <Play className="w-4 h-4" />
            Watch Demo
          </button>
        </div>

        {/* Mockup Dashboard */}
        <DashboardPreview />
        
      </div>
    </section>
  );
}
