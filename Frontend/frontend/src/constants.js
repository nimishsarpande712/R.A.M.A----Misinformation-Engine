import { 
  CheckCircle, 
  XCircle, 
  AlertOctagon, 
  AlertTriangle 
} from 'lucide-react';

export const COLORS = {
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

export const CATEGORIES = ["Health", "Election", "Disaster", "Communal", "Finance", "Other"];

export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi' },
  { code: 'mr', label: 'Marathi' },
  { code: 'te', label: 'Telugu' }
];
