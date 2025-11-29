import React, { useState } from 'react';
import { 
  Database, 
  ShieldCheck, 
  Cpu, 
  ChevronUp, 
  ChevronDown,
  Share2,
  Copy,
  Check
} from 'lucide-react';
import { COLORS } from '../constants';

const ResultDetails = ({ result }) => {
  const theme = COLORS[result.verdict] || COLORS.unverified;
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleShare = () => {
    const text = `Fact Check Result: ${result.verdict.toUpperCase()}\n\n${result.explanation}\n\nVerified by R.A.M.A.`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="animate-fade-in-up space-y-6">
       {/* Verdict Section */}
       <div className={`p-8 rounded-[2rem] border ${theme.border} ${theme.bg} relative overflow-hidden backdrop-blur-xl shadow-2xl`}>
          {/* Ambient Glow */}
          <div className={`absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-white/10 to-transparent blur-3xl opacity-40 pointer-events-none`}></div>
          
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-6">
              <div className={`inline-flex items-center px-5 py-2 rounded-full text-xs font-bold uppercase tracking-wider ${theme.badge} backdrop-blur-md shadow-lg`}>
                <theme.icon size={16} className="mr-2" />
                {result.verdict}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-mono text-slate-400 bg-black/20 px-3 py-1 rounded-full border border-white/5">
                  {new Date(result.timestamp).toLocaleTimeString()}
                </span>
                <button 
                  onClick={handleShare}
                  className="p-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/5 text-slate-400 hover:text-white transition-all"
                  title="Copy to clipboard"
                >
                  {copied ? <Check size={14} className="text-emerald-400"/> : <Share2 size={14}/>}
                </button>
              </div>
            </div>
            
            <p className="text-slate-100 text-xl leading-relaxed font-medium tracking-tight">
               {result.explanation}
            </p>
          </div>
       </div>

       {/* Sources Section */}
       <div>
         <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-4 block flex items-center gap-2 pl-2">
            <Database size={12} /> Sources Found
         </label>
         <div className="grid gap-4">
           {result.sources_used.map((source, idx) => {
             // Determine credibility badge styling
             const credibilityScore = source.credibility_score || 0.5;
             const isVerified = source.is_verified_source || false;
             
             let credibilityColor = 'bg-slate-500/10 text-slate-400 border-slate-500/20';
             if (credibilityScore >= 0.85) {
               credibilityColor = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
             } else if (credibilityScore >= 0.7) {
               credibilityColor = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
             } else if (credibilityScore >= 0.5) {
               credibilityColor = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
             } else {
               credibilityColor = 'bg-red-500/10 text-red-400 border-red-500/20';
             }
             
             return (
               <a key={idx} href={source.url} target="_blank" rel="noreferrer" className="flex flex-col sm:flex-row sm:items-start justify-between bg-white/[0.02] border border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.04] p-5 rounded-3xl transition-all group relative overflow-hidden backdrop-blur-md">
                  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-indigo-500/0 group-hover:bg-indigo-500/50 transition-colors"></div>
                  <div className="flex-1 min-w-0 mr-4">
                     <div className="flex items-center gap-2 mb-2">
                       <h4 className="text-base text-indigo-200 font-medium truncate">{source.source}</h4>
                       {isVerified && (
                         <ShieldCheck size={16} className="text-emerald-400 shrink-0" title="Verified Source" />
                       )}
                     </div>
                     <p className="text-sm text-slate-500 mt-1 group-hover:text-slate-400 line-clamp-2 leading-relaxed">{source.snippet}</p>
                     <div className="flex gap-2 mt-3 flex-wrap">
                       <span className={`text-[10px] font-mono px-2.5 py-1 rounded-lg border ${credibilityColor}`}>
                         CREDIBILITY: {(credibilityScore * 100).toFixed(0)}%
                       </span>
                       <span className="text-[10px] font-mono px-2.5 py-1 rounded-lg border bg-indigo-500/10 text-indigo-400 border-indigo-500/20">
                         {source.type.toUpperCase()}
                       </span>
                     </div>
                  </div>
               </a>
             );
           })}
         </div>
       </div>

       {/* Reasoning Trace */}
       <div className="pt-4">
          <button 
            onClick={() => setExpanded(!expanded)} 
            className="w-full flex justify-between items-center px-6 py-4 bg-white/[0.02] border border-white/5 rounded-2xl text-xs font-medium text-slate-400 hover:text-indigo-300 hover:border-white/10 transition-all group backdrop-blur-md"
          >
             <span className="flex items-center gap-3">
               <Cpu size={16} className="group-hover:text-indigo-400 transition-colors" />
               View Neural Reasoning Trace
             </span>
             {expanded ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
          </button>
          
          {expanded && (
            <div className="mt-3 p-6 bg-[#050508]/80 rounded-2xl border border-white/10 text-xs font-mono text-indigo-300/80 whitespace-pre-wrap leading-relaxed shadow-inner backdrop-blur-xl">
               <div className="flex items-center gap-2 mb-4 text-slate-600 border-b border-white/5 pb-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-700"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-700"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-700"></span>
               </div>
               {result.raw_answer}
            </div>
          )}
       </div>
    </div>
  );
};

export default ResultDetails;
