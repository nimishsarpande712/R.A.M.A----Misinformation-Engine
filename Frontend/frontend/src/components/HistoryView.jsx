import React from 'react';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  ChevronDown 
} from 'lucide-react';

const HistoryView = ({ history, onLoadItem }) => {
  return (
    <div className="max-w-5xl mx-auto pt-8 animate-fade-in text-slate-300 relative z-10 px-4 pb-12">
      <div className="flex items-center justify-between mb-10 border-b border-white/5 pb-8">
        <div>
          <h2 className="text-4xl font-bold text-white mb-3 tracking-tight">Archive</h2>
          <p className="text-slate-500 text-sm">Previous verifications and outcomes.</p>
        </div>
        <div className="text-right">
           <span className="bg-white/5 border border-white/10 px-5 py-2.5 rounded-xl text-xs font-mono text-indigo-300 backdrop-blur-md shadow-sm">{history.length} ENTRIES</span>
        </div>
      </div>
      
      {history.length === 0 ? (
        <div className="text-center py-24 bg-white/[0.02] rounded-[2rem] border border-white/5 border-dashed backdrop-blur-sm">
          <Clock size={56} className="mx-auto text-slate-700 mb-6 opacity-50"/>
          <h3 className="text-xl font-medium text-slate-400">Archive Empty</h3>
        </div>
      ) : (
        <div className="grid gap-5">
          {history.map((item, idx) => (
            <div 
              key={idx} 
              onClick={() => onLoadItem(item)}
              className="bg-white/[0.02] p-6 rounded-[1.5rem] border border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.04] transition-all cursor-pointer group flex items-start gap-6 relative overflow-hidden backdrop-blur-md shadow-sm hover:shadow-lg hover:shadow-indigo-500/5"
            >
              {/* Hover Highlight */}
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/0 via-indigo-500/5 to-indigo-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

              <div className={`mt-1 shrink-0 w-12 h-12 rounded-2xl flex items-center justify-center border shadow-lg transition-transform group-hover:scale-110 duration-300 ${item.verdict === 'true' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 shadow-emerald-500/10' : item.verdict === 'false' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400 shadow-rose-500/10' : 'bg-slate-700/20 border-slate-600/30 text-slate-500'}`}>
                {item.verdict === 'true' ? <CheckCircle size={20}/> : item.verdict === 'false' ? <XCircle size={20}/> : <AlertTriangle size={20}/>}
              </div>

              <div className="flex-grow min-w-0 relative z-10">
                 <div className="flex justify-between items-center mb-2">
                    <span className={`text-xs font-bold uppercase tracking-widest px-2 py-1 rounded-lg bg-white/5 ${item.verdict === 'true' ? 'text-emerald-400' : item.verdict === 'false' ? 'text-rose-400' : 'text-slate-400'}`}>
                      {item.verdict}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">{new Date(item.timestamp).toLocaleDateString()}</span>
                 </div>
                 <h4 className="text-slate-200 font-medium truncate group-hover:text-white transition-colors text-lg leading-snug">
                   {item.query_text}
                 </h4>
              </div>
              
              <div className="self-center shrink-0 text-slate-700 group-hover:text-indigo-400 transition-colors relative z-10 p-2 rounded-full group-hover:bg-white/5">
                 <ChevronDown className="transform -rotate-90" size={20} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryView;
