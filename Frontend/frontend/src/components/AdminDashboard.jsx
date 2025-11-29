import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  RefreshCw, 
  Database, 
  Server, 
  Shield, 
  Cpu,
  Globe,
  Zap
} from 'lucide-react';

// Mock Backend for Admin Stats (simulating the one from original App.jsx)
const MockBackend = {
  ingest: async () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: "ok",
          ingested: {
            news: Math.floor(Math.random() * 50) + 10,
            gov: Math.floor(Math.random() * 20) + 5,
            factchecks: Math.floor(Math.random() * 10) + 1,
            social: Math.floor(Math.random() * 100) + 20
          },
          last_synced: new Date().toISOString()
        });
      }, 2000);
    });
  }
};

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    MockBackend.ingest().then(setStats);
  }, []);

  const handleSync = async () => {
    setLoading(true);
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] Initiating sync sequence...`, ...prev]);
    try {
      const data = await MockBackend.ingest();
      setStats(data);
      setLogs(prev => [`[${new Date().toLocaleTimeString()}] Sync completed successfully.`, ...prev]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto pt-8 animate-fade-in text-slate-300 relative z-10 px-4 pb-12">
      <div className="mb-12 border-b border-white/5 pb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
           <h2 className="text-4xl font-bold text-white mb-3 tracking-tight">System Status</h2>
           <p className="text-sm text-slate-500">Real-time overview of verification nodes and knowledge base.</p>
        </div>
        <div className="flex items-center gap-3 bg-emerald-500/10 px-5 py-2.5 rounded-2xl border border-emerald-500/20 backdrop-blur-md shadow-lg shadow-emerald-500/5">
           <div className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </div>
           <span className="text-emerald-400 text-xs font-bold uppercase tracking-wide">All Systems Operational</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Sync Control Panel */}
        <div className="bg-white/[0.02] border border-white/10 p-8 rounded-[2rem] backdrop-blur-xl shadow-2xl flex flex-col h-full relative overflow-hidden group">
           <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 blur-[100px] rounded-full pointer-events-none"></div>
           
           <div className="flex items-center justify-between mb-8 relative z-10">
             <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <RefreshCw size={14} /> Data Ingestion
             </h3>
             <Activity size={18} className="text-indigo-400" />
           </div>
           
           <div className="flex-grow flex flex-col justify-center mb-8 relative z-10">
             <div className="text-center mb-6">
                <div className="text-5xl font-bold text-white mb-2 tracking-tighter">
                    {loading ? <span className="animate-pulse">...</span> : "Idle"}
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider font-medium">Current State</div>
             </div>

             <button 
                onClick={handleSync}
                disabled={loading}
                className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl text-sm font-bold tracking-wide uppercase transition-all flex justify-center items-center gap-3 shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
             >
                {loading ? <RefreshCw className="animate-spin" size={18}/> : <Zap size={18} className="fill-current"/>}
                {loading ? 'Syncing Databases...' : 'Trigger Manual Sync'}
             </button>
           </div>

           <div className="mt-auto relative z-10">
              <h4 className="text-[10px] text-slate-500 uppercase tracking-widest mb-4 font-bold">System Logs</h4>
              <div className="p-5 bg-[#050508]/60 rounded-2xl border border-white/5 font-mono text-[10px] text-indigo-300/80 h-48 overflow-y-auto custom-scrollbar shadow-inner backdrop-blur-sm">
                  {logs.length === 0 && <div className="text-slate-600 italic flex items-center gap-2"><Server size={12}/> No recent activity logged.</div>}
                  {logs.map((l, i) => (
                    <div key={i} className="mb-2.5 border-b border-white/5 pb-2.5 last:border-0 last:pb-0 flex gap-2">
                        <span className="text-slate-600">{'>'}</span> {l}
                    </div>
                  ))}
              </div>
           </div>
        </div>

        {/* Metrics Grid */}
        <div className="lg:col-span-2 flex flex-col gap-8">
            
            {/* Knowledge Base Stats */}
            <div className="bg-white/[0.02] border border-white/10 p-8 rounded-[2rem] backdrop-blur-xl shadow-2xl relative overflow-hidden">
                <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-indigo-500/5 to-transparent pointer-events-none"></div>
                
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                        <Database size={14} /> Knowledge Base Metrics
                    </h3>
                    <span className="text-[10px] bg-white/5 px-2 py-1 rounded text-slate-500">Last Updated: {stats ? new Date(stats.last_synced).toLocaleTimeString() : '--:--'}</span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
                    {stats && Object.entries(stats.ingested).map(([key, val]) => (
                        <div key={key} className="bg-white/[0.03] p-6 rounded-3xl border border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.06] transition-all group relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                                {key === 'news' && <Globe size={32} />}
                                {key === 'gov' && <Shield size={32} />}
                                {key === 'factchecks' && <CheckCircle size={32} />}
                                {key === 'social' && <Share2 size={32} />}
                            </div>
                            <div className="text-4xl font-bold text-white group-hover:text-indigo-300 transition-colors mb-2">{val}</div>
                            <div className="text-[10px] uppercase text-slate-500 font-bold tracking-wider">{key}</div>
                        </div>
                    ))}
                    {!stats && [1,2,3,4].map(i => (
                        <div key={i} className="bg-white/[0.02] p-6 rounded-3xl border border-white/5 animate-pulse h-32"></div>
                    ))}
                </div>
            </div>

            {/* Server Health (New Feature) */}
            <div className="bg-white/[0.02] border border-white/10 p-8 rounded-[2rem] backdrop-blur-xl shadow-2xl flex-grow">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                        <Cpu size={14} /> Node Health
                    </h3>
                </div>
                
                <div className="space-y-4">
                    {[
                        { name: "Inference Engine (Gemini Pro)", status: "Operational", lat: "45ms", load: "12%" },
                        { name: "Vector Database (ChromaDB)", status: "Operational", lat: "12ms", load: "08%" },
                        { name: "Ingestion Pipeline", status: "Idle", lat: "-", load: "0%" },
                    ].map((node, idx) => (
                        <div key={idx} className="flex items-center justify-between p-4 bg-white/[0.02] rounded-2xl border border-white/5 hover:border-white/10 transition-colors">
                            <div className="flex items-center gap-4">
                                <div className={`w-2 h-2 rounded-full ${node.status === 'Operational' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-500'}`}></div>
                                <div>
                                    <div className="text-sm font-medium text-slate-200">{node.name}</div>
                                    <div className="text-[10px] text-slate-500 font-mono mt-0.5">LATENCY: {node.lat}</div>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className={`text-xs font-bold ${node.status === 'Operational' ? 'text-emerald-400' : 'text-slate-500'}`}>{node.status}</div>
                                <div className="text-[10px] text-slate-500 font-mono mt-0.5">LOAD: {node.load}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

// Helper icons for the map above
import { CheckCircle, Share2 } from 'lucide-react';

export default AdminDashboard;
