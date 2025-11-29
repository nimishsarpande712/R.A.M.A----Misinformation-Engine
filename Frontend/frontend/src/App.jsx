<<<<<<< HEAD
import React, { useState, useEffect } from 'react';
import ColorBends from './components/ColorBends';
import Navbar from './components/Navbar';
import ConsoleLayout from './components/ConsoleLayout';
import HistoryView from './components/HistoryView';
import AdminDashboard from './components/AdminDashboard';

// --- DUMMY DATA (Moved from original App.jsx) ---
const KNOWLEDGE_BASE = {
  health: {
    keywords: ['vaccine', 'virus', 'doctor', 'hospital', 'medicine', 'side effects'],
    verdict: 'false',
    explanation: "This health claim contradicts established medical consensus and official Ministry of Health guidelines issued in 2024.",
    raw: "Step 1: Identifying medical entities...\nStep 2: Querying ICMR database...\nStep 3: Found Circular 404 which explicitly refutes the viral message.\nStep 4: Cross-referencing with WHO guidelines... Match confirmed (Negative).",
    sources: [
      { type: "gov", source: "Ministry of Health & Family Welfare", url: "https://mohfw.gov.in", snippet: "Advisory dated 12th Jan 2025: No such side effects have been reported in clinical trials.", confidence: 0.98 },
      { type: "factcheck", source: "AltNews", url: "https://altnews.in", snippet: "Viral WhatsApp forward debunked. Image was doctored.", confidence: 0.95 }
    ]
  },
  election: {
    keywords: ['vote', 'election', 'poll', 'candidate', 'party', 'evm', 'turnout'],
    verdict: 'true',
    explanation: "The claim accurately reflects the voter turnout statistics released by the Election Commission for Phase 1.",
    raw: "Step 1: Parsing election data entities...\nStep 2: Retrieving ECI Press Release #22...\nStep 3: Verifying numbers against regional district reports...\nStep 4: Consistency check passed.",
    sources: [
      { type: "gov", source: "Election Commission of India", url: "https://eci.gov.in", snippet: "Press Note: Phase 1 records 67.8% turnout across 102 constituencies.", confidence: 0.99 },
      { type: "news", source: "The Hindu", url: "https://thehindu.com", snippet: "Live updates confirm the polling percentages match official records.", confidence: 0.92 }
    ]
  },
  disaster: {
    keywords: ['flood', 'earthquake', 'warning', 'storm', 'rain', 'alert', 'cyclone'],
    verdict: 'unverified',
    explanation: "While there are reports of heavy rain, no official 'Red Alert' has been issued for this specific district by the IMD yet.",
    raw: "Step 1: Checking IMD real-time API...\nStep 2: analyzing satellite imagery (INSAT-3D)...\nStep 3: Found Orange alert, but not Red.\nStep 4: Conclusion: Evidence is partial/insufficient for specific claim.",
    sources: [
      { type: "gov", source: "IMD", url: "https://mausam.imd.gov.in", snippet: "Forecast: Heavy to Very Heavy rainfall likely. No Red alert issued yet.", confidence: 0.70 },
      { type: "news", source: "Local News 18", url: "#", snippet: "Residents report waterlogging in low-lying areas.", confidence: 0.65 }
    ]
  },
  finance: {
    keywords: ['tax', 'gst', 'bank', 'money', 'scheme', 'rbi', 'upi'],
    verdict: 'misleading',
    explanation: "This claim takes a real policy change out of context. The tax hike applies only to luxury goods, not essential items.",
    raw: "Step 1: Analyzing GST Council minutes...\nStep 2: Comparing product categories...\nStep 3: Detected omission of context ('Luxury' qualifier missing).\nStep 4: Verdict: Technically true but misleading context.",
    sources: [
      { type: "gov", source: "CBIC / GST Council", url: "https://cbic.gov.in", snippet: "Notification 12/2025: 28% GST applicable only on casinos and online gaming.", confidence: 0.96 },
      { type: "news", source: "Mint", url: "https://livemint.com", snippet: "Clarification: Essential food items remain in the 5% bracket.", confidence: 0.90 }
    ]
  }
};

