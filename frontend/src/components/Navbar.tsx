import Link from 'next/link';
import { Sparkles } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-slate-950/50 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.5)]">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="text-xl font-semibold tracking-tight text-white">
            AI Spark
          </span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
          <Link href="#solutions" className="hover:text-white transition-colors">Solutions</Link>
          <Link href="#features" className="hover:text-white transition-colors">Features</Link>
          <Link href="#integrations" className="hover:text-white transition-colors">Integrations</Link>
          <Link href="#pricing" className="hover:text-white transition-colors">Pricing</Link>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="hidden md:block text-sm font-medium text-slate-300 hover:text-white transition-colors">
            Dashboard
          </Link>
          <Link href="#signup" className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/15 text-sm font-medium text-white border border-white/5 transition-all">
            Start Free Trial
          </Link>
        </div>
      </div>
    </nav>
  );
}
