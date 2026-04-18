import Sidebar from '@/components/dashboard/Sidebar';
import Topbar from '@/components/dashboard/Topbar';
import { DocumentProvider } from '@/context/DocumentContext';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen w-full bg-stone-50 text-stone-900 overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar />
      
      {/* Main Workspace Area */}
      <div className="flex flex-col flex-1 h-full w-full">
        {/* Topbar */}
        <Topbar />
        
        {/* Content Area */}
        <main className="flex-1 overflow-y-auto px-6 py-8 relative">
          {/* Subtle glow behind dashboard content */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-lg h-96 bg-orange-500/5 blur-[100px] pointer-events-none rounded-full" />
          <div className="relative z-10 max-w-7xl mx-auto h-full">
            <DocumentProvider>
              {children}
            </DocumentProvider>
          </div>
        </main>
      </div>
    </div>
  );
}