const INITIAL_HISTORY = [
  {
    id: 101,
    query_text: "New tax of 50% introduced on UPI transactions above 500 rupees.",
    verdict: "false",
    explanation: "NPCI has officially clarified that there are no charges for normal UPI transactions between bank accounts.",
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    sources_used: [{ type: "gov", source: "NPCI", snippet: "Press Release: UPI remains free for users.", confidence: 0.99 }]
  },
  {
    id: 102,
    query_text: "Cyclone Dana expected to hit Odisha coast by Friday evening.",
    verdict: "true",
    explanation: "IMD bulletins confirm the trajectory of the depression intensifying into a cyclone.",
    timestamp: new Date(Date.now() - 172800000).toISOString(),
    sources_used: [{ type: "gov", source: "IMD", snippet: "Bulletin 4: Landfall expected near Puri.", confidence: 0.95 }]
  },
  {
    id: 103,
    query_text: "Drinking hot water with lemon cures all stages of cancer.",
    verdict: "false",
    explanation: "This is a pseudoscientific claim with no medical evidence. It is a common recurring hoax.",
    timestamp: new Date(Date.now() - 250000000).toISOString(),
    sources_used: [{ type: "factcheck", source: "Snopes", snippet: "False claim circulating since 2011.", confidence: 0.98 }]
  }
];

// --- MOCK BACKEND SERVICE ---
const MockBackend = {
  checkClaim: async (text, category, language) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const lowerText = text.toLowerCase();
        let scenario = null;

        for (const key in KNOWLEDGE_BASE) {
          if (KNOWLEDGE_BASE[key].keywords.some(k => lowerText.includes(k))) {
            scenario = KNOWLEDGE_BASE[key];
            break;
          }
        }

        if (!scenario) {
          const rand = Math.random();
          const type = rand > 0.5 ? 'true' : 'unverified';
          scenario = {
            verdict: type,
            explanation: type === 'true' 
              ? "Multiple independent sources corroborate the core details of this statement." 
              : "We could not find sufficient public records to verify this specific claim at this time.",
            raw: "Step 1: General search initiated...\nStep 2: No direct semantic matches in indexed laws/circulars.\nStep 3: Checking news archives...\nStep 4: Result inconclusive based on available 2024-25 data.",
            sources: [
              { type: "news", source: "Google News Aggregate", url: "#", snippet: "Various reports mention similar events but differ on details.", confidence: 0.60 }
            ]
          };
        }

        resolve({
          mode: "reasoned",
          verdict: scenario.verdict,
          explanation: scenario.explanation,
          raw_answer: scenario.raw,
          sources_used: scenario.sources,
          timestamp: new Date().toISOString()
        });
      }, 1800);
    });
  }
};

