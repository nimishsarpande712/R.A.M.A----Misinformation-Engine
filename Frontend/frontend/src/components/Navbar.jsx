import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Menu, 
  X,
  Activity,
  Clock,
  Cpu,
  Github
} from 'lucide-react';

const Navbar = ({ currentView, setView }) => {
  const [isOpen, setIsOpen] = useState(false);

  const NavItem = ({ view, label, icon: Icon }) => (
    <button 
      onClick={() => { setView(view); setIsOpen(false); }}
      className={`relative px-5 py-2.5 text-sm font-medium transition-all duration-300 rounded-2xl flex items-center gap-2 group overflow-hidden ${
        currentView === view 
          ? 'text-white' 
          : 'text-slate-400 hover:text-white'
      }`}
    >
      {/* Active State Background */}
      {currentView === view && (
        <div className="absolute inset-0 bg-white/10 rounded-2xl border border-white/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1)] backdrop-blur-md"></div>
      )}
      
      <Icon size={18} className={`relative z-10 transition-colors ${currentView === view ? "text-indigo-400 drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]" : "text-slate-500 group-hover:text-slate-300"}`} />
      <span className="relative z-10">{label}</span>
    </button>
  );

  return (
    <nav className="fixed top-0 w-full z-50 border-b border-white/[0.06] bg-[#030712]/60 backdrop-blur-xl supports-[backdrop-filter]:bg-[#030712]/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo Section */}
          <div className="flex items-center gap-4 cursor-pointer group" onClick={() => setView('home')}>
             <div className="relative w-10 h-10 flex items-center justify-center">
                <div className="absolute inset-0 bg-indigo-500/20 rounded-2xl blur-md group-hover:bg-indigo-500/30 transition-colors"></div>
                <div className="relative w-full h-full rounded-2xl bg-gradient-to-br from-[#1e1b4b] to-[#0f172a] border border-white/10 flex items-center justify-center shadow-lg">
                   <Cpu size={20} className="text-indigo-400" />
                </div>
             </div>
             <div className="flex flex-col">
                <span className="text-white text-lg font-bold tracking-tight leading-none">R.A.M.A.</span>
                <span className="text-[10px] text-indigo-400/80 font-medium tracking-wider uppercase leading-none mt-1.5">Intelligence Unit</span>
             </div>
          </div>
          
          {/* Center Nav */}
          <div className="hidden md:flex items-center p-1.5 bg-white/[0.03] rounded-3xl border border-white/[0.05] backdrop-blur-md shadow-xl">
            <NavItem view="home" label="Fact Check" icon={ShieldCheck} />
            <NavItem view="history" label="History" icon={Clock} />
            <NavItem view="admin" label="System Status" icon={Activity} />
          </div>

          {/* Right Section */}
          <div className="hidden md:flex items-center gap-4">
            <a href="#" className="group flex items-center gap-2 px-4 py-2 rounded-2xl hover:bg-white/5 transition-all border border-transparent hover:border-white/5 backdrop-blur-sm">
               <div className="p-1.5 bg-white/10 rounded-xl">
                 <Github size={16} className="text-slate-400 group-hover:text-white" />
               </div>
               <span className="text-xs font-medium text-slate-400 group-hover:text-white">Repository</span>
            </a>
          </div>

          {/* Mobile Menu Toggle */}
          <div className="md:hidden flex items-center">
            <button onClick={() => setIsOpen(!isOpen)} className="text-slate-300 hover:text-white p-2 bg-white/5 rounded-xl backdrop-blur-md border border-white/5">
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-[#030712]/90 backdrop-blur-xl border-b border-white/10 px-4 py-6 space-y-3 absolute w-full z-50">
          <button onClick={() => { setView('home'); setIsOpen(false); }} className="block w-full text-left text-white font-medium text-sm py-4 px-6 rounded-2xl bg-white/10 border border-white/5">Fact Check</button>
          <button onClick={() => { setView('history'); setIsOpen(false); }} className="block w-full text-left text-slate-300 font-medium text-sm py-4 px-6 rounded-2xl hover:bg-white/5 border border-transparent hover:border-white/5">History</button>
          <button onClick={() => { setView('admin'); setIsOpen(false); }} className="block w-full text-left text-slate-300 font-medium text-sm py-4 px-6 rounded-2xl hover:bg-white/5 border border-transparent hover:border-white/5">System Status</button>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
