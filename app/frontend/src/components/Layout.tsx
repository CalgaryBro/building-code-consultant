import { useState, useRef, useEffect, type ReactNode } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Map,
  FileCheck,
  Building2,
  ExternalLink,
  User,
  LogOut,
  ChevronDown,
  Settings,
  Mail,
  ClipboardList,
  Shield,
  Users,
  LayoutDashboard,
  Lock,
  ListChecks,
  Calculator,
  Ruler,
} from 'lucide-react';
import type { AppMode } from '../types';
import { useAuth } from '../contexts/AuthContext';

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
  {
    id: 'permits',
    label: 'PERMITS',
    description: 'Track applications',
    icon: ClipboardList,
  },
];

// Role badge component
function RoleBadge({ role }: { role: string }) {
  const config = {
    admin: { bg: 'bg-rose-500/20', text: 'text-rose-400', label: 'Admin' },
    reviewer: { bg: 'bg-teal-500/20', text: 'text-teal-400', label: 'Reviewer' },
    user: { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'Free' },
  }[role] || { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'User' };

  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}

// User dropdown component
function UserDropdown() {
  const { user, logout, isLoading, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch {
      // Error handled by context
    }
  };

  // Get user initials for avatar
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  if (!user) {
    return null;
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 w-full p-3 rounded-lg hover:bg-slate-800/50 transition-colors group"
      >
        {/* Avatar */}
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-400 to-amber-500 flex items-center justify-center text-slate-900 font-semibold text-sm shadow-lg">
          {getInitials(user.full_name)}
        </div>

        {/* User info */}
        <div className="flex-1 text-left min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white truncate">{user.full_name}</span>
            <RoleBadge role={user.role} />
          </div>
          <div className="text-xs text-slate-400 truncate">{user.email}</div>
        </div>

        {/* Chevron */}
        <ChevronDown
          className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute bottom-full left-0 right-0 mb-2 bg-slate-800 rounded-lg border border-slate-700 shadow-xl overflow-hidden"
          >
            {/* Email verification status */}
            {!user.is_verified && (
              <div className="px-3 py-2 bg-amber-500/10 border-b border-slate-700">
                <div className="flex items-center gap-2 text-xs text-amber-400">
                  <Mail className="w-3.5 h-3.5" />
                  <span>Email not verified</span>
                </div>
              </div>
            )}

            <div className="py-1">
              <button
                onClick={() => {
                  setIsOpen(false);
                  navigate('/settings');
                }}
                className="flex items-center gap-3 w-full px-3 py-2 text-sm text-slate-300 hover:bg-slate-700/50 hover:text-white transition-colors"
              >
                <Settings className="w-4 h-4" />
                Settings
              </button>

              <div className="my-1 border-t border-slate-700" />

              <button
                onClick={handleLogout}
                disabled={isLoading}
                className="flex items-center gap-3 w-full px-3 py-2 text-sm text-rose-400 hover:bg-slate-700/50 hover:text-rose-300 transition-colors disabled:opacity-50"
              >
                <LogOut className="w-4 h-4" />
                {isLoading ? 'Signing out...' : 'Sign out'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const { isAuthenticated, isAdmin, isReviewer } = useAuth();
  const currentMode = location.pathname.split('/')[1] || 'explore';

  // Define which modes require authentication
  const protectedModes = ['review', 'permits'];

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
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider px-4 mb-3">
            Operating Mode
          </p>
          {modes.map((mode, index) => {
            const Icon = mode.icon;
            const isActive = currentMode === mode.id;
            const requiresAuth = protectedModes.includes(mode.id);
            const isLocked = requiresAuth && !isAuthenticated;

            return (
              <motion.div
                key={mode.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <NavLink
                  to={isLocked ? '/login' : `/${mode.id}`}
                  className={`${isActive ? 'mode-indicator-active' : 'mode-indicator-inactive'} ${isLocked ? 'opacity-60' : ''}`}
                >
                  <div className="relative">
                    <Icon className="w-5 h-5" />
                    {isLocked && (
                      <Lock className="w-3 h-3 absolute -top-1 -right-1 text-slate-400" />
                    )}
                  </div>
                  <div>
                    <div className="font-medium text-sm">{mode.label}</div>
                    <div className="text-xs opacity-60">{mode.description}</div>
                  </div>
                </NavLink>
              </motion.div>
            );
          })}

          {/* Reviewer Section - Only for reviewers and admins */}
          {isReviewer && (
            <>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider px-4 mb-3 mt-6">
                Review Queue
              </p>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <NavLink
                  to="/review-queue"
                  className={currentMode === 'review-queue' ? 'mode-indicator-active' : 'mode-indicator-inactive'}
                >
                  <ListChecks className="w-5 h-5" />
                  <div>
                    <div className="font-medium text-sm">Pending Reviews</div>
                    <div className="text-xs opacity-60">Applications to review</div>
                  </div>
                </NavLink>
              </motion.div>
            </>
          )}

          {/* Admin Section - Only for admins */}
          {isAdmin && (
            <>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider px-4 mb-3 mt-6">
                Admin
              </p>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <NavLink
                  to="/admin"
                  className={currentMode === 'admin' ? 'mode-indicator-active' : 'mode-indicator-inactive'}
                >
                  <LayoutDashboard className="w-5 h-5" />
                  <div>
                    <div className="font-medium text-sm">Dashboard</div>
                    <div className="text-xs opacity-60">System overview</div>
                  </div>
                </NavLink>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                <NavLink
                  to="/admin/users"
                  className={location.pathname === '/admin/users' ? 'mode-indicator-active' : 'mode-indicator-inactive'}
                >
                  <Users className="w-5 h-5" />
                  <div>
                    <div className="font-medium text-sm">Users</div>
                    <div className="text-xs opacity-60">Manage accounts</div>
                  </div>
                </NavLink>
              </motion.div>
            </>
          )}

          {/* Tools Section - Available to all users */}
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider px-4 mb-3 mt-6">
            Tools
          </p>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <NavLink
              to="/dssp"
              className={currentMode === 'dssp' ? 'mode-indicator-active' : 'mode-indicator-inactive'}
            >
              <Calculator className="w-5 h-5" />
              <div>
                <div className="font-medium text-sm">DSSP Calculator</div>
                <div className="text-xs opacity-60">Stormwater & servicing</div>
              </div>
            </NavLink>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <NavLink
              to="/quantity-survey"
              className={currentMode === 'quantity-survey' ? 'mode-indicator-active' : 'mode-indicator-inactive'}
            >
              <Ruler className="w-5 h-5" />
              <div>
                <div className="font-medium text-sm">Quantity Survey</div>
                <div className="text-xs opacity-60">Material estimates</div>
              </div>
            </NavLink>
          </motion.div>
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

        {/* User dropdown or sign in link */}
        <div className="p-4 border-t border-slate-800">
          {isAuthenticated ? (
            <UserDropdown />
          ) : (
            <NavLink
              to="/login"
              className="flex items-center gap-3 w-full p-3 rounded-lg hover:bg-slate-800/50 transition-colors group"
            >
              <div className="w-9 h-9 rounded-lg bg-slate-700 flex items-center justify-center">
                <User className="w-5 h-5 text-slate-400 group-hover:text-white transition-colors" />
              </div>
              <div className="flex-1 text-left">
                <div className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                  Sign in
                </div>
                <div className="text-xs text-slate-500">Access all features</div>
              </div>
            </NavLink>
          )}
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
