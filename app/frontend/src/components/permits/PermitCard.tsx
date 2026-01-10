import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  MapPin,
  Calendar,
  Building,
  DollarSign,
  ArrowRight,
  Clock,
  User,
  FileText,
} from 'lucide-react';
import type { PermitApplication } from '../../types';
import { StatusBadge } from './StatusBadge';

interface PermitCardProps {
  permit: PermitApplication;
  index?: number;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function getPermitTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    building: 'Building Permit',
    development: 'Development Permit',
    demolition: 'Demolition Permit',
    electrical: 'Electrical Permit',
    plumbing: 'Plumbing Permit',
    mechanical: 'Mechanical Permit',
    gas: 'Gas Permit',
  };
  return labels[type] || type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

function getWorkTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    new_construction: 'New Construction',
    addition: 'Addition',
    renovation: 'Renovation',
    alteration: 'Alteration',
    demolition: 'Demolition',
    repair: 'Repair',
    change_of_use: 'Change of Use',
  };
  return labels[type] || type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

export function PermitCard({ permit, index = 0 }: PermitCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Link
        to={`/permits/${permit.id}`}
        className="block bg-white rounded-2xl border border-slate-200 shadow-sm
                   hover:shadow-lg hover:border-slate-300 transition-all duration-200 group"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3 min-w-0">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 to-amber-600
                              flex items-center justify-center shadow-sm flex-shrink-0">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <div className="min-w-0">
                <h3 className="font-semibold text-slate-900 truncate group-hover:text-amber-600 transition-colors">
                  {permit.application_number || `Draft #${permit.id.slice(0, 8)}`}
                </h3>
                <p className="text-sm text-slate-500">
                  {getPermitTypeLabel(permit.permit_type)}
                </p>
              </div>
            </div>
            <StatusBadge status={permit.status} size="md" />
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Address */}
          <div className="flex items-start gap-3">
            <MapPin className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-slate-900">{permit.project_address}</p>
              {permit.project_description && (
                <p className="text-sm text-slate-500 mt-0.5 line-clamp-2">
                  {permit.project_description}
                </p>
              )}
            </div>
          </div>

          {/* Details grid */}
          <div className="grid grid-cols-2 gap-4">
            {/* Work type */}
            <div className="flex items-center gap-2 text-sm">
              <Building className="w-4 h-4 text-slate-400" />
              <span className="text-slate-600">{getWorkTypeLabel(permit.work_type)}</span>
            </div>

            {/* Estimated value */}
            {permit.estimated_value && (
              <div className="flex items-center gap-2 text-sm">
                <DollarSign className="w-4 h-4 text-slate-400" />
                <span className="text-slate-600">{formatCurrency(permit.estimated_value)}</span>
              </div>
            )}

            {/* Applicant */}
            <div className="flex items-center gap-2 text-sm">
              <User className="w-4 h-4 text-slate-400" />
              <span className="text-slate-600 truncate">{permit.applicant_name}</span>
            </div>

            {/* Created date */}
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span className="text-slate-600">{formatDate(permit.created_at)}</span>
            </div>
          </div>

          {/* Building details if available */}
          {(permit.building_area_sqm || permit.storeys) && (
            <div className="flex items-center gap-4 pt-2 text-xs text-slate-500">
              {permit.building_area_sqm && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-100">
                  {permit.building_area_sqm.toLocaleString()} m²
                </span>
              )}
              {permit.storeys && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-100">
                  {permit.storeys} {permit.storeys === 1 ? 'storey' : 'storeys'}
                </span>
              )}
              {permit.occupancy_type && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-100">
                  {permit.occupancy_type.replace(/_/g, ' ')}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 rounded-b-2xl flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs text-slate-500">
            {permit.submitted_at && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Submitted {formatDate(permit.submitted_at)}
              </span>
            )}
            {permit.approved_at && (
              <span className="flex items-center gap-1 text-teal-600">
                Approved {formatDate(permit.approved_at)}
              </span>
            )}
          </div>
          <span className="inline-flex items-center gap-1 text-sm font-medium text-amber-600
                          group-hover:translate-x-1 transition-transform">
            View Details
            <ArrowRight className="w-4 h-4" />
          </span>
        </div>
      </Link>
    </motion.div>
  );
}

// Compact list item version
export function PermitListItem({ permit, index = 0 }: PermitCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
    >
      <Link
        to={`/permits/${permit.id}`}
        className="flex items-center gap-4 p-4 bg-white rounded-xl border border-slate-200
                   hover:border-slate-300 hover:shadow-md transition-all group"
      >
        <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-slate-500" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-slate-900 truncate group-hover:text-amber-600 transition-colors">
              {permit.application_number || `Draft #${permit.id.slice(0, 8)}`}
            </h4>
            <StatusBadge status={permit.status} size="sm" />
          </div>
          <p className="text-sm text-slate-500 truncate">{permit.project_address}</p>
        </div>

        <div className="text-right flex-shrink-0">
          <p className="text-sm font-medium text-slate-900">
            {getPermitTypeLabel(permit.permit_type)}
          </p>
          <p className="text-xs text-slate-500">{formatDate(permit.created_at)}</p>
        </div>

        <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 transition-colors" />
      </Link>
    </motion.div>
  );
}

// Skeleton loading state
export function PermitCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm animate-pulse">
      <div className="px-6 py-4 border-b border-slate-100">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-200" />
            <div>
              <div className="h-5 w-32 bg-slate-200 rounded mb-1" />
              <div className="h-4 w-24 bg-slate-100 rounded" />
            </div>
          </div>
          <div className="h-6 w-20 bg-slate-100 rounded-full" />
        </div>
      </div>
      <div className="p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="w-4 h-4 bg-slate-200 rounded mt-0.5" />
          <div className="flex-1">
            <div className="h-5 w-3/4 bg-slate-200 rounded mb-1" />
            <div className="h-4 w-1/2 bg-slate-100 rounded" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-4 bg-slate-100 rounded" />
          ))}
        </div>
      </div>
      <div className="px-6 py-3 bg-slate-50 rounded-b-2xl flex justify-between">
        <div className="h-4 w-32 bg-slate-200 rounded" />
        <div className="h-4 w-24 bg-slate-200 rounded" />
      </div>
    </div>
  );
}
