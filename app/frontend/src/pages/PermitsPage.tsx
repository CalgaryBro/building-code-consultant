import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { useQuery } from '@tanstack/react-query';
import {
  Plus,
  Search,
  LayoutGrid,
  List,
  ChevronLeft,
  ChevronRight,
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Building2,
  TrendingUp,
  ArrowLeft,
} from 'lucide-react';
import type { PermitStatus, PermitApplicationsListParams } from '../types';
import { permitsApi } from '../api/client';
import { PermitCard, PermitListItem, PermitCardSkeleton } from '../components/permits/PermitCard';

// Blueprint background component
function BlueprintBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-amber-50/30" />

      {/* Blueprint grid */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #1e3a5f 1px, transparent 1px),
            linear-gradient(to bottom, #1e3a5f 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-64 h-64 border-l-2 border-t-2 border-slate-200/50 pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-64 h-64 border-r-2 border-b-2 border-slate-200/50 pointer-events-none" />
    </div>
  );
}

const statusFilters: { value: PermitStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All Applications' },
  { value: 'draft', label: 'Drafts' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'deficiency_issued', label: 'Deficiencies' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
];

const permitTypeFilters: { value: string; label: string }[] = [
  { value: 'all', label: 'All Types' },
  { value: 'building', label: 'Building' },
  { value: 'development', label: 'Development' },
  { value: 'demolition', label: 'Demolition' },
  { value: 'electrical', label: 'Electrical' },
  { value: 'plumbing', label: 'Plumbing' },
  { value: 'mechanical', label: 'Mechanical' },
];

export function PermitsPage() {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [statusFilter, setStatusFilter] = useState<PermitStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12;

  // Build query params
  const queryParams: PermitApplicationsListParams = {
    page: currentPage,
    limit: pageSize,
  };
  if (statusFilter !== 'all') queryParams.status = statusFilter;
  if (typeFilter !== 'all') queryParams.permit_type = typeFilter;
  if (searchQuery.trim()) queryParams.search = searchQuery.trim();

  // Fetch applications
  const {
    data: applicationsData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['permits', 'applications', queryParams],
    queryFn: () => permitsApi.listApplications(queryParams),
  });

  // Fetch statistics
  const { data: statistics } = useQuery({
    queryKey: ['permits', 'statistics'],
    queryFn: () => permitsApi.getStatistics(),
  });

  const applications = applicationsData?.items || [];
  const totalPages = applicationsData?.pages || 1;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
  };

  return (
    <div className="min-h-screen">
      <BlueprintBackground />

      <div className="p-8 max-w-7xl mx-auto">
        {/* Back Button - Show for admins */}
        {isAdmin && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="mb-4"
          >
            <button
              onClick={() => navigate('/admin')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="font-medium">Back to Dashboard</span>
            </button>
          </motion.div>
        )}

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-600
                              flex items-center justify-center shadow-lg shadow-amber-200">
                <FileText className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="font-display text-4xl text-slate-900">Permit Tracker</h1>
                <p className="text-slate-600 mt-1">Manage and track your permit applications</p>
              </div>
            </div>

            <Link
              to="/permits/new"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold
                         bg-gradient-to-r from-amber-500 to-amber-600 text-white
                         shadow-lg shadow-amber-200 hover:shadow-xl hover:shadow-amber-200
                         transition-all duration-200"
            >
              <Plus className="w-5 h-5" />
              New Application
            </Link>
          </div>
        </motion.div>

        {/* Statistics Cards */}
        {statistics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
          >
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-slate-600" />
                </div>
                <span className="text-sm font-medium text-slate-500">Total</span>
              </div>
              <p className="font-display text-3xl text-slate-900">{statistics.total_applications}</p>
              <p className="text-xs text-slate-500 mt-1">All applications</p>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-amber-600" />
                </div>
                <span className="text-sm font-medium text-slate-500">Pending</span>
              </div>
              <p className="font-display text-3xl text-amber-600">{statistics.pending_review}</p>
              <p className="text-xs text-slate-500 mt-1">Awaiting review</p>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-teal-100 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-teal-600" />
                </div>
                <span className="text-sm font-medium text-slate-500">Approved</span>
              </div>
              <p className="font-display text-3xl text-teal-600">
                {statistics.by_status.approved || 0}
              </p>
              <p className="text-xs text-slate-500 mt-1">This period</p>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                </div>
                <span className="text-sm font-medium text-slate-500">Avg. Days</span>
              </div>
              <p className="font-display text-3xl text-blue-600">
                {statistics.average_review_days?.toFixed(0) ?? '—'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Review time</p>
            </div>
          </motion.div>
        )}

        {/* Filters and Search */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 mb-6"
        >
          <div className="flex flex-wrap items-center gap-4">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex-1 min-w-[250px]">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by address, application number, or applicant..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-2.5 rounded-xl border-2 border-slate-200
                             bg-white text-slate-900 placeholder:text-slate-400
                             focus:border-amber-500 focus:ring-4 focus:ring-amber-100
                             outline-none transition-all"
                />
              </div>
            </form>

            {/* Status filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as PermitStatus | 'all');
                setCurrentPage(1);
              }}
              className="px-4 py-2.5 rounded-xl border-2 border-slate-200 bg-white text-slate-900
                         focus:border-amber-500 focus:ring-4 focus:ring-amber-100 outline-none transition-all"
            >
              {statusFilters.map((filter) => (
                <option key={filter.value} value={filter.value}>
                  {filter.label}
                </option>
              ))}
            </select>

            {/* Type filter */}
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="px-4 py-2.5 rounded-xl border-2 border-slate-200 bg-white text-slate-900
                         focus:border-amber-500 focus:ring-4 focus:ring-amber-100 outline-none transition-all"
            >
              {permitTypeFilters.map((filter) => (
                <option key={filter.value} value={filter.value}>
                  {filter.label}
                </option>
              ))}
            </select>

            {/* View toggle */}
            <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-100">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-white text-amber-600 shadow-sm'
                    : 'text-slate-400 hover:text-slate-600'
                }`}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'list'
                    ? 'bg-white text-amber-600 shadow-sm'
                    : 'text-slate-400 hover:text-slate-600'
                }`}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Active filters */}
          {(statusFilter !== 'all' || typeFilter !== 'all' || searchQuery) && (
            <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-100">
              <span className="text-sm text-slate-500">Active filters:</span>
              {statusFilter !== 'all' && (
                <button
                  onClick={() => setStatusFilter('all')}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-amber-100
                             text-amber-700 text-xs font-medium hover:bg-amber-200 transition-colors"
                >
                  Status: {statusFilter.replace(/_/g, ' ')}
                  <span className="ml-1">&times;</span>
                </button>
              )}
              {typeFilter !== 'all' && (
                <button
                  onClick={() => setTypeFilter('all')}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-blue-100
                             text-blue-700 text-xs font-medium hover:bg-blue-200 transition-colors"
                >
                  Type: {typeFilter}
                  <span className="ml-1">&times;</span>
                </button>
              )}
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-100
                             text-slate-700 text-xs font-medium hover:bg-slate-200 transition-colors"
                >
                  Search: "{searchQuery}"
                  <span className="ml-1">&times;</span>
                </button>
              )}
            </div>
          )}
        </motion.div>

        {/* Applications List/Grid */}
        {isLoading ? (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <PermitCardSkeleton key={i} />
            ))}
          </div>
        ) : isError ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-rose-50 border border-rose-200 rounded-2xl p-8 text-center"
          >
            <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-4" />
            <h3 className="font-semibold text-rose-900 mb-2">Failed to load applications</h3>
            <p className="text-sm text-rose-700">{error instanceof Error ? error.message : 'An error occurred'}</p>
          </motion.div>
        ) : applications.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white border border-slate-200 rounded-2xl p-12 text-center"
          >
            <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="font-semibold text-slate-900 mb-2">No applications found</h3>
            <p className="text-slate-600 mb-6">
              {searchQuery || statusFilter !== 'all' || typeFilter !== 'all'
                ? 'Try adjusting your filters or search query.'
                : 'Get started by creating your first permit application.'}
            </p>
            <Link
              to="/permits/new"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold
                         bg-gradient-to-r from-amber-500 to-amber-600 text-white
                         shadow-lg shadow-amber-200 hover:shadow-xl transition-all"
            >
              <Plus className="w-5 h-5" />
              New Application
            </Link>
          </motion.div>
        ) : (
          <>
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {applications.map((permit, index) => (
                  <PermitCard key={permit.id} permit={permit} index={index} />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {applications.map((permit, index) => (
                  <PermitListItem key={permit.id} permit={permit} index={index} />
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="flex items-center justify-center gap-2 mt-8"
              >
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="p-2 rounded-lg border border-slate-200 text-slate-600
                             hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed
                             transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }

                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                          currentPage === pageNum
                            ? 'bg-amber-500 text-white'
                            : 'text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded-lg border border-slate-200 text-slate-600
                             hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed
                             transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </motion.div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
