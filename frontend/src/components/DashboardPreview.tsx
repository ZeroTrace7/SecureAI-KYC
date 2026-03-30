import { ShieldAlert, ShieldCheck, Activity, Users, Search, Bell } from 'lucide-react';

export default function DashboardPreview() {
  return (
    <div className="w-full max-w-5xl mx-auto mt-20 relative">
      {/* Glow Effects */}
      <div className="absolute -inset-1 bg-gradient-to-tr from-indigo-500/20 via-purple-500/20 to-blue-500/20 rounded-3xl blur-2xl" />
      
      {/* Dashboard container */}
      <div className="relative rounded-2xl bg-slate-900/60 backdrop-blur-xl border border-slate-800 shadow-2xl p-4 sm:p-6 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-800/60">
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 bg-indigo-500/20 rounded border border-indigo-500/30 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-indigo-400" />
            </div>
            <h2 className="text-slate-200 font-medium">Risk Overview</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded-md border border-slate-700/50">
              <Search className="w-4 h-4 text-slate-400" />
              <span className="text-sm text-slate-400">Search documents...</span>
            </div>
            <Bell className="w-5 h-5 text-slate-400" />
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total Processed', value: '4,102', trend: '+12%', color: 'text-slate-200' },
            { label: 'Pending Review', value: '23', trend: '-2%', color: 'text-yellow-400' },
            { label: 'Auto-Approved', value: '3,840', trend: '+15%', color: 'text-green-400' },
            { label: 'Rejected (Fake)', value: '239', trend: '+5%', color: 'text-red-400' },
          ].map((stat, i) => (
            <div key={i} className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <p className="text-sm tracking-wide text-slate-400 mb-2">{stat.label}</p>
              <div className="flex items-end justify-between">
                <span className={`text-2xl font-semibold ${stat.color}`}>{stat.value}</span>
                <span className="text-xs text-green-400 font-medium">{stat.trend}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Panel */}
          <div className="md:col-span-2 space-y-6">
            <div className="p-6 rounded-xl bg-slate-800/40 border border-slate-700/50 h-64 relative overflow-hidden">
               <h3 className="text-sm font-medium text-slate-300 mb-4">Fraud Score Trend</h3>
               <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-indigo-500/10 to-transparent flex items-end px-6 pb-6 gap-2">
                 {/* Fake Chart Bars */}
                 {[40, 65, 30, 80, 45, 20, 90, 50, 60, 30, 40, 70].map((h, i) => (
                   <div key={i} className="flex-1 rounded-t-sm bg-indigo-500/40 hover:bg-indigo-400/60 transition-colors" style={{ height: `${h}%` }}></div>
                 ))}
               </div>
            </div>
            
            <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl overflow-hidden">
               <div className="p-4 border-b border-slate-700/50 flex items-center justify-between">
                 <h3 className="text-sm font-medium text-slate-300">Recent Validations</h3>
               </div>
               <div className="p-4 space-y-3">
                 {[
                   { name: 'Aadhaar Card - John Doe', id: 'DOC-1029', status: 'Forged', score: 92 },
                   { name: 'PAN Card - Jane Smith', id: 'DOC-1028', status: 'Clean', score: 12 },
                   { name: 'Passport - M. Kumar', id: 'DOC-1027', status: 'Manual', score: 48 },
                 ].map((doc, i) => (
                   <div key={i} className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-700/30 transition-colors border border-transparent hover:border-slate-600/50">
                     <div className="flex items-center gap-3">
                       <div className="h-8 w-8 rounded bg-slate-700/50 flex items-center justify-center">
                         <Activity className="w-4 h-4 text-slate-300" />
                       </div>
                       <div>
                         <p className="text-sm font-medium text-slate-200">{doc.name}</p>
                         <p className="text-xs text-slate-500">{doc.id}</p>
                       </div>
                     </div>
                     <div className="flex items-center gap-4">
                       <span className={`text-xs px-2 py-1 rounded border font-medium
                         ${doc.status === 'Forged' ? 'bg-red-500/10 border-red-500/20 text-red-400' : 
                           doc.status === 'Clean' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 
                           'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'}`}>
                         {doc.status}
                       </span>
                       <span className="text-sm font-semibold text-slate-300 w-8 text-right">{doc.score}</span>
                     </div>
                   </div>
                 ))}
               </div>
            </div>
          </div>

          {/* Right Panel: Risk Flagging */}
          <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/50">
            <h3 className="text-sm font-medium text-slate-300 mb-4">Live Threat Insights</h3>
            
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-red-500/5 border border-red-500/20">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-red-400" />
                    <span className="text-sm font-medium text-red-200">High Risk Score</span>
                  </div>
                  <span className="text-lg font-bold text-red-400">89</span>
                </div>
                <p className="text-xs text-slate-400 mb-3">Found multiple anomalies in DOC-1033. EXIF metadata mismatch and layout tampering detected.</p>
                <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-red-600 to-red-400 w-[89%] rounded-full"></div>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-yellow-500/5 border border-yellow-500/20">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm font-medium text-yellow-200">Blur Detected</span>
                  </div>
                </div>
                <p className="text-xs text-slate-400">DOC-1044 rejected at Integrity Validation Layer (Laplacian variance low).</p>
              </div>
              
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                 <h4 className="text-xs font-medium text-slate-300 mb-3">Model Accuracy</h4>
                 <div className="space-y-2">
                   {['OCR Field Matching', 'Face Alignment', 'QR Decoding'].map((lbl, i) => (
                     <div key={i} className="space-y-1">
                       <div className="flex justify-between text-xs text-slate-400">
                         <span>{lbl}</span>
                         <span>99.{i + 7}%</span>
                       </div>
                       <div className="h-1 w-full bg-slate-900 rounded-full">
                         <div className="h-full bg-indigo-500 rounded-full" style={{ width: `99.${i + 7}%` }}></div>
                       </div>
                     </div>
                   ))}
                 </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