const App = () => {
  const [view, setView] = useState('home'); 
  const [loading, setLoading] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);
  const [history, setHistory] = useState([]);
  
  // Console Inputs
  const [inputText, setInputText] = useState('');
  const [category, setCategory] = useState('Other');
  const [language, setLanguage] = useState('en');

  // Init History from LocalStorage or Constants
  useEffect(() => {
    const saved = localStorage.getItem('rama_history');
    if (saved && JSON.parse(saved).length > 0) {
      setHistory(JSON.parse(saved));
    } else {
      setHistory(INITIAL_HISTORY);
      localStorage.setItem('rama_history', JSON.stringify(INITIAL_HISTORY));
    }
  }, []);

  const handleClaimSubmit = async () => {
    if(!inputText.trim()) return;
    setLoading(true);
    setCurrentResult(null); 
    try {
      const result = await MockBackend.checkClaim(inputText, category, language);
      const resultWithId = { ...result, id: Date.now(), query_text: inputText };
      setCurrentResult(resultWithId);

      // Update History
      const newHistory = [resultWithId, ...history].slice(0, 50);
      setHistory(newHistory);
      localStorage.setItem('rama_history', JSON.stringify(newHistory));

    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const clearConsole = () => {
    setCurrentResult(null);
    setInputText('');
  };

  const loadHistoryItem = (item) => {
    setCurrentResult(item);
    setInputText(item.query_text);
    setView('home');
  };

  return (
    <div className="min-h-screen bg-[#030712] font-sans flex flex-col text-slate-200 selection:bg-indigo-500/30 overflow-hidden">
      
      {/* Custom "ColorBends" Background Component */}
      <div className="fixed inset-0 z-0 pointer-events-none after:absolute after:inset-0 after:bg-[#030712] after:opacity-10">
        <ColorBends
          colors={["#FF1493", "#00FF00", "#00BFFF", "#FFD700", "#FF4500"]}
          rotation={30}
          speed={0.3}
          scale={1.2}
          frequency={1.4}
          warpStrength={1.2}
          mouseInfluence={0.8}
          parallax={0.6}
          noise={0.08}
          transparent
        />
      </div>

      <Navbar currentView={view} setView={setView} />
      
      <main className="flex-grow w-full mx-auto px-4 sm:px-6 lg:px-8 py-28 relative z-10 overflow-y-auto custom-scrollbar">
        {view === 'home' && (
          <ConsoleLayout 
            inputText={inputText}
            setInputText={setInputText}
            category={category}
            setCategory={setCategory}
            language={language}
            setLanguage={setLanguage}
            onSubmit={handleClaimSubmit}
            isLoading={loading}
            result={currentResult}
            onClear={clearConsole}
          />
        )}

        {view === 'admin' && <AdminDashboard />}

        {view === 'history' && (
           <HistoryView history={history} onLoadItem={loadHistoryItem} />
        )}
      </main>

      <footer className="fixed bottom-0 w-full py-4 bg-[#030712]/80 backdrop-blur-xl border-t border-white/5 z-50">
         <div className="max-w-7xl mx-auto px-4 flex justify-between items-center text-[10px] text-slate-500 font-medium tracking-wider uppercase">
            <span>Project R.A.M.A. v3.0 • Intelligence Unit</span>
            <span className="flex items-center gap-2">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
              </span>
              System Online
            </span>
         </div>
      </footer>
      
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
        
        body {
          font-family: 'Inter', sans-serif;
        }
        
        .font-mono {
          font-family: 'JetBrains Mono', monospace;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
        
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.6s ease-out forwards;
        }
        
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-up {
          animation: fade-in-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>
    </div>
  );
};

export default App;
=======
import { Link, NavLink, Route, Routes } from 'react-router-dom'
import ClaimCheckPage from './pages/ClaimCheckPage.jsx'
import AdminPage from './pages/AdminPage.jsx'
import './App.css'

function App() {
  return (
    <div className="app-root">
      <header className="app-header">
        <div className="brand">
          <span className="brand-pill">R.A.M.A</span>
          <span className="brand-sub">Real-time AI Misinfo Auditor</span>
        </div>
        <nav className="nav-links">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              'nav-link' + (isActive ? ' nav-link-active' : '')
            }
          >
            Claim Check
          </NavLink>
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              'nav-link' + (isActive ? ' nav-link-active' : '')
            }
          >
            Admin
          </NavLink>
          <a
            href="https://github.com/"
            target="_blank"
            rel="noreferrer"
            className="nav-link nav-link-ghost"
          >
            GitHub
          </a>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<ClaimCheckPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route
            path="*"
            element={
              <div className="empty-state">
                <h2>Page not found</h2>
                <p>
                  The page you are looking for does not exist. Go back to{' '}
                  <Link to="/">Claim Check</Link>.
                </p>
              </div>
            }
          />
        </Routes>
      </main>

      <footer className="app-footer">
        <span>Powered by R.A.M.A Engine</span>
        <span className="dot" />
        <span>Fact-checking vibes only ✦</span>
      </footer>
    </div>
  )
}

export default App
>>>>>>> f7b9d1374505795c6df0a83d5b4547f2b7c6b837
