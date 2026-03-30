import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import Features from "@/components/Features";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-50 flex flex-col items-center">
      <Navbar />
      <div className="w-full flex flex-col items-center justify-center flex-1">
        <Hero />
        <Features />
      </div>

      {/* Footer */}
      <footer className="w-full border-t border-slate-800/60 py-12 bg-slate-950/80">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between">
          <p className="text-slate-500 text-sm">© {new Date().getFullYear()} AI Spark. Intelligent KYC Pipeline.</p>
          <div className="flex gap-4 mt-4 md:mt-0 text-slate-400 text-sm">
            <span className="hover:text-slate-200 cursor-pointer">Privacy</span>
            <span className="hover:text-slate-200 cursor-pointer">Terms</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
