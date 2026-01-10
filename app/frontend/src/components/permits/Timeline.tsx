import { motion } from 'framer-motion';
import {
  FileEdit,
  Send,
  Search,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  MessageSquare,
  Upload,
  Clock,
  User,
  Settings,
} from 'lucide-react';
import type { PermitTimelineEvent } from '../../types';

interface TimelineProps {
  events: PermitTimelineEvent[];
  isLoading?: boolean;
}

const eventTypeConfig: Record<
  string,
  {
    icon: typeof FileEdit;
    color: string;
    bgColor: string;
    borderColor: string;
  }
> = {
  created: {
    icon: FileEdit,
    color: 'text-slate-600',
    bgColor: 'bg-slate-100',
    borderColor: 'border-slate-200',
  },
  submitted: {
    icon: Send,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200',
  },
  under_review: {
    icon: Search,
    color: 'text-amber-600',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-200',
  },
  deficiency_issued: {
    icon: AlertTriangle,
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200',
  },
  deficiency_resolved: {
    icon: CheckCircle2,
    color: 'text-teal-600',
    bgColor: 'bg-teal-100',
    borderColor: 'border-teal-200',
  },
  approved: {
    icon: CheckCircle2,
    color: 'text-teal-600',
    bgColor: 'bg-teal-100',
    borderColor: 'border-teal-200',
  },
  rejected: {
    icon: XCircle,
    color: 'text-rose-600',
    bgColor: 'bg-rose-100',
    borderColor: 'border-rose-200',
  },
  document_uploaded: {
    icon: Upload,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200',
  },
  document_verified: {
    icon: FileText,
    color: 'text-teal-600',
    bgColor: 'bg-teal-100',
    borderColor: 'border-teal-200',
  },
  comment_added: {
    icon: MessageSquare,
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200',
  },
  status_changed: {
    icon: Settings,
    color: 'text-slate-600',
    bgColor: 'bg-slate-100',
    borderColor: 'border-slate-200',
  },
  default: {
    icon: Clock,
    color: 'text-slate-600',
    bgColor: 'bg-slate-100',
    borderColor: 'border-slate-200',
  },
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-CA', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
}

export function Timeline({ events, isLoading = false }: TimelineProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-4 animate-pulse">
            <div className="w-10 h-10 rounded-full bg-slate-200" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-200 rounded w-1/3" />
              <div className="h-3 bg-slate-100 rounded w-2/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-8">
        <Clock className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="font-medium text-slate-600">No timeline events yet</p>
        <p className="text-sm text-slate-500 mt-1">
          Events will appear here as the application progresses
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />

      <div className="space-y-6">
        {events.map((event, index) => {
          const config = eventTypeConfig[event.event_type] || eventTypeConfig.default;
          const Icon = config.icon;

          return (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative flex gap-4"
            >
              {/* Icon */}
              <div
                className={`
                  relative z-10 w-10 h-10 rounded-full flex items-center justify-center
                  ${config.bgColor} border-2 ${config.borderColor}
                `}
              >
                <Icon className={`w-4 h-4 ${config.color}`} />
              </div>

              {/* Content */}
              <div className="flex-1 pt-1">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="font-semibold text-slate-900">{event.title}</h4>
                    {event.description && (
                      <p className="text-sm text-slate-600 mt-0.5">{event.description}</p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-slate-500">{formatRelativeTime(event.created_at)}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {formatDate(event.created_at)} at {formatTime(event.created_at)}
                    </p>
                  </div>
                </div>

                {/* Created by */}
                {event.created_by && (
                  <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-500">
                    <User className="w-3 h-3" />
                    <span>{event.created_by}</span>
                  </div>
                )}

                {/* Metadata */}
                {event.metadata && Object.keys(event.metadata).length > 0 && (
                  <div className="mt-2 p-2 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                      {Object.entries(event.metadata).map(([key, value]) => (
                        <span key={key} className="text-slate-600">
                          <span className="text-slate-400">{key.replace(/_/g, ' ')}:</span>{' '}
                          <span className="font-medium">{String(value)}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// Compact version for cards
export function TimelineMini({ events, maxItems = 3 }: { events: PermitTimelineEvent[]; maxItems?: number }) {
  const displayEvents = events.slice(0, maxItems);

  return (
    <div className="space-y-2">
      {displayEvents.map((event) => {
        const config = eventTypeConfig[event.event_type] || eventTypeConfig.default;
        const Icon = config.icon;

        return (
          <div key={event.id} className="flex items-center gap-2 text-sm">
            <div
              className={`
                w-6 h-6 rounded-full flex items-center justify-center
                ${config.bgColor}
              `}
            >
              <Icon className={`w-3 h-3 ${config.color}`} />
            </div>
            <span className="flex-1 text-slate-700 truncate">{event.title}</span>
            <span className="text-xs text-slate-400 flex-shrink-0">
              {formatRelativeTime(event.created_at)}
            </span>
          </div>
        );
      })}
      {events.length > maxItems && (
        <p className="text-xs text-slate-500 text-center">
          +{events.length - maxItems} more events
        </p>
      )}
    </div>
  );
}
