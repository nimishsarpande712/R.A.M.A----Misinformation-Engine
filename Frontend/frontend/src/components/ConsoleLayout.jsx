import React from 'react';
import { 
  Search, 
  ChevronDown, 
  Globe, 
  FileText, 
  RefreshCw, 
  Zap, 
  Trash2, 
  Activity, 
  ShieldCheck,
  TrendingUp
} from 'lucide-react';
import ResultDetails from './ResultDetails';
import { CATEGORIES, LANGUAGES } from '../constants';

const ConsoleLayout = ({ 
  inputText, setInputText, category, setCategory, language, setLanguage, 
  onSubmit, isLoading, result, onClear
}) => {
  const suggestions = [
    { label: "Health", text: "New vaccine causes severe side effects according to 2024 leaked report." },
    { label: "Elections", text: "Phase 1 election voter turnout was only 40% in most districts." },
    { label: "Alerts", text: "Red alert issued for Mumbai coast due to approaching cyclone." },
  ];

  const trendingTopics = [
    "Election Phase 2", "Cyclone Dana", "UPI Tax Hoax", "New Health Guidelines"
  ];

  return (
    <div className="w-full max-w-7xl mx-auto pt-6 animate-fade-in relative z-10">
       <div className="mb-12 text-center lg:text-left flex flex-col lg:flex-row justify-between items-end gap-6">
         <div>
            <h1 className="text-5xl md:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-indigo-100 to-indigo-200/50 mb-4 tracking-tight drop-shadow-sm">
              Fact-Checking Cockpit
            </h1>
            <p className="text-slate-400 text-base max-w-2xl leading-relaxed">
              Advanced misinformation detection engine powered by multi-source verification.
            </p>
         </div>
         
         {/* New Feature: Trending Ticker */}
         <div className="hidden lg:flex items-center gap-3 bg-white/5 border border-white/10 px-5 py-3 rounded-2xl backdrop-blur-md">
            <div className="flex items-center gap-2 text-indigo-400 font-bold text-xs uppercase tracking-wider border-r border-white/10 pr-3">
                <TrendingUp size={14} />
                Trending
            </div>
            <div className="flex gap-4 text-xs text-slate-400 font-medium">
                {trendingTopics.map((t, i) => (
                    <span key={i} className="hover:text-white cursor-pointer transition-colors">#{t.replace(/\s/g, '')}</span>
                ))}
            </div>
         </div>
       </div>

       <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 min-h-[650px]">
          
          {/* LEFT PANEL: INPUT */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <div className="bg-white/[0.02] backdrop-blur-2xl border border-white/[0.08] rounded-[2.5rem] p-1.5 shadow-2xl relative group ring-1 ring-white/5 transition-all hover:ring-white/10">
              
              {/* Inner Card */}
              <div className="bg-[#0a0a0f]/60 rounded-[2rem] p-8 h-full flex flex-col relative overflow-hidden backdrop-blur-xl">
                
                {/* Header */}
                <div className="flex items-center justify-between mb-8 pb-6 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
                      <Search size={18} className="text-indigo-400" />
                    </div>
                    <h2 className="text-base font-semibold text-white tracking-wide">Analysis Parameters</h2>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400 px-3 py-1.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    SYSTEM READY
                  </span>
                </div>
                
                {/* Selectors */}
                <div className="grid grid-cols-2 gap-5 mb-6">
                    <div className="space-y-2.5">
                      <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider pl-1">Category</label>
                      <div className="relative group/select">
                        <select 
                          value={category}
                          onChange={(e) => setCategory(e.target.value)}
                          className="w-full bg-[#15151a]/80 border border-white/10 rounded-2xl py-3.5 px-4 text-sm text-slate-200 focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all hover:bg-[#1a1a20] appearance-none cursor-pointer backdrop-blur-md"
                        >
                          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                        <ChevronDown size={16} className="absolute right-4 top-4 text-slate-500 pointer-events-none group-hover/select:text-indigo-400 transition-colors" />
                      </div>
                    </div>
                    <div className="space-y-2.5">
                      <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider pl-1">Language</label>
                      <div className="relative group/select">
                        <select 
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          className="w-full bg-[#15151a]/80 border border-white/10 rounded-2xl py-3.5 px-4 text-sm text-slate-200 focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 outline-none appearance-none transition-all hover:bg-[#1a1a20] cursor-pointer backdrop-blur-md"
                        >
                          {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
                        </select>
                        <Globe size={16} className="absolute right-4 top-4 text-slate-500 pointer-events-none group-hover/select:text-indigo-400 transition-colors" />
                      </div>
                    </div>
                </div>

                {/* Text Area */}
                <div className="flex-grow flex flex-col space-y-2.5 mb-8">
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider pl-1">Claim Data</label>
                  <div className="relative flex-grow group/textarea">
                    <textarea 
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      placeholder="Paste text, URL, or social media snippet to verify..."
                      className="w-full h-full min-h-[240px] bg-[#15151a]/80 border border-white/10 rounded-2xl p-5 text-slate-200 placeholder:text-slate-600 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 resize-none transition-all text-sm leading-relaxed custom-scrollbar font-mono group-hover/textarea:bg-[#1a1a20] backdrop-blur-md"
                    />
                    <div className="absolute bottom-4 right-4 pointer-events-none">
                      <FileText size={16} className="text-slate-600 group-focus-within/textarea:text-indigo-500/50 transition-colors" />
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <button 
                  onClick={onSubmit}
                  disabled={isLoading || !inputText.trim()}
                  className={`w-full py-4.5 rounded-2xl font-bold text-sm tracking-wide uppercase shadow-lg transition-all duration-300 flex justify-center items-center gap-3 group/btn relative overflow-hidden ${
                    isLoading 
                      ? 'bg-slate-800/50 text-slate-500 cursor-not-allowed border border-white/5' 
                      : 'bg-indigo-600 text-white shadow-indigo-500/20 hover:shadow-indigo-500/40 hover:bg-indigo-500 border border-indigo-500/50 hover:scale-[1.02]'
                  }`}
                >
                  {isLoading ? (
                    <><RefreshCw className="animate-spin" size={18} /> Verifying...</>
                  ) : (
                    <>
                      <span className="relative z-10">Run Analysis</span>
                      <Zap size={18} className="fill-current relative z-10 group-hover/btn:scale-110 transition-transform"/>
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-700 ease-in-out"></div>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Suggestions */}
            <div className="px-2">
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-4 block">Quick Scenarios</label>
              <div className="flex flex-wrap gap-3">
                  {suggestions.map((s, idx) => (
                    <button 
                      key={idx}
                      onClick={() => setInputText(s.text)}
                      className="text-xs bg-white/[0.03] hover:bg-white/[0.08] text-slate-400 hover:text-indigo-300 border border-white/5 hover:border-indigo-500/30 px-5 py-2.5 rounded-xl transition-all backdrop-blur-md shadow-sm"
                    >
                      {s.label}
                    </button>
                  ))}
              </div>
            </div>
          </div>

          {/* RIGHT PANEL: OUTPUT */}
          <div className="lg:col-span-7 flex flex-col h-full">
            <div className="bg-white/[0.02] backdrop-blur-2xl border border-white/[0.08] rounded-[2.5rem] p-1.5 shadow-2xl h-full flex flex-col relative ring-1 ring-white/5 transition-all hover:ring-white/10">
              <div className="bg-[#0a0a0f]/60 rounded-[2rem] p-0 h-full flex flex-col relative overflow-hidden backdrop-blur-xl">
                
                {/* Header */}
                <div className="flex items-center justify-between p-8 border-b border-white/5 bg-white/[0.02]">
                  <div className="flex items-center gap-3">
                      <div className="p-2 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                        <Activity size={18} className="text-emerald-400" />
                      </div>
                      <h2 className="text-base font-semibold text-white tracking-wide">Verification Output</h2>
                  </div>
                   {result && (
                     <button onClick={onClear} className="text-xs text-slate-500 hover:text-rose-400 flex items-center gap-2 transition-colors px-4 py-2 rounded-xl hover:bg-white/5 border border-transparent hover:border-white/5 font-medium">
                       <Trash2 size={14} /> Clear Results
                     </button>
                   )}
                </div>

                {/* Content */}
                <div className="flex-grow overflow-y-auto custom-scrollbar relative p-8">
                   {!result && !isLoading && (
                     <div className="absolute inset-0 flex flex-col items-center justify-center opacity-30 select-none">
                        <div className="relative">
                          <div className="absolute inset-0 bg-indigo-500 blur-3xl opacity-20"></div>
                          <ShieldCheck size={80} className="text-slate-500 relative z-10 stroke-[0.8]"/>
                        </div>
                        <p className="text-slate-500 text-sm mt-6 font-medium tracking-wide">System ready. Awaiting input.</p>
                     </div>
                   )}

                   {isLoading && (
                     <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0a0a0f]/60 z-20 backdrop-blur-sm">
                        <div className="relative w-20 h-20 mb-8">
                           <div className="absolute inset-0 border-t-2 border-indigo-500 rounded-full animate-spin"></div>
                           <div className="absolute inset-2 border-r-2 border-violet-500 rounded-full animate-spin animation-delay-500"></div>
                           <div className="absolute inset-4 border-b-2 border-emerald-500 rounded-full animate-spin animation-delay-1000"></div>
                        </div>
                        <p className="text-indigo-300 text-xs font-bold animate-pulse tracking-[0.2em] uppercase">Triangulating Data Points...</p>
                     </div>
                   )}

                   {result && !isLoading && (
                     <ResultDetails result={result} />
                   )}
                </div>
              </div>
            </div>
          </div>

       </div>
    </div>
  );
};

export default ConsoleLayout;
