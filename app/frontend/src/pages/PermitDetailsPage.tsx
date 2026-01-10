import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Edit3,
  MapPin,
  Building,
  User,
  Calendar,
  FileText,
  Clock,
  Send,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  MessageSquare,
  Phone,
  Mail,
} from 'lucide-react';
import { permitsApi, ApiError } from '../api/client';
import { StatusBadge, StatusIndicator } from '../components/permits/StatusBadge';
import { Timeline } from '../components/permits/Timeline';
import { DocumentList } from '../components/permits/DocumentUpload';

// Blueprint background component
function BlueprintBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-amber-50/30" />
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
      <div className="absolute top-0 left-0 w-64 h-64 border-l-2 border-t-2 border-slate-200/50 pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-64 h-64 border-r-2 border-b-2 border-slate-200/50 pointer-events-none" />
    </div>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-CA', {
    year: 'numeric',
    month: 'long',
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

// Severity badge for deficiencies
function SeverityBadge({ severity }: { severity: 'critical' | 'major' | 'minor' }) {
  const config = {
    critical: { bg: 'bg-rose-100', text: 'text-rose-700', border: 'border-rose-200' },
    major: { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-200' },
    minor: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200' },
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${config[severity].bg} ${config[severity].text} ${config[severity].border}`}
    >
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </span>
  );
}

// Deficiency status badge
function DeficiencyStatusBadge({ status }: { status: 'open' | 'resolved' | 'waived' }) {
  const config = {
    open: { bg: 'bg-rose-100', text: 'text-rose-700', icon: AlertTriangle },
    resolved: { bg: 'bg-teal-100', text: 'text-teal-700', icon: CheckCircle2 },
    waived: { bg: 'bg-slate-100', text: 'text-slate-600', icon: XCircle },
  };

  const Icon = config[status].icon;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${config[status].bg} ${config[status].text}`}
    >
      <Icon className="w-3 h-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export function PermitDetailsPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'timeline' | 'deficiencies' | 'comments'>('overview');
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Fetch application
  const {
    data: application,
    isLoading: isLoadingApplication,
    isError: isApplicationError,
    error: applicationError,
  } = useQuery({
    queryKey: ['permits', 'application', id],
    queryFn: () => permitsApi.getApplication(id!),
    enabled: !!id,
  });

  // Fetch documents
  const { data: documents = [], isLoading: isLoadingDocuments } = useQuery({
    queryKey: ['permits', 'documents', id],
    queryFn: () => permitsApi.listDocuments(id!),
    enabled: !!id,
  });

  // Fetch timeline
  const { data: timeline = [], isLoading: isLoadingTimeline } = useQuery({
    queryKey: ['permits', 'timeline', id],
    queryFn: () => permitsApi.getTimeline(id!),
    enabled: !!id,
  });

  // Fetch deficiencies
  const { data: deficiencies = [], isLoading: isLoadingDeficiencies } = useQuery({
    queryKey: ['permits', 'deficiencies', id],
    queryFn: () => permitsApi.listDeficiencies(id!),
    enabled: !!id,
  });

  // Fetch comments
  const { data: comments = [], isLoading: isLoadingComments } = useQuery({
    queryKey: ['permits', 'comments', id],
    queryFn: () => permitsApi.listComments(id!),
    enabled: !!id,
  });

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: () => permitsApi.submitApplication(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permits', 'application', id] });
      queryClient.invalidateQueries({ queryKey: ['permits', 'timeline', id] });
      setSubmitError(null);
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        setSubmitError(error.message);
      } else {
        setSubmitError('Failed to submit application');
      }
    },
  });

  if (isLoadingApplication) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
      </div>
    );
  }

  if (isApplicationError || !application) {
    return (
      <div className="min-h-screen">
        <BlueprintBackground />
        <div className="p-8 max-w-4xl mx-auto">
          <Link
            to="/permits"
            className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Permits
          </Link>
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 text-center">
            <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-4" />
            <h3 className="font-semibold text-rose-900 mb-2">Application Not Found</h3>
            <p className="text-sm text-rose-700">
              {applicationError instanceof Error ? applicationError.message : 'The requested application could not be found.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const openDeficiencies = deficiencies.filter((d) => d.status === 'open').length;

  return (
    <div className="min-h-screen">
      <BlueprintBackground />

      <div className="p-8 max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Link
            to="/permits"
            className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Permits
          </Link>

          <div className="flex items-start justify-between gap-6 flex-wrap">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-200">
                <FileText className="w-8 h-8 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="font-display text-3xl text-slate-900">
                    {application.application_number || `Draft Application`}
                  </h1>
                  <StatusBadge status={application.status} size="lg" />
                </div>
                <p className="text-slate-600 mt-1">{getPermitTypeLabel(application.permit_type)}</p>
                <div className="flex items-center gap-2 mt-2 text-sm text-slate-500">
                  <Calendar className="w-4 h-4" />
                  Created {formatDate(application.created_at)}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {application.status === 'draft' && (
                <>
                  <Link
                    to={`/permits/${id}/edit`}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold
                               border-2 border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    <Edit3 className="w-4 h-4" />
                    Edit
                  </Link>
                  <motion.button
                    onClick={() => submitMutation.mutate()}
                    disabled={submitMutation.isPending}
                    className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold
                               bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-lg shadow-teal-200
                               disabled:opacity-70"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {submitMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        Submit for Review
                      </>
                    )}
                  </motion.button>
                </>
              )}
            </div>
          </div>

          {submitError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3"
            >
              <AlertTriangle className="w-5 h-5 text-rose-500" />
              <p className="text-sm text-rose-700">{submitError}</p>
            </motion.div>
          )}
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex items-center gap-1 p-1 bg-white rounded-xl border border-slate-200 shadow-sm mb-6"
        >
          {[
            { id: 'overview', label: 'Overview', icon: Building },
            { id: 'documents', label: 'Documents', icon: FileText, count: documents.length },
            { id: 'timeline', label: 'Timeline', icon: Clock, count: timeline.length },
            { id: 'deficiencies', label: 'Deficiencies', icon: AlertTriangle, count: openDeficiencies },
            { id: 'comments', label: 'Comments', icon: MessageSquare, count: comments.length },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  isActive
                    ? 'bg-amber-500 text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span
                    className={`px-1.5 py-0.5 rounded-full text-xs font-bold ${
                      isActive ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-600'
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </motion.div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="grid grid-cols-1 lg:grid-cols-3 gap-6"
            >
              {/* Main content */}
              <div className="lg:col-span-2 space-y-6">
                {/* Project Details */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
                      <Building className="w-4 h-4 text-amber-600" />
                    </div>
                    <h2 className="font-semibold text-slate-900">Project Details</h2>
                  </div>
                  <div className="p-6 space-y-6">
                    {/* Address */}
                    <div className="flex items-start gap-3">
                      <MapPin className="w-5 h-5 text-slate-400 mt-0.5" />
                      <div>
                        <p className="text-sm text-slate-500">Project Address</p>
                        <p className="font-medium text-slate-900">{application.project_address}</p>
                      </div>
                    </div>

                    {/* Description */}
                    {application.project_description && (
                      <div>
                        <p className="text-sm text-slate-500 mb-1">Description</p>
                        <p className="text-slate-700">{application.project_description}</p>
                      </div>
                    )}

                    {/* Details grid */}
                    <div className="grid grid-cols-2 gap-6 pt-4 border-t border-slate-100">
                      <div>
                        <p className="text-sm text-slate-500">Permit Type</p>
                        <p className="font-medium text-slate-900">{getPermitTypeLabel(application.permit_type)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-500">Work Type</p>
                        <p className="font-medium text-slate-900">{getWorkTypeLabel(application.work_type)}</p>
                      </div>
                      {application.estimated_value && (
                        <div>
                          <p className="text-sm text-slate-500">Estimated Value</p>
                          <p className="font-medium text-slate-900">{formatCurrency(application.estimated_value)}</p>
                        </div>
                      )}
                      {application.building_area_sqm && (
                        <div>
                          <p className="text-sm text-slate-500">Building Area</p>
                          <p className="font-medium text-slate-900">{application.building_area_sqm.toLocaleString()} m²</p>
                        </div>
                      )}
                      {application.storeys && (
                        <div>
                          <p className="text-sm text-slate-500">Storeys</p>
                          <p className="font-medium text-slate-900">{application.storeys}</p>
                        </div>
                      )}
                      {application.occupancy_type && (
                        <div>
                          <p className="text-sm text-slate-500">Occupancy Type</p>
                          <p className="font-medium text-slate-900 capitalize">{application.occupancy_type.replace(/_/g, ' ')}</p>
                        </div>
                      )}
                      {application.construction_type && (
                        <div>
                          <p className="text-sm text-slate-500">Construction Type</p>
                          <p className="font-medium text-slate-900 capitalize">{application.construction_type.replace(/_/g, ' ')}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Applicant Details */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
                      <User className="w-4 h-4 text-blue-600" />
                    </div>
                    <h2 className="font-semibold text-slate-900">Applicant Information</h2>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-2 gap-6">
                      <div className="flex items-center gap-3">
                        <User className="w-5 h-5 text-slate-400" />
                        <div>
                          <p className="text-sm text-slate-500">Name</p>
                          <p className="font-medium text-slate-900">{application.applicant_name}</p>
                          {application.company_name && (
                            <p className="text-sm text-slate-500">{application.company_name}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Mail className="w-5 h-5 text-slate-400" />
                        <div>
                          <p className="text-sm text-slate-500">Email</p>
                          <a href={`mailto:${application.applicant_email}`} className="font-medium text-amber-600 hover:text-amber-700">
                            {application.applicant_email}
                          </a>
                        </div>
                      </div>
                      {application.applicant_phone && (
                        <div className="flex items-center gap-3">
                          <Phone className="w-5 h-5 text-slate-400" />
                          <div>
                            <p className="text-sm text-slate-500">Phone</p>
                            <a href={`tel:${application.applicant_phone}`} className="font-medium text-slate-900">
                              {application.applicant_phone}
                            </a>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Status card */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                  <div className="flex justify-center mb-6">
                    <StatusIndicator status={application.status} />
                  </div>

                  <div className="space-y-4">
                    {application.submitted_at && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">Submitted</span>
                        <span className="font-medium text-slate-900">{formatDate(application.submitted_at)}</span>
                      </div>
                    )}
                    {application.reviewed_at && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">Reviewed</span>
                        <span className="font-medium text-slate-900">{formatDate(application.reviewed_at)}</span>
                      </div>
                    )}
                    {application.approved_at && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">Approved</span>
                        <span className="font-medium text-teal-600">{formatDate(application.approved_at)}</span>
                      </div>
                    )}
                    {application.expires_at && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">Expires</span>
                        <span className="font-medium text-slate-900">{formatDate(application.expires_at)}</span>
                      </div>
                    )}
                  </div>

                  {application.reviewer_notes && (
                    <div className="mt-4 pt-4 border-t border-slate-100">
                      <p className="text-sm text-slate-500 mb-2">Reviewer Notes</p>
                      <p className="text-sm text-slate-700">{application.reviewer_notes}</p>
                    </div>
                  )}
                </div>

                {/* Quick stats */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Quick Stats</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-500">Documents</span>
                      <span className="text-sm font-medium text-slate-900">{documents.length}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-500">Open Deficiencies</span>
                      <span className={`text-sm font-medium ${openDeficiencies > 0 ? 'text-rose-600' : 'text-teal-600'}`}>
                        {openDeficiencies}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-500">Timeline Events</span>
                      <span className="text-sm font-medium text-slate-900">{timeline.length}</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Documents Tab */}
          {activeTab === 'documents' && (
            <motion.div
              key="documents"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-semibold text-slate-900">Uploaded Documents</h2>
                {application.status === 'draft' && (
                  <Link
                    to={`/permits/${id}/edit`}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                               text-amber-600 hover:bg-amber-50 transition-colors"
                  >
                    <Edit3 className="w-4 h-4" />
                    Manage Documents
                  </Link>
                )}
              </div>
              {isLoadingDocuments ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
                </div>
              ) : (
                <DocumentList documents={documents} />
              )}
            </motion.div>
          )}

          {/* Timeline Tab */}
          {activeTab === 'timeline' && (
            <motion.div
              key="timeline"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
            >
              <h2 className="font-semibold text-slate-900 mb-6">Application Timeline</h2>
              <Timeline events={timeline} isLoading={isLoadingTimeline} />
            </motion.div>
          )}

          {/* Deficiencies Tab */}
          {activeTab === 'deficiencies' && (
            <motion.div
              key="deficiencies"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
            >
              <h2 className="font-semibold text-slate-900 mb-6">Deficiencies</h2>
              {isLoadingDeficiencies ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
                </div>
              ) : deficiencies.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle2 className="w-12 h-12 text-teal-500 mx-auto mb-4" />
                  <h3 className="font-semibold text-slate-900 mb-2">No Deficiencies</h3>
                  <p className="text-sm text-slate-600">This application has no recorded deficiencies.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {deficiencies.map((deficiency, index) => (
                    <motion.div
                      key={deficiency.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`p-4 rounded-xl border ${
                        deficiency.status === 'open'
                          ? 'bg-rose-50 border-rose-200'
                          : deficiency.status === 'resolved'
                            ? 'bg-teal-50 border-teal-200'
                            : 'bg-slate-50 border-slate-200'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-semibold text-slate-900">{deficiency.deficiency_type}</span>
                            <SeverityBadge severity={deficiency.severity} />
                            <DeficiencyStatusBadge status={deficiency.status} />
                          </div>
                          <p className="text-sm text-slate-700">{deficiency.description}</p>
                          {deficiency.code_reference && (
                            <p className="text-xs text-slate-500 mt-2 font-mono">{deficiency.code_reference}</p>
                          )}
                          {deficiency.resolution_notes && (
                            <div className="mt-3 pt-3 border-t border-slate-200">
                              <p className="text-xs text-slate-500">Resolution Notes</p>
                              <p className="text-sm text-slate-700">{deficiency.resolution_notes}</p>
                            </div>
                          )}
                        </div>
                        <div className="text-right text-xs text-slate-500">
                          <p>{formatDate(deficiency.created_at)}</p>
                          {deficiency.created_by && <p className="mt-1">by {deficiency.created_by}</p>}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Comments Tab */}
          {activeTab === 'comments' && (
            <motion.div
              key="comments"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
            >
              <h2 className="font-semibold text-slate-900 mb-6">Comments</h2>
              {isLoadingComments ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
                </div>
              ) : comments.length === 0 ? (
                <div className="text-center py-12">
                  <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="font-semibold text-slate-900 mb-2">No Comments</h3>
                  <p className="text-sm text-slate-600">No comments have been added to this application.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {comments.map((comment, index) => (
                    <motion.div
                      key={comment.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-4 rounded-xl bg-slate-50 border border-slate-200"
                    >
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
                            <User className="w-4 h-4 text-slate-500" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{comment.author_name}</p>
                            {comment.author_role && (
                              <p className="text-xs text-slate-500">{comment.author_role}</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {comment.is_internal && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">
                              Internal
                            </span>
                          )}
                          <span className="text-xs text-slate-500">{formatDate(comment.created_at)}</span>
                        </div>
                      </div>
                      <p className="text-sm text-slate-700 pl-10">{comment.content}</p>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
