import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { 
  ShieldCheck, 
  XCircle, 
  RefreshCw, 
  Menu, 
  X,
  ChevronDown,
  ChevronUp,
  FileText,
  Database, 
  Activity,
  Trash2,
  Zap,
  Clock,
  CheckCircle,
  AlertTriangle,
  AlertOctagon,
  Cpu,
  Globe,
  Share2,
  Settings,
  Github,
  Search
} from 'lucide-react';

/**
 * PROJECT R.A.M.A. - Cinematic Glass Theme
 * * Theme Upgrades:
 * - Custom "ColorBends" Fluid Background (Three.js)
 * - Premium Glassmorphism
 * - Luminous UI accents
 */

// --- THREE.JS SHADERS & COMPONENTS ---

const MAX_COLORS = 8;

const frag = `
#define MAX_COLORS ${MAX_COLORS}
uniform vec2 uCanvas;
uniform float uTime;
uniform float uSpeed;
uniform vec2 uRot;
uniform int uColorCount;
uniform vec3 uColors[MAX_COLORS];
uniform int uTransparent;
uniform float uScale;
uniform float uFrequency;
uniform float uWarpStrength;
uniform vec2 uPointer; // in NDC [-1,1]
uniform float uMouseInfluence;
uniform float uParallax;
uniform float uNoise;
varying vec2 vUv;

void main() {
  float t = uTime * uSpeed;
  vec2 p = vUv * 2.0 - 1.0;
  p += uPointer * uParallax * 0.1;
  vec2 rp = vec2(p.x * uRot.x - p.y * uRot.y, p.x * uRot.y + p.y * uRot.x);
  vec2 q = vec2(rp.x * (uCanvas.x / uCanvas.y), rp.y);
  q /= max(uScale, 0.0001);
  q /= 0.5 + 0.2 * dot(q, q);
  q += 0.2 * cos(t) - 7.56;
  vec2 toward = (uPointer - rp);
  q += toward * uMouseInfluence * 0.2;

    vec3 col = vec3(0.0);
    float a = 1.0;

    if (uColorCount > 0) {
      vec2 s = q;
      vec3 sumCol = vec3(0.0);
      float cover = 0.0;
      for (int i = 0; i < MAX_COLORS; ++i) {
            if (i >= uColorCount) break;
            s -= 0.01;
            vec2 r = sin(1.5 * (s.yx * uFrequency) + 2.0 * cos(s * uFrequency));
            float m0 = length(r + sin(5.0 * r.y * uFrequency - 3.0 * t + float(i)) / 4.0);
            float kBelow = clamp(uWarpStrength, 0.0, 1.0);
            float kMix = pow(kBelow, 0.3); // strong response across 0..1
            float gain = 1.0 + max(uWarpStrength - 1.0, 0.0); // allow >1 to amplify displacement
            vec2 disp = (r - s) * kBelow;
            vec2 warped = s + disp * gain;
            float m1 = length(warped + sin(5.0 * warped.y * uFrequency - 3.0 * t + float(i)) / 4.0);
            float m = mix(m0, m1, kMix);
            float w = 1.0 - exp(-6.0 / exp(6.0 * m));
            sumCol += uColors[i] * w;
            cover = max(cover, w);
      }
      col = clamp(sumCol, 0.0, 1.0);
      a = uTransparent > 0 ? cover : 1.0;
    } else {
        vec2 s = q;
        for (int k = 0; k < 3; ++k) {
            s -= 0.01;
            vec2 r = sin(1.5 * (s.yx * uFrequency) + 2.0 * cos(s * uFrequency));
            float m0 = length(r + sin(5.0 * r.y * uFrequency - 3.0 * t + float(k)) / 4.0);
            float kBelow = clamp(uWarpStrength, 0.0, 1.0);
            float kMix = pow(kBelow, 0.3);
            float gain = 1.0 + max(uWarpStrength - 1.0, 0.0);
            vec2 disp = (r - s) * kBelow;
            vec2 warped = s + disp * gain;
            float m1 = length(warped + sin(5.0 * warped.y * uFrequency - 3.0 * t + float(k)) / 4.0);
            float m = mix(m0, m1, kMix);
            col[k] = 1.0 - exp(-6.0 / exp(6.0 * m));
        }
        a = uTransparent > 0 ? max(max(col.r, col.g), col.b) : 1.0;
    }

    if (uNoise > 0.0001) {
      float n = fract(sin(dot(gl_FragCoord.xy + vec2(uTime), vec2(12.9898, 78.233))) * 43758.5453123);
      col += (n - 0.5) * uNoise;
      col = clamp(col, 0.0, 1.0);
    }

    vec3 rgb = (uTransparent > 0) ? col * a : col;
    gl_FragColor = vec4(rgb, a);
}
`;

