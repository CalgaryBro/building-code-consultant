import { motion } from 'framer-motion';
import {
  FileEdit,
  Send,
  Search,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Ban,
} from 'lucide-react';
import type { PermitStatus } from '../../types';

interface StatusBadgeProps {
  status: PermitStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  animated?: boolean;
}

const statusConfig: Record<
  PermitStatus,
  {
    label: string;
    icon: typeof FileEdit;
    bg: string;
    text: string;
    border: string;
    gradient: string;
  }
> = {
  draft: {
    label: 'Draft',
    icon: FileEdit,
    bg: 'bg-slate-100',
    text: 'text-slate-700',
    border: 'border-slate-200',
    gradient: 'from-slate-400 to-slate-500',
  },
  submitted: {
    label: 'Submitted',
    icon: Send,
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
    gradient: 'from-blue-500 to-blue-600',
  },
  under_review: {
    label: 'Under Review',
    icon: Search,
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
    gradient: 'from-amber-500 to-amber-600',
  },
  deficiency_issued: {
    label: 'Deficiency Issued',
    icon: AlertTriangle,
    bg: 'bg-orange-50',
    text: 'text-orange-700',
    border: 'border-orange-200',
    gradient: 'from-orange-500 to-orange-600',
  },
  approved: {
    label: 'Approved',
    icon: CheckCircle2,
    bg: 'bg-teal-50',
    text: 'text-teal-700',
    border: 'border-teal-200',
    gradient: 'from-teal-500 to-teal-600',
  },
  rejected: {
    label: 'Rejected',
    icon: XCircle,
    bg: 'bg-rose-50',
    text: 'text-rose-700',
    border: 'border-rose-200',
    gradient: 'from-rose-500 to-rose-600',
  },
  expired: {
    label: 'Expired',
    icon: Clock,
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    border: 'border-gray-300',
    gradient: 'from-gray-400 to-gray-500',
  },
  cancelled: {
    label: 'Cancelled',
    icon: Ban,
    bg: 'bg-gray-100',
    text: 'text-gray-500',
    border: 'border-gray-200',
    gradient: 'from-gray-400 to-gray-500',
  },
};

const sizeClasses = {
  sm: {
    container: 'px-2 py-0.5 text-xs',
    icon: 'w-3 h-3',
    gap: 'gap-1',
  },
  md: {
    container: 'px-2.5 py-1 text-xs',
    icon: 'w-3.5 h-3.5',
    gap: 'gap-1.5',
  },
  lg: {
    container: 'px-3 py-1.5 text-sm',
    icon: 'w-4 h-4',
    gap: 'gap-2',
  },
};

export function StatusBadge({
  status,
  size = 'md',
  showIcon = true,
  animated = false,
}: StatusBadgeProps) {
  const config = statusConfig[status];
  const sizes = sizeClasses[size];
  const Icon = config.icon;

  const badge = (
    <span
      className={`
        inline-flex items-center ${sizes.gap} ${sizes.container}
        rounded-full font-semibold border
        ${config.bg} ${config.text} ${config.border}
      `}
    >
      {showIcon && <Icon className={sizes.icon} />}
      {config.label}
    </span>
  );

  if (animated) {
    return (
      <motion.span
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      >
        {badge}
      </motion.span>
    );
  }

  return badge;
}

// Larger status indicator for detail pages
export function StatusIndicator({
  status,
  showLabel = true,
}: {
  status: PermitStatus;
  showLabel?: boolean;
}) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <motion.div
      className="flex flex-col items-center gap-2"
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 15 }}
    >
      <div
        className={`
          w-16 h-16 rounded-full bg-gradient-to-br ${config.gradient}
          flex items-center justify-center shadow-lg relative
        `}
      >
        <Icon className="w-8 h-8 text-white" />
        <div className="absolute inset-0 rounded-full border-2 border-white/30" />
      </div>
      {showLabel && (
        <span className="text-sm font-bold tracking-wider text-slate-600 uppercase">
          {config.label}
        </span>
      )}
    </motion.div>
  );
}

export { statusConfig };
