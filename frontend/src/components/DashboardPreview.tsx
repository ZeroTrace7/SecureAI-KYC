import { ShieldAlert, ShieldCheck, Activity, Users, Search, Bell } from 'lucide-react';

export default function DashboardPreview() {
  return (
    <div className="w-full max-w-5xl mx-auto mt-20 relative">
      {/* Glow Effects */}
      <div className="absolute -inset-1 bg-gradient-to-tr from-orange-500/15 via-red-500/15 to-amber-500/15 rounded-3xl blur-2xl" />
      
      {/* Dashboard container */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-xl border border-stone-200 shadow-2xl p-4 sm:p-6 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-stone-200">
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 bg-orange-50 rounded border border-orange-200 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-orange-500" />
            </div>
            <h2 className="text-stone-800 font-medium">Risk Overview</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-stone-50 rounded-md border border-stone-200">
              <Search className="w-4 h-4 text-stone-400" />
              <span className="text-sm text-stone-400">Search documents...</span>
            </div>
            <Bell className="w-5 h-5 text-stone-400" />
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total Processed', value: '4,102', trend: '+12%', color: 'text-stone-800' },
            { label: 'Pending Review', value: '23', trend: '-2%', color: 'text-yellow-600' },
            { label: 'Auto-Approved', value: '3,840', trend: '+15%', color: 'text-green-600' },
            { label: 'Rejected (Fake)', value: '239', trend: '+5%', color: 'text-red-500' },
          ].map((stat, i) => (
            <div key={i} className="p-4 rounded-xl bg-stone-50 border border-stone-200">
              <p className="text-sm tracking-wide text-stone-500 mb-2">{stat.label}</p>
              <div className="flex items-end justify-between">
                <span className={`text-2xl font-semibold ${stat.color}`}>{stat.value}</span>
                <span className="text-xs text-green-600 font-medium">{stat.trend}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Panel */}
          <div className="md:col-span-2 space-y-6">
            <div className="p-6 rounded-xl bg-stone-50 border border-stone-200 h-64 relative overflow-hidden">
               <h3 className="text-sm font-medium text-stone-700 mb-4">Fraud Score Trend</h3>
               <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-orange-500/10 to-transparent flex items-end px-6 pb-6 gap-2">
                 {/* Fake Chart Bars */}
                 {[40, 65, 30, 80, 45, 20, 90, 50, 60, 30, 40, 70].map((h, i) => (
                   <div key={i} className="flex-1 rounded-t-sm bg-orange-500/30 hover:bg-orange-400/50 transition-colors" style={{ height: `${h}%` }}></div>
                 ))}
               </div>
            </div>
            
            <div className="bg-white border border-stone-200 rounded-xl overflow-hidden shadow-sm">
               <div className="p-4 border-b border-stone-200 flex items-center justify-between">
                 <h3 className="text-sm font-medium text-stone-700">Recent Validations</h3>
               </div>
               <div className="p-4 space-y-3">
                 {[
                   { name: 'Aadhaar Card - John Doe', id: 'DOC-1029', status: 'Forged', score: 92 },
                   { name: 'PAN Card - Jane Smith', id: 'DOC-1028', status: 'Clean', score: 12 },
                   { name: 'Passport - M. Kumar', id: 'DOC-1027', status: 'Manual', score: 48 },
                 ].map((doc, i) => (
                   <div key={i} className="flex items-center justify-between p-3 rounded-lg hover:bg-stone-50 transition-colors border border-transparent hover:border-stone-200">
                     <div className="flex items-center gap-3">
                       <div className="h-8 w-8 rounded bg-stone-100 flex items-center justify-center">
                         <Activity className="w-4 h-4 text-stone-600" />
                       </div>
                       <div>
                         <p className="text-sm font-medium text-stone-800">{doc.name}</p>
                         <p className="text-xs text-stone-400">{doc.id}</p>
                       </div>
                     </div>
                     <div className="flex items-center gap-4">
                       <span className={`text-xs px-2 py-1 rounded border font-medium
                         ${doc.status === 'Forged' ? 'bg-red-50 border-red-200 text-red-600' : 
                           doc.status === 'Clean' ? 'bg-green-50 border-green-200 text-green-600' : 
                           'bg-yellow-50 border-yellow-200 text-yellow-600'}`}>
                         {doc.status}
                       </span>
                       <span className="text-sm font-semibold text-stone-700 w-8 text-right">{doc.score}</span>
                     </div>
                   </div>
                 ))}
               </div>
            </div>
          </div>

          {/* Right Panel: Risk Flagging */}
          <div className="p-5 rounded-xl bg-stone-50 border border-stone-200">
            <h3 className="text-sm font-medium text-stone-700 mb-4">Live Threat Insights</h3>
            
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-red-50 border border-red-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-red-500" />
                    <span className="text-sm font-medium text-red-700">High Risk Score</span>
                  </div>
                  <span className="text-lg font-bold text-red-500">89</span>
                </div>
                <p className="text-xs text-stone-500 mb-3">Found multiple anomalies in DOC-1033. EXIF metadata mismatch and layout tampering detected.</p>
                <div className="h-1.5 w-full bg-stone-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-red-600 to-red-400 w-[89%] rounded-full"></div>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-yellow-50 border border-yellow-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-yellow-600" />
                    <span className="text-sm font-medium text-yellow-700">Blur Detected</span>
                  </div>
                </div>
                <p className="text-xs text-stone-500">DOC-1044 rejected at Integrity Validation Layer (Laplacian variance low).</p>
              </div>
              
              <div className="p-4 rounded-lg bg-white border border-stone-200 shadow-sm">
                 <h4 className="text-xs font-medium text-stone-700 mb-3">Model Accuracy</h4>
                 <div className="space-y-2">
                   {['OCR Field Matching', 'Face Alignment', 'QR Decoding'].map((lbl, i) => (
                     <div key={i} className="space-y-1">
                       <div className="flex justify-between text-xs text-stone-500">
                         <span>{lbl}</span>
                         <span>99.{i + 7}%</span>
                       </div>
                       <div className="h-1 w-full bg-stone-200 rounded-full">
                         <div className="h-full bg-orange-500 rounded-full" style={{ width: `99.${i + 7}%` }}></div>
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