const vert = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 1.0);
}
`;

const ColorBends = ({
  className,
  style,
  rotation = 90,
  speed = 0.8,
  colors = [],
  transparent = true,
  autoRotate = 1,
  scale = 0.5,
  frequency = 0.5,
  warpStrength = 4,
  mouseInfluence = 1,
  parallax = 0.5,
  noise = 0
}) => {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const rafRef = useRef(null);
  const materialRef = useRef(null);
  const resizeObserverRef = useRef(null);
  const rotationRef = useRef(rotation);
  const autoRotateRef = useRef(autoRotate);
  const pointerTargetRef = useRef(new THREE.Vector2(0, 0));
  const pointerCurrentRef = useRef(new THREE.Vector2(0, 0));
  const pointerSmoothRef = useRef(8);

  useEffect(() => {
    const container = containerRef.current;
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const geometry = new THREE.PlaneGeometry(2, 2);
    const uColorsArray = Array.from({ length: MAX_COLORS }, () => new THREE.Vector3(0, 0, 0));
    const material = new THREE.ShaderMaterial({
      vertexShader: vert,
      fragmentShader: frag,
      uniforms: {
        uCanvas: { value: new THREE.Vector2(1, 1) },
        uTime: { value: 0 },
        uSpeed: { value: speed },
        uRot: { value: new THREE.Vector2(1, 0) },
        uColorCount: { value: 0 },
        uColors: { value: uColorsArray },
        uTransparent: { value: transparent ? 1 : 0 },
        uScale: { value: scale },
        uFrequency: { value: frequency },
        uWarpStrength: { value: warpStrength },
        uPointer: { value: new THREE.Vector2(0, 0) },
        uMouseInfluence: { value: mouseInfluence },
        uParallax: { value: parallax },
        uNoise: { value: noise }
      },
      premultipliedAlpha: true,
      transparent: true
    });
    materialRef.current = material;

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    const renderer = new THREE.WebGLRenderer({
      antialias: false,
      powerPreference: 'high-performance',
      alpha: true
    });
    rendererRef.current = renderer;
    // Three r152+ uses outputColorSpace and SRGBColorSpace
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, transparent ? 0 : 1);
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    renderer.domElement.style.display = 'block';
    container.appendChild(renderer.domElement);

    const clock = new THREE.Clock();

    const handleResize = () => {
      const w = container.clientWidth || 1;
      const h = container.clientHeight || 1;
      renderer.setSize(w, h, false);
      material.uniforms.uCanvas.value.set(w, h);
    };

    handleResize();

    if ('ResizeObserver' in window) {
      const ro = new ResizeObserver(handleResize);
      ro.observe(container);
      resizeObserverRef.current = ro;
    } else {
      window.addEventListener('resize', handleResize);
    }

    const loop = () => {
      const dt = clock.getDelta();
      const elapsed = clock.elapsedTime;
      material.uniforms.uTime.value = elapsed;

      const deg = (rotationRef.current % 360) + autoRotateRef.current * elapsed;
      const rad = (deg * Math.PI) / 180;
      const c = Math.cos(rad);
      const s = Math.sin(rad);
      material.uniforms.uRot.value.set(c, s);

      const cur = pointerCurrentRef.current;
      const tgt = pointerTargetRef.current;
      const amt = Math.min(1, dt * pointerSmoothRef.current);
      cur.lerp(tgt, amt);
      material.uniforms.uPointer.value.copy(cur);
      renderer.render(scene, camera);
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      if (resizeObserverRef.current) resizeObserverRef.current.disconnect();
      else window.removeEventListener('resize', handleResize);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      if (renderer.domElement && renderer.domElement.parentElement === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [frequency, mouseInfluence, noise, parallax, scale, speed, transparent, warpStrength]);

  useEffect(() => {
    const material = materialRef.current;
    const renderer = rendererRef.current;
    if (!material) return;

    rotationRef.current = rotation;
    autoRotateRef.current = autoRotate;
    material.uniforms.uSpeed.value = speed;
    material.uniforms.uScale.value = scale;
    material.uniforms.uFrequency.value = frequency;
    material.uniforms.uWarpStrength.value = warpStrength;
    material.uniforms.uMouseInfluence.value = mouseInfluence;
    material.uniforms.uParallax.value = parallax;
    material.uniforms.uNoise.value = noise;

    const toVec3 = hex => {
      const h = hex.replace('#', '').trim();
      const v =
        h.length === 3
          ? [parseInt(h[0] + h[0], 16), parseInt(h[1] + h[1], 16), parseInt(h[2] + h[2], 16)]
          : [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
      return new THREE.Vector3(v[0] / 255, v[1] / 255, v[2] / 255);
    };

    const arr = (colors || []).filter(Boolean).slice(0, MAX_COLORS).map(toVec3);
    for (let i = 0; i < MAX_COLORS; i++) {
      const vec = material.uniforms.uColors.value[i];
      if (i < arr.length) vec.copy(arr[i]);
      else vec.set(0, 0, 0);
    }
    material.uniforms.uColorCount.value = arr.length;

    material.uniforms.uTransparent.value = transparent ? 1 : 0;
    if (renderer) renderer.setClearColor(0x000000, transparent ? 0 : 1);
  }, [
    rotation,
    autoRotate,
    speed,
    scale,
    frequency,
    warpStrength,
    mouseInfluence,
    parallax,
    noise,
    colors,
    transparent
  ]);

  useEffect(() => {
    const material = materialRef.current;
    const container = containerRef.current;
    if (!material || !container) return;

    const handlePointerMove = e => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / (rect.width || 1)) * 2 - 1;
      const y = -(((e.clientY - rect.top) / (rect.height || 1)) * 2 - 1);
      pointerTargetRef.current.set(x, y);
    };

    container.addEventListener('pointermove', handlePointerMove);
    return () => {
      container.removeEventListener('pointermove', handlePointerMove);
    };
  }, []);

  return <div ref={containerRef} className={`w-full h-full relative overflow-hidden ${className}`} style={style} />;
}


// --- DUMMY DATA (Unchanged Logic) ---
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
  },

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

// --- THEME CONSTANTS ---
const COLORS = {
  true: { 
    bg: 'bg-emerald-500/10', 
    text: 'text-emerald-200', 
    border: 'border-emerald-500/20', 
    icon: CheckCircle, 
    badge: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-[0_0_15px_-3px_rgba(16,185,129,0.3)]' 
  },
  false: { 
    bg: 'bg-rose-500/10', 
    text: 'text-rose-200', 
    border: 'border-rose-500/20', 
    icon: XCircle, 
    badge: 'bg-rose-500/20 text-rose-300 border border-rose-500/30 shadow-[0_0_15px_-3px_rgba(244,63,94,0.3)]' 
  },
  misleading: { 
    bg: 'bg-amber-500/10', 
    text: 'text-amber-200', 
    border: 'border-amber-500/20', 
    icon: AlertOctagon, 
    badge: 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-[0_0_15px_-3px_rgba(245,158,11,0.3)]' 
  },
  unverified: { 
    bg: 'bg-slate-500/10', 
    text: 'text-slate-300', 
    border: 'border-slate-500/20', 
    icon: AlertTriangle, 
    badge: 'bg-slate-500/20 text-slate-300 border border-slate-500/30' 
  }
};

const CATEGORIES = ["Health", "Election", "Disaster", "Communal", "Finance", "Other"];
const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi' },
  { code: 'mr', label: 'Marathi' },
  { code: 'te', label: 'Telugu' }
];

// --- APP COMPONENTS ---

const Navbar = ({ currentView, setView }) => {
  const [isOpen, setIsOpen] = useState(false);

  const NavItem = ({ view, label, icon: Icon }) => (
    <button 
      onClick={() => { setView(view); setIsOpen(false); }}
      className={`relative px-4 py-2 text-sm font-medium transition-all duration-300 rounded-lg flex items-center gap-2 group overflow-hidden ${
        currentView === view 
          ? 'text-white' 
          : 'text-slate-400 hover:text-white'
      }`}
    >
      {/* Active State Background */}
      {currentView === view && (
        <div className="absolute inset-0 bg-white/5 rounded-lg border border-white/5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1)]"></div>
      )}
      
      <Icon size={16} className={`relative z-10 transition-colors ${currentView === view ? "text-indigo-400 drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]" : "text-slate-500 group-hover:text-slate-300"}`} />
      <span className="relative z-10">{label}</span>
    </button>
  );

  return (
    <nav className="fixed top-0 w-full z-50 border-b border-white/[0.06] bg-[#030712]/70 backdrop-blur-xl supports-[backdrop-filter]:bg-[#030712]/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo Section */}
          <div className="flex items-center gap-3 cursor-pointer group" onClick={() => setView('home')}>
             <div className="relative w-9 h-9 flex items-center justify-center">
                <div className="absolute inset-0 bg-indigo-500/20 rounded-xl blur-md group-hover:bg-indigo-500/30 transition-colors"></div>
                <div className="relative w-full h-full rounded-xl bg-gradient-to-br from-[#1e1b4b] to-[#0f172a] border border-white/10 flex items-center justify-center">
                   <Cpu size={18} className="text-indigo-400" />
                </div>
             </div>
             <div className="flex flex-col">
                <span className="text-white text-base font-bold tracking-tight leading-none">R.A.M.A.</span>
                <span className="text-[10px] text-indigo-400/80 font-medium tracking-wider uppercase leading-none mt-1">Intelligence Unit</span>
             </div>
          </div>
          
          {/* Center Nav */}
          <div className="hidden md:flex items-center p-1 bg-white/[0.03] rounded-xl border border-white/[0.05] backdrop-blur-md">
            <NavItem view="home" label="Fact Check" icon={ShieldCheck} />
            <NavItem view="history" label="History" icon={Clock} />
            <NavItem view="admin" label="System Status" icon={Activity} />
          </div>

          {/* Right Section */}
          <div className="hidden md:flex items-center gap-4">
            <a href="#" className="group flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 transition-all border border-transparent hover:border-white/5">
               <div className="p-1 bg-white/10 rounded-md">
                 <Github size={14} className="text-slate-400 group-hover:text-white" />
               </div>
               <span className="text-xs font-medium text-slate-400 group-hover:text-white">Repository</span>
            </a>
          </div>

          {/* Mobile Menu Toggle */}
          <div className="md:hidden flex items-center">
            <button onClick={() => setIsOpen(!isOpen)} className="text-slate-300 hover:text-white p-2">
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-[#030712] border-b border-white/10 px-4 py-4 space-y-2">
          <button onClick={() => { setView('home'); setIsOpen(false); }} className="block w-full text-left text-white font-medium text-sm py-3 px-4 rounded-lg bg-white/5">Fact Check</button>
          <button onClick={() => { setView('history'); setIsOpen(false); }} className="block w-full text-left text-slate-300 font-medium text-sm py-3 px-4 rounded-lg hover:bg-white/5">History</button>
          <button onClick={() => { setView('admin'); setIsOpen(false); }} className="block w-full text-left text-slate-300 font-medium text-sm py-3 px-4 rounded-lg hover:bg-white/5">System Status</button>
        </div>
      )}
    </nav>
  );
};

const ConsoleLayout = ({ 
  inputText, setInputText, category, setCategory, language, setLanguage, 
  onSubmit, isLoading, result, onClear
}) => {
  const suggestions = [
    { label: "Health", text: "New vaccine causes severe side effects according to 2024 leaked report." },
    { label: "Elections", text: "Phase 1 election voter turnout was only 40% in most districts." },
    { label: "Alerts", text: "Red alert issued for Mumbai coast due to approaching cyclone." },
  ];

  return (
    <div className="w-full max-w-7xl mx-auto pt-6 animate-fade-in relative z-10">
       <div className="mb-10 text-center lg:text-left">
         <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-indigo-100 to-indigo-200/50 mb-3 tracking-tight drop-shadow-sm">
           Fact-Checking Cockpit
         </h1>
         <p className="text-slate-400 text-sm max-w-2xl">
           Advanced misinformation detection engine powered by multi-source verification.
         </p>
       </div>

       <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 min-h-[600px]">
          
          {/* LEFT PANEL: INPUT */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <div className="bg-white/[0.02] backdrop-blur-2xl border border-white/[0.08] rounded-3xl p-1 shadow-2xl relative group ring-1 ring-white/5">
              
              {/* Inner Card */}
              <div className="bg-[#0a0a0f]/80 rounded-[20px] p-6 h-full flex flex-col relative overflow-hidden">
                
                {/* Header */}
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-indigo-500/10 rounded-lg">
                      <Search size={16} className="text-indigo-400" />
                    </div>
                    <h2 className="text-sm font-semibold text-white tracking-wide">Analysis Parameters</h2>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 px-2 py-1 bg-white/5 rounded border border-white/5">READY</span>
                </div>
                
                {/* Selectors */}
                <div className="grid grid-cols-2 gap-4 mb-5">
                    <div className="space-y-2">
                      <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider pl-1">Category</label>
                      <div className="relative group/select">
                        <select 
                          value={category}
                          onChange={(e) => setCategory(e.target.value)}
                          className="w-full bg-[#15151a] border border-white/10 rounded-xl py-3 px-3 text-sm text-slate-200 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 outline-none transition-all hover:bg-[#1a1a20] appearance-none cursor-pointer"
                        >
                          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                        <ChevronDown size={14} className="absolute right-3 top-3.5 text-slate-500 pointer-events-none group-hover/select:text-indigo-400 transition-colors" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider pl-1">Language</label>
                      <div className="relative group/select">
                        <select 
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          className="w-full bg-[#15151a] border border-white/10 rounded-xl py-3 px-3 text-sm text-slate-200 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 outline-none appearance-none transition-all hover:bg-[#1a1a20] cursor-pointer"
                        >
                          {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
                        </select>
                        <Globe size={14} className="absolute right-3 top-3.5 text-slate-500 pointer-events-none group-hover/select:text-indigo-400 transition-colors" />
                      </div>
                    </div>
                </div>

                {/* Text Area */}
                <div className="flex-grow flex flex-col space-y-2 mb-6">
                  <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider pl-1">Claim Data</label>
                  <div className="relative flex-grow group/textarea">
                    <textarea 
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      placeholder="Paste text to verify..."
                      className="w-full h-full min-h-[220px] bg-[#15151a] border border-white/10 rounded-xl p-4 text-slate-200 placeholder:text-slate-600 focus:ring-1 focus:ring-indigo-500/50 focus:border-indigo-500/50 resize-none transition-all text-sm leading-relaxed custom-scrollbar font-mono group-hover/textarea:bg-[#1a1a20]"
                    />
                    <div className="absolute bottom-3 right-3 pointer-events-none">
                      <FileText size={14} className="text-slate-600 group-focus-within/textarea:text-indigo-500/50 transition-colors" />
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <button 
                  onClick={onSubmit}
                  disabled={isLoading || !inputText.trim()}
                  className={`w-full py-4 rounded-xl font-bold text-sm tracking-wide uppercase shadow-lg transition-all duration-300 flex justify-center items-center gap-2 group/btn relative overflow-hidden ${
                    isLoading 
                      ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-white/5' 
                      : 'bg-indigo-600 text-white shadow-indigo-500/20 hover:shadow-indigo-500/40 hover:bg-indigo-500 border border-indigo-500/50'
                  }`}
                >
                  {isLoading ? (
                    <><RefreshCw className="animate-spin" size={16} /> Verifying...</>
                  ) : (
                    <>
                      <span className="relative z-10">Run Analysis</span>
                      <Zap size={16} className="fill-current relative z-10 group-hover/btn:scale-110 transition-transform"/>
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-700 ease-in-out"></div>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Suggestions */}
            <div className="px-2">
              <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-3 block">Quick Scenarios</label>
              <div className="flex flex-wrap gap-2">
                  {suggestions.map((s, idx) => (
                    <button 
                      key={idx}
                      onClick={() => setInputText(s.text)}
                      className="text-xs bg-white/[0.03] hover:bg-white/[0.08] text-slate-400 hover:text-indigo-300 border border-white/5 hover:border-indigo-500/30 px-4 py-2 rounded-lg transition-all backdrop-blur-md"
                    >
                      {s.label}
                    </button>
                  ))}
              </div>
            </div>
          </div>

          {/* RIGHT PANEL: OUTPUT */}
          <div className="lg:col-span-7 flex flex-col h-full">
            <div className="bg-white/[0.02] backdrop-blur-2xl border border-white/[0.08] rounded-3xl p-1 shadow-2xl h-full flex flex-col relative ring-1 ring-white/5">
              <div className="bg-[#0a0a0f]/80 rounded-[20px] p-0 h-full flex flex-col relative overflow-hidden">
                
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/5 bg-white/[0.02]">
                  <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-emerald-500/10 rounded-lg">
                        <Activity size={16} className="text-emerald-400" />
                      </div>
                      <h2 className="text-sm font-semibold text-white tracking-wide">Verification Output</h2>
                  </div>
                   {result && (
                     <button onClick={onClear} className="text-xs text-slate-500 hover:text-rose-400 flex items-center gap-1.5 transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5 border border-transparent hover:border-white/5">
                       <Trash2 size={12} /> Clear
                     </button>
                   )}
                </div>

                {/* Content */}
                <div className="flex-grow overflow-y-auto custom-scrollbar relative p-6">
                   {!result && !isLoading && (
                     <div className="absolute inset-0 flex flex-col items-center justify-center opacity-30 select-none">
                        <div className="relative">
                          <div className="absolute inset-0 bg-indigo-500 blur-3xl opacity-20"></div>
                          <ShieldCheck size={64} className="text-slate-500 relative z-10 stroke-[1]"/>
                        </div>
                        <p className="text-slate-500 text-sm mt-4 font-medium tracking-wide">System ready. Awaiting input.</p>
                     </div>
                   )}

                   {isLoading && (
                     <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0a0a0f]/60 z-20 backdrop-blur-sm">
                        <div className="relative w-16 h-16 mb-6">
                           <div className="absolute inset-0 border-t-2 border-indigo-500 rounded-full animate-spin"></div>
                           <div className="absolute inset-2 border-r-2 border-violet-500 rounded-full animate-spin animation-delay-500"></div>
                           <div className="absolute inset-4 border-b-2 border-emerald-500 rounded-full animate-spin animation-delay-1000"></div>
                        </div>
                        <p className="text-indigo-300 text-sm font-medium animate-pulse tracking-widest uppercase text-[10px]">Triangulating Data Points...</p>
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

const ResultDetails = ({ result }) => {
  const theme = COLORS[result.verdict] || COLORS.unverified;
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="animate-fade-in-up space-y-6">
       {/* Verdict Section */}
       <div className={`p-6 rounded-2xl border ${theme.border} ${theme.bg} relative overflow-hidden`}>
          {/* Ambient Glow */}
          <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-white/10 to-transparent blur-2xl opacity-50`}></div>
          
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className={`inline-flex items-center px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${theme.badge} backdrop-blur-md`}>
                <theme.icon size={14} className="mr-2" />
                {result.verdict}
              </div>
              <span className="text-[10px] font-mono text-slate-400">{new Date(result.timestamp).toLocaleTimeString()}</span>
            </div>
            
            <p className="text-slate-100 text-lg leading-relaxed font-medium">
               {result.explanation}
            </p>
          </div>
       </div>

       {/* Sources Section */}
       <div>
         <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-3 block flex items-center gap-2">
            <Database size={12} /> Sources Found
         </label>
         <div className="grid gap-3">
           {result.sources_used.map((source, idx) => (
             <a key={idx} href={source.url} target="_blank" rel="noreferrer" className="flex flex-col sm:flex-row sm:items-center justify-between bg-white/[0.02] border border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.04] p-4 rounded-xl transition-all group relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-indigo-500/0 group-hover:bg-indigo-500/50 transition-colors"></div>
                <div className="flex-1 min-w-0 mr-4">
                   <h4 className="text-sm text-indigo-200 font-medium truncate">{source.source}</h4>
                   <p className="text-xs text-slate-500 truncate mt-1 group-hover:text-slate-400">{source.snippet}</p>
                </div>
                <div className="mt-2 sm:mt-0 self-start sm:self-center shrink-0">
                    <span className={`text-[10px] font-mono px-2 py-1 rounded border ${source.confidence > 0.8 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>
                        {(source.confidence * 100).toFixed(1)}% MATCH
                    </span>
                </div>
             </a>
           ))}
         </div>
       </div>

       {/* Reasoning Trace */}
       <div className="pt-2">
          <button 
            onClick={() => setExpanded(!expanded)} 
            className="w-full flex justify-between items-center px-5 py-3 bg-white/[0.02] border border-white/5 rounded-xl text-xs font-medium text-slate-400 hover:text-indigo-300 hover:border-white/10 transition-all group"
          >
             <span className="flex items-center gap-2">
               <Cpu size={14} className="group-hover:text-indigo-400 transition-colors" />
               View Neural Reasoning Trace
             </span>
             {expanded ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
          </button>
          
          {expanded && (
            <div className="mt-2 p-5 bg-[#050508] rounded-xl border border-white/10 text-xs font-mono text-indigo-300/80 whitespace-pre-wrap leading-relaxed shadow-inner">
               <div className="flex items-center gap-2 mb-2 text-slate-600 border-b border-white/5 pb-2">
                  <span className="w-2 h-2 rounded-full bg-slate-700"></span>
                  <span className="w-2 h-2 rounded-full bg-slate-700"></span>
                  <span className="w-2 h-2 rounded-full bg-slate-700"></span>
               </div>
               {result.raw_answer}
            </div>
          )}
       </div>
    </div>
  );
};

const HistoryView = ({ history, onLoadItem }) => {
  return (
    <div className="max-w-5xl mx-auto pt-8 animate-fade-in text-slate-300 relative z-10 px-4 pb-12">
      <div className="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">Archive</h2>
          <p className="text-slate-500 text-sm">Previous verifications and outcomes.</p>
        </div>
        <div className="text-right">
           <span className="bg-white/5 border border-white/10 px-4 py-2 rounded-lg text-xs font-mono text-indigo-300">{history.length} ENTRIES</span>
        </div>
      </div>
      
      {history.length === 0 ? (
        <div className="text-center py-20 bg-white/[0.02] rounded-2xl border border-white/5 border-dashed">
          <Clock size={48} className="mx-auto text-slate-700 mb-4 opacity-50"/>
          <h3 className="text-lg font-medium text-slate-400">Archive Empty</h3>
        </div>
      ) : (
        <div className="grid gap-4">
          {history.map((item, idx) => (
            <div 
              key={idx} 
              onClick={() => onLoadItem(item)}
              className="bg-white/[0.02] p-6 rounded-2xl border border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.04] transition-all cursor-pointer group flex items-start gap-5 relative overflow-hidden"
            >
              {/* Hover Highlight */}
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/0 via-indigo-500/5 to-indigo-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

              <div className={`mt-1 shrink-0 w-10 h-10 rounded-full flex items-center justify-center border shadow-lg ${item.verdict === 'true' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 shadow-emerald-500/10' : item.verdict === 'false' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400 shadow-rose-500/10' : 'bg-slate-700/20 border-slate-600/30 text-slate-500'}`}>
                {item.verdict === 'true' ? <CheckCircle size={18}/> : item.verdict === 'false' ? <XCircle size={18}/> : <AlertTriangle size={18}/>}
              </div>

              <div className="flex-grow min-w-0 relative z-10">
                 <div className="flex justify-between items-center mb-1.5">
                    <span className={`text-xs font-bold uppercase tracking-widest ${item.verdict === 'true' ? 'text-emerald-400' : item.verdict === 'false' ? 'text-rose-400' : 'text-slate-400'}`}>
                      {item.verdict}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">{new Date(item.timestamp).toLocaleDateString()}</span>
                 </div>
                 <h4 className="text-slate-200 font-medium truncate group-hover:text-white transition-colors text-base">
                   {item.query_text}
                 </h4>
              </div>
              
              <div className="self-center shrink-0 text-slate-700 group-hover:text-indigo-400 transition-colors relative z-10">
                 <ChevronDown className="transform -rotate-90" size={20} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
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
    <div className="max-w-6xl mx-auto pt-8 animate-fade-in text-slate-300 relative z-10 px-4 pb-12">
      <div className="mb-10 border-b border-white/5 pb-6 flex justify-between items-center">
        <div>
           <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">System Status</h2>
           <p className="text-sm text-slate-500">Overview of verification nodes and knowledge base.</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/10 px-4 py-1.5 rounded-full border border-emerald-500/20 backdrop-blur-sm">
           <div className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </div>
           <span className="text-emerald-400 text-xs font-bold uppercase tracking-wide">Operational</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Sync Control */}
        <div className="bg-white/[0.02] border border-white/10 p-6 rounded-3xl backdrop-blur-xl">
           <div className="flex items-center justify-between mb-8">
             <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Data Ingestion</h3>
             <Activity size={16} className="text-indigo-400" />
           </div>
           
           <button 
             onClick={handleSync}
             disabled={loading}
             className="w-full py-3 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-xl text-sm font-medium transition-all flex justify-center items-center gap-2 shadow-sm group"
           >
             {loading ? <RefreshCw className="animate-spin" size={16}/> : <RefreshCw size={16} className="group-hover:rotate-180 transition-transform duration-500"/>}
             {loading ? 'Syncing...' : 'Sync Now'}
           </button>

           <div className="mt-8">
              <h4 className="text-[10px] text-slate-500 uppercase tracking-widest mb-3 font-semibold">Activity Log</h4>
              <div className="p-4 bg-black/40 rounded-xl border border-white/5 font-mono text-[10px] text-indigo-300/80 h-48 overflow-y-auto custom-scrollbar shadow-inner">
                  {logs.length === 0 && <div className="text-slate-600 italic">No recent activity.</div>}
                  {logs.map((l, i) => <div key={i} className="mb-2 border-b border-white/5 pb-2 last:border-0 last:pb-0">{l}</div>)}
              </div>
           </div>
        </div>

        {/* Metrics */}
        <div className="bg-white/[0.02] border border-white/10 p-6 rounded-3xl col-span-2 backdrop-blur-xl">
           <div className="flex items-center justify-between mb-8">
             <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Knowledge Base Metrics</h3>
             <Database size={16} className="text-indigo-400" />
           </div>

           <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              {stats && Object.entries(stats.ingested).map(([key, val]) => (
                <div key={key} className="bg-white/5 p-5 rounded-2xl border border-white/5 hover:border-indigo-500/20 transition-colors group">
                  <div className="text-3xl font-bold text-white group-hover:text-indigo-300 transition-colors">{val}</div>
                  <div className="text-[10px] uppercase text-slate-500 mt-2 font-bold tracking-wider">{key}</div>
                </div>
              ))}
           </div>
           
           <div className="mt-10 pt-8 border-t border-white/5">
             <h4 className="text-[10px] text-slate-500 uppercase font-semibold mb-4 tracking-widest">System Alerts</h4>
             <div className="space-y-3">
                <div className="flex justify-between text-sm items-center bg-emerald-500/5 p-4 rounded-xl border border-emerald-500/10 hover:bg-emerald-500/10 transition-colors">
                   <div className="flex items-center gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                      <span className="text-emerald-100/80">Indexed 45 new government circulars</span>
                   </div>
                   <span className="text-slate-500 text-[10px] font-mono">10m ago</span>
                </div>
                <div className="flex justify-between text-sm items-center bg-indigo-500/5 p-4 rounded-xl border border-indigo-500/10 hover:bg-indigo-500/10 transition-colors">
                   <div className="flex items-center gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-500"></div>
                      <span className="text-indigo-100/80">Sync completed for 'Elections' topic</span>
                   </div>
                   <span className="text-slate-500 text-[10px] font-mono">1h ago</span>
                </div>
             </div>
           </div>
        </div>
      </div>
    </div>
  );
};

// --- MAIN APP ---

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
      
      {/* Custom "ColorBends" Background Component
        Using 'fixed' positioning to ensure it stays behind everything.
      */}
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
      
      <main className="flex-grow w-full mx-auto px-4 sm:px-6 lg:px-8 py-24 relative z-10 overflow-y-auto custom-scrollbar">
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

      <footer className="fixed bottom-0 w-full py-3 bg-[#030712]/80 backdrop-blur-xl border-t border-white/5 z-50">
         <div className="max-w-7xl mx-auto px-4 flex justify-between items-center text-[10px] text-slate-500 font-medium tracking-wider uppercase">
            <span>Project R.A.M.A. v3.0 • Ashish</span>
            <span className="flex items-center gap-2">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
              </span>
              Connected
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
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.2);
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