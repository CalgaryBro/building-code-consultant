import type { ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search,
  Map,
  FileCheck,
  Building2,
  ExternalLink,
} from 'lucide-react';
import type { AppMode } from '../types';

interface LayoutProps {
  children: ReactNode;
}

const modes: { id: AppMode; label: string; description: string; icon: typeof Search }[] = [
  {
    id: 'explore',
    label: 'EXPLORE',
    description: 'Search building codes',
    icon: Search,
  },
  {
    id: 'guide',
    label: 'GUIDE',
    description: 'Permit requirements',
    icon: Map,
  },
  {
    id: 'review',
    label: 'REVIEW',
    description: 'Check compliance',
    icon: FileCheck,
  },
];

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const currentMode = location.pathname.split('/')[1] || 'explore';

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-72 bg-blueprint-dark flex flex-col fixed h-full">
        {/* Logo */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500 flex items-center justify-center">
              <Building2 className="w-6 h-6 text-slate-900" />
            </div>
            <div>
              <h1 className="font-display text-lg text-white">Calgary Codes</h1>
              <p className="text-xs text-slate-500">Building Code Expert</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider px-4 mb-3">
            Operating Mode
          </p>
          {modes.map((mode, index) => {
            const Icon = mode.icon;
            const isActive = currentMode === mode.id;

            return (
              <motion.div
                key={mode.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <NavLink
                  to={`/${mode.id}`}
                  className={isActive ? 'mode-indicator-active' : 'mode-indicator-inactive'}
                >
                  <Icon className="w-5 h-5" />
                  <div>
                    <div className="font-medium text-sm">{mode.label}</div>
                    <div className="text-xs opacity-60">{mode.description}</div>
                  </div>
                </NavLink>
              </motion.div>
            );
          })}
        </nav>

        {/* Code versions */}
        <div className="p-4 border-t border-slate-800">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
            Active Codes
          </p>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">NBC(AE)</span>
              <span className="code-ref bg-slate-800 text-slate-300">2023</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">LUB 1P2007</span>
              <span className="code-ref bg-slate-800 text-slate-300">2025</span>
            </div>
          </div>
        </div>

        {/* Footer links */}
        <div className="p-4 border-t border-slate-800">
          <a
            href="https://www.calgary.ca/planning"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-300 transition-colors"
          >
            <span>City of Calgary Planning</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 ml-72 bg-blueprint min-h-screen">
        {children}
      </main>
    </div>
  );
}
