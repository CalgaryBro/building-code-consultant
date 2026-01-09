import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Eye,
  Play,
  Loader2,
  ChevronDown,
  Edit3,
  Check,
  X,
  Shield,
  Download,
  Users,
  UploadCloud,
  Sparkles,
  ClipboardCheck,
} from 'lucide-react';
import type { Document, ExtractedData, ComplianceCheck } from '../types';

// Blueprint background component
function BlueprintBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-slate-50" />

      {/* Blueprint grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #1e3a5f 1px, transparent 1px),
            linear-gradient(to bottom, #1e3a5f 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Subtle cross-hatch */}
      <div
        className="absolute inset-0 opacity-[0.01]"
        style={{
          backgroundImage: `
            repeating-linear-gradient(45deg, transparent, transparent 80px, #1e3a5f 80px, #1e3a5f 81px),
            repeating-linear-gradient(-45deg, transparent, transparent 80px, #1e3a5f 80px, #1e3a5f 81px)
          `,
        }}
      />
    </div>
  );
}

// Animated border for upload zone
function AnimatedBorder({ isDragging }: { isDragging: boolean }) {
  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
      <rect
        x="2"
        y="2"
        width="calc(100% - 4px)"
        height="calc(100% - 4px)"
        rx="16"
        fill="none"
        stroke={isDragging ? '#f59e0b' : '#cbd5e1'}
        strokeWidth="2"
        strokeDasharray="8 8"
        className="transition-all duration-300"
        style={{
          strokeDashoffset: isDragging ? '16' : '0',
          animation: isDragging ? 'dash 0.5s linear infinite' : 'none',
        }}
      />
      <style>{`
        @keyframes dash {
          to { stroke-dashoffset: 0; }
          from { stroke-dashoffset: 16; }
        }
      `}</style>
    </svg>
  );
}

// Status seal component - like an official stamp
function StatusSeal({ status, size = 'md' }: { status: 'pass' | 'fail' | 'warning' | 'needs_review'; size?: 'sm' | 'md' | 'lg' }) {
  const config = {
    pass: { bg: 'from-teal-500 to-teal-600', icon: CheckCircle2, label: 'APPROVED' },
    fail: { bg: 'from-rose-500 to-rose-600', icon: XCircle, label: 'FAILED' },
    warning: { bg: 'from-amber-500 to-amber-600', icon: AlertTriangle, label: 'WARNING' },
    needs_review: { bg: 'from-slate-500 to-slate-600', icon: HelpCircle, label: 'REVIEW' },
  };

  const { bg, icon: Icon, label } = config[status];
  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-16 h-16',
    lg: 'w-20 h-20',
  };

  return (
    <motion.div
      className={`${sizeClasses[size]} rounded-full bg-gradient-to-br ${bg} flex items-center justify-center shadow-lg relative`}
      initial={{ scale: 0, rotate: -180 }}
      animate={{ scale: 1, rotate: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 15 }}
    >
      <Icon className={`${size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'} text-white`} />
      <div className="absolute inset-0 rounded-full border-2 border-white/30" />
      {size === 'lg' && (
        <span className="absolute -bottom-6 text-[10px] font-bold tracking-widest text-slate-500">
          {label}
        </span>
      )}
    </motion.div>
  );
}

// Mock data
const mockDocuments: Document[] = [
  {
    id: '1',
    project_id: 'p1',
    filename: 'floor-plan-ground.pdf',
    file_path: '/uploads/floor-plan-ground.pdf',
    file_type: 'pdf',
    file_size_bytes: 2450000,
    document_type: 'floor_plan',
    extraction_status: 'complete',
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    project_id: 'p1',
    filename: 'site-plan.pdf',
    file_path: '/uploads/site-plan.pdf',
    file_type: 'pdf',
    file_size_bytes: 1820000,
    document_type: 'site_plan',
    extraction_status: 'complete',
    created_at: new Date().toISOString(),
  },
];

const mockExtractedData: ExtractedData[] = [
  {
    id: 'e1',
    document_id: '1',
    field_name: 'stair_width',
    field_category: 'dimension',
    value_raw: '900mm',
    value_numeric: 900,
    unit: 'mm',
    confidence: 'HIGH',
    is_verified: true,
    verified_value: '900',
    created_at: new Date().toISOString(),
  },
  {
    id: 'e2',
    document_id: '1',
    field_name: 'corridor_width',
    field_category: 'dimension',
    value_raw: '1100mm',
    value_numeric: 1100,
    unit: 'mm',
    confidence: 'MEDIUM',
    is_verified: false,
    created_at: new Date().toISOString(),
  },
  {
    id: 'e3',
    document_id: '2',
    field_name: 'front_setback',
    field_category: 'dimension',
    value_raw: '6.0m',
    value_numeric: 6.0,
    unit: 'm',
    confidence: 'HIGH',
    is_verified: true,
    verified_value: '6.0',
    created_at: new Date().toISOString(),
  },
];

const mockChecks: ComplianceCheck[] = [
  {
    id: 'c1',
    project_id: 'p1',
    check_category: 'egress',
    check_name: 'Stair Width',
    element: 'stair_width',
    required_value: '≥ 860 mm',
    actual_value: '900 mm',
    status: 'pass',
    message: 'Stair width meets minimum requirement',
    code_reference: 'NBC 9.8.4.1',
    is_verified: true,
    created_at: new Date().toISOString(),
  },
  {
    id: 'c2',
    project_id: 'p1',
    check_category: 'egress',
    check_name: 'Corridor Width',
    element: 'corridor_width',
    required_value: '≥ 1100 mm',
    actual_value: '1100 mm',
    status: 'pass',
    message: 'Corridor width meets requirement (minimum for egress)',
    code_reference: 'NBC 9.9.3.1',
    is_verified: false,
    created_at: new Date().toISOString(),
  },
  {
    id: 'c3',
    project_id: 'p1',
    check_category: 'zoning',
    check_name: 'Front Setback',
    element: 'front_setback',
    required_value: '≥ 6.0 m',
    actual_value: '6.0 m',
    status: 'pass',
    code_reference: 'LUB 1P2007 R-C1',
    is_verified: true,
    created_at: new Date().toISOString(),
  },
  {
    id: 'c4',
    project_id: 'p1',
    check_category: 'fire',
    check_name: 'Smoke Alarms',
    element: 'smoke_alarms',
    required_value: 'Each floor + bedrooms',
    actual_value: undefined,
    status: 'needs_review',
    message: 'Could not determine smoke alarm locations from drawings',
    code_reference: 'NBC 9.10.19.1',
    is_verified: false,
    created_at: new Date().toISOString(),
  },
];

const statusConfig = {
  pass: { icon: CheckCircle2, color: 'text-teal-600', bg: 'bg-teal-50', border: 'border-teal-200', gradient: 'from-teal-500 to-teal-600' },
  fail: { icon: XCircle, color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-200', gradient: 'from-rose-500 to-rose-600' },
  warning: { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', gradient: 'from-amber-500 to-amber-600' },
  needs_review: { icon: HelpCircle, color: 'text-slate-600', bg: 'bg-slate-100', border: 'border-slate-200', gradient: 'from-slate-500 to-slate-600' },
};

const categoryIcons = {
  egress: '🚪',
  zoning: '📐',
  fire: '🔥',
  structural: '🏗️',
  plumbing: '🚿',
  electrical: '⚡',
};

export function ReviewPage() {
  const [documents] = useState<Document[]>(mockDocuments);
  const [extractedData, setExtractedData] = useState<ExtractedData[]>(mockExtractedData);
  const [checks] = useState<ComplianceCheck[]>(mockChecks);
  const [isDragging, setIsDragging] = useState(false);
  const [isRunningChecks, setIsRunningChecks] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['egress', 'zoning', 'fire']);
  const [editingValue, setEditingValue] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    console.log('Dropped files:', files);
  }, []);

  const runComplianceChecks = async () => {
    setIsRunningChecks(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsRunningChecks(false);
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  const startEditing = (data: ExtractedData) => {
    setEditingValue(data.id);
    setEditValue(data.verified_value || data.value_raw || '');
  };

  const saveEdit = (id: string) => {
    setExtractedData((prev) =>
      prev.map((d) =>
        d.id === id
          ? { ...d, is_verified: true, verified_value: editValue }
          : d
      )
    );
    setEditingValue(null);
  };

  const cancelEdit = () => {
    setEditingValue(null);
    setEditValue('');
  };

  // Group checks by category
  const checksByCategory = checks.reduce((acc, check) => {
    if (!acc[check.check_category]) acc[check.check_category] = [];
    acc[check.check_category].push(check);
    return acc;
  }, {} as Record<string, ComplianceCheck[]>);

  // Calculate summary
  const summary = {
    total: checks.length,
    pass: checks.filter((c) => c.status === 'pass').length,
    fail: checks.filter((c) => c.status === 'fail').length,
    warning: checks.filter((c) => c.status === 'warning').length,
    needsReview: checks.filter((c) => c.status === 'needs_review').length,
  };

  return (
    <div className="min-h-screen">
      <BlueprintBackground />

      <div className="p-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-200">
              <ClipboardCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-display text-4xl text-slate-900">
                Compliance Review
              </h1>
              <p className="text-slate-600">
                Upload drawings, extract parameters, verify code compliance
              </p>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Documents & Extraction */}
          <div className="lg:col-span-2 space-y-6">
            {/* Upload area */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className={`relative bg-white rounded-2xl p-10 transition-all duration-300 ${
                isDragging ? 'shadow-xl shadow-amber-100' : 'shadow-sm'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <AnimatedBorder isDragging={isDragging} />

              <div className="text-center relative z-10">
                <motion.div
                  className={`w-20 h-20 mx-auto mb-6 rounded-2xl flex items-center justify-center transition-all duration-300 ${
                    isDragging
                      ? 'bg-gradient-to-br from-amber-500 to-amber-600 shadow-lg shadow-amber-200'
                      : 'bg-slate-100'
                  }`}
                  animate={{
                    scale: isDragging ? 1.1 : 1,
                    y: isDragging ? -10 : 0,
                  }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                >
                  <UploadCloud className={`w-10 h-10 transition-colors ${
                    isDragging ? 'text-white' : 'text-slate-400'
                  }`} />
                </motion.div>

                <h3 className="font-display text-xl text-slate-900 mb-2">
                  {isDragging ? 'Drop your drawings here' : 'Upload Architectural Drawings'}
                </h3>
                <p className="text-slate-500 mb-6 max-w-md mx-auto">
                  Drop your floor plans, site plans, and elevations here. We'll extract dimensions
                  and check code compliance automatically.
                </p>

                <div className="flex items-center justify-center gap-4">
                  <motion.button
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200"
                    whileHover={{ scale: 1.02, boxShadow: '0 20px 40px -12px rgba(251, 191, 36, 0.4)' }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Upload className="w-4 h-4" />
                    Select Files
                  </motion.button>
                  <span className="text-sm text-slate-400">or drag and drop</span>
                </div>

                <p className="mt-4 text-xs text-slate-400">
                  PDF, PNG, JPG up to 50MB each
                </p>
              </div>
            </motion.div>

            {/* Uploaded documents */}
            {documents.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
              >
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-slate-600" />
                    </div>
                    <h2 className="font-semibold text-slate-900">
                      Uploaded Documents
                    </h2>
                    <span className="text-sm text-slate-500">({documents.length})</span>
                  </div>
                </div>
                <div className="divide-y divide-slate-100">
                  {documents.map((doc, index) => (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + index * 0.1 }}
                      className="p-4 flex items-center gap-4 hover:bg-slate-50 transition-colors group"
                    >
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm">
                        <FileText className="w-6 h-6 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 truncate">{doc.filename}</p>
                        <p className="text-sm text-slate-500">
                          {doc.document_type?.replace('_', ' ')} • {(doc.file_size_bytes! / 1024 / 1024).toFixed(1)}MB
                        </p>
                      </div>
                      <span className={`
                        inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
                        ${doc.extraction_status === 'complete'
                          ? 'bg-teal-100 text-teal-700'
                          : 'bg-amber-100 text-amber-700'
                        }
                      `}>
                        {doc.extraction_status === 'complete' ? (
                          <>
                            <CheckCircle2 className="w-3 h-3" />
                            Extracted
                          </>
                        ) : (
                          <>
                            <Loader2 className="w-3 h-3 animate-spin" />
                            Processing
                          </>
                        )}
                      </span>
                      <motion.button
                        className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors opacity-0 group-hover:opacity-100"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        <Eye className="w-4 h-4" />
                      </motion.button>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Extracted values */}
            {extractedData.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
              >
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-amber-600" />
                    </div>
                    <h2 className="font-semibold text-slate-900">
                      Extracted Values
                    </h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-500">
                      {extractedData.filter((d) => d.is_verified).length}/{extractedData.length} verified
                    </span>
                    <div className="w-24 h-2 rounded-full bg-slate-100 overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-teal-500 to-teal-400 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${(extractedData.filter((d) => d.is_verified).length / extractedData.length) * 100}%` }}
                        transition={{ duration: 0.5, delay: 0.5 }}
                      />
                    </div>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Field
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Value
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Confidence
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {extractedData.map((data, index) => (
                        <motion.tr
                          key={data.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.4 + index * 0.05 }}
                          className="hover:bg-slate-50 transition-colors"
                        >
                          <td className="px-6 py-4">
                            <span className="font-medium text-slate-900 capitalize">
                              {data.field_name.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            {editingValue === data.id ? (
                              <div className="flex items-center gap-2">
                                <input
                                  type="text"
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  className="px-3 py-1.5 rounded-lg border-2 border-amber-500 bg-white text-slate-900 font-mono w-24 outline-none ring-2 ring-amber-100"
                                  autoFocus
                                />
                                <span className="text-slate-500 font-mono text-sm">{data.unit}</span>
                                <motion.button
                                  onClick={() => saveEdit(data.id)}
                                  className="p-1.5 rounded-lg bg-teal-500 text-white"
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                >
                                  <Check className="w-3.5 h-3.5" />
                                </motion.button>
                                <motion.button
                                  onClick={cancelEdit}
                                  className="p-1.5 rounded-lg bg-slate-200 text-slate-600"
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                >
                                  <X className="w-3.5 h-3.5" />
                                </motion.button>
                              </div>
                            ) : (
                              <span className="font-mono text-slate-700 bg-slate-100 px-2 py-1 rounded">
                                {data.is_verified ? data.verified_value : data.value_raw} {data.unit}
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`
                              inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold
                              ${data.confidence === 'HIGH'
                                ? 'bg-teal-100 text-teal-700'
                                : data.confidence === 'MEDIUM'
                                  ? 'bg-amber-100 text-amber-700'
                                  : 'bg-rose-100 text-rose-700'
                              }
                            `}>
                              {data.confidence}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            {data.is_verified ? (
                              <span className="flex items-center gap-1.5 text-teal-600 text-sm font-medium">
                                <CheckCircle2 className="w-4 h-4" />
                                Verified
                              </span>
                            ) : (
                              <span className="flex items-center gap-1.5 text-amber-600 text-sm font-medium">
                                <AlertTriangle className="w-4 h-4" />
                                Pending
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-right">
                            {!data.is_verified && editingValue !== data.id && (
                              <motion.button
                                onClick={() => startEditing(data)}
                                className="p-2 rounded-lg text-slate-400 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                              >
                                <Edit3 className="w-4 h-4" />
                              </motion.button>
                            )}
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* Compliance checks */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
            >
              <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                    <Shield className="w-4 h-4 text-white" />
                  </div>
                  <h2 className="font-semibold text-slate-900">
                    Compliance Checks
                  </h2>
                </div>
                <motion.button
                  onClick={runComplianceChecks}
                  disabled={isRunningChecks}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-200 disabled:opacity-70"
                  whileHover={!isRunningChecks ? { scale: 1.02 } : {}}
                  whileTap={!isRunningChecks ? { scale: 0.98 } : {}}
                >
                  {isRunningChecks ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Run Checks
                    </>
                  )}
                </motion.button>
              </div>

              <div className="divide-y divide-slate-100">
                {Object.entries(checksByCategory).map(([category, categoryChecks]) => (
                  <div key={category}>
                    <button
                      onClick={() => toggleCategory(category)}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">
                          {categoryIcons[category as keyof typeof categoryIcons] || '📋'}
                        </span>
                        <span className="font-semibold text-slate-900 capitalize">{category}</span>
                        <span className="text-sm text-slate-500">
                          {categoryChecks.length} check{categoryChecks.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex gap-1.5">
                          {categoryChecks.filter((c) => c.status === 'pass').length > 0 && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-teal-100 text-teal-700">
                              <CheckCircle2 className="w-3 h-3" />
                              {categoryChecks.filter((c) => c.status === 'pass').length}
                            </span>
                          )}
                          {categoryChecks.filter((c) => c.status === 'fail').length > 0 && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-700">
                              <XCircle className="w-3 h-3" />
                              {categoryChecks.filter((c) => c.status === 'fail').length}
                            </span>
                          )}
                          {categoryChecks.filter((c) => c.status === 'needs_review').length > 0 && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                              <HelpCircle className="w-3 h-3" />
                              {categoryChecks.filter((c) => c.status === 'needs_review').length}
                            </span>
                          )}
                        </div>
                        <motion.div
                          animate={{ rotate: expandedCategories.includes(category) ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ChevronDown className="w-5 h-5 text-slate-400" />
                        </motion.div>
                      </div>
                    </button>

                    <AnimatePresence>
                      {expandedCategories.includes(category) && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="px-6 pb-4 space-y-3">
                            {categoryChecks.map((check, index) => {
                              const config = statusConfig[check.status];
                              const Icon = config.icon;

                              return (
                                <motion.div
                                  key={check.id}
                                  initial={{ opacity: 0, x: -20 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: index * 0.05 }}
                                  className={`p-4 rounded-xl border ${config.bg} ${config.border} relative overflow-hidden`}
                                >
                                  {/* Status indicator bar */}
                                  <div className={`absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b ${config.gradient}`} />

                                  <div className="flex items-start gap-3 pl-3">
                                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${config.gradient} flex items-center justify-center flex-shrink-0`}>
                                      <Icon className="w-4 h-4 text-white" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center justify-between gap-2">
                                        <h4 className="font-semibold text-slate-900">{check.check_name}</h4>
                                        {check.code_reference && (
                                          <span className="text-xs font-mono px-2 py-1 rounded bg-white/80 text-slate-600 border border-slate-200">
                                            {check.code_reference}
                                          </span>
                                        )}
                                      </div>
                                      <div className="mt-2 flex items-center gap-4 text-sm">
                                        {check.required_value && (
                                          <span className="text-slate-600">
                                            <span className="text-slate-400">Required:</span> {check.required_value}
                                          </span>
                                        )}
                                        {check.actual_value && (
                                          <span className="text-slate-600">
                                            <span className="text-slate-400">Actual:</span>{' '}
                                            <span className="font-semibold">{check.actual_value}</span>
                                          </span>
                                        )}
                                      </div>
                                      {check.message && (
                                        <p className="mt-2 text-sm text-slate-500">{check.message}</p>
                                      )}
                                    </div>
                                  </div>
                                </motion.div>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Right column - Summary */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sticky top-8"
            >
              <h2 className="font-display text-xl text-slate-900 mb-6">
                Review Summary
              </h2>

              {/* Overall status seal */}
              <div className="flex justify-center mb-8">
                <StatusSeal
                  status={
                    summary.fail > 0 ? 'fail' :
                    summary.needsReview > 0 ? 'needs_review' :
                    summary.warning > 0 ? 'warning' :
                    'pass'
                  }
                  size="lg"
                />
              </div>

              {/* Status message */}
              <div className={`p-4 rounded-xl mb-6 text-center ${
                summary.fail > 0 ? 'bg-rose-50 border border-rose-200' :
                summary.needsReview > 0 ? 'bg-slate-100 border border-slate-200' :
                summary.warning > 0 ? 'bg-amber-50 border border-amber-200' :
                'bg-teal-50 border border-teal-200'
              }`}>
                <p className={`font-semibold ${
                  summary.fail > 0 ? 'text-rose-900' :
                  summary.needsReview > 0 ? 'text-slate-900' :
                  summary.warning > 0 ? 'text-amber-900' :
                  'text-teal-900'
                }`}>
                  {summary.fail > 0 ? 'Compliance Issues Found' :
                   summary.needsReview > 0 ? 'Manual Review Required' :
                   summary.warning > 0 ? 'Warnings Present' :
                   'All Checks Passed'}
                </p>
                <p className={`text-sm mt-1 ${
                  summary.fail > 0 ? 'text-rose-700' :
                  summary.needsReview > 0 ? 'text-slate-600' :
                  summary.warning > 0 ? 'text-amber-700' :
                  'text-teal-700'
                }`}>
                  {summary.fail > 0 ? `${summary.fail} issue${summary.fail > 1 ? 's' : ''} must be resolved` :
                   summary.needsReview > 0 ? `${summary.needsReview} check${summary.needsReview > 1 ? 's' : ''} need verification` :
                   summary.warning > 0 ? 'Review warnings before submission' :
                   'Ready for permit submission'}
                </p>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="p-4 rounded-xl bg-gradient-to-br from-teal-50 to-teal-100 border border-teal-200">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle2 className="w-4 h-4 text-teal-600" />
                    <span className="text-xs font-semibold text-teal-700 uppercase">Passing</span>
                  </div>
                  <p className="font-display text-3xl text-teal-900">{summary.pass}</p>
                </div>
                <div className="p-4 rounded-xl bg-gradient-to-br from-rose-50 to-rose-100 border border-rose-200">
                  <div className="flex items-center gap-2 mb-1">
                    <XCircle className="w-4 h-4 text-rose-600" />
                    <span className="text-xs font-semibold text-rose-700 uppercase">Failed</span>
                  </div>
                  <p className="font-display text-3xl text-rose-900">{summary.fail}</p>
                </div>
                <div className="p-4 rounded-xl bg-gradient-to-br from-amber-50 to-amber-100 border border-amber-200">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span className="text-xs font-semibold text-amber-700 uppercase">Warnings</span>
                  </div>
                  <p className="font-display text-3xl text-amber-900">{summary.warning}</p>
                </div>
                <div className="p-4 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200">
                  <div className="flex items-center gap-2 mb-1">
                    <HelpCircle className="w-4 h-4 text-slate-600" />
                    <span className="text-xs font-semibold text-slate-600 uppercase">Review</span>
                  </div>
                  <p className="font-display text-3xl text-slate-900">{summary.needsReview}</p>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 mb-6">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-amber-900 text-sm">Professional Verification Required</p>
                    <p className="text-xs text-amber-700 mt-1">
                      All extracted values and compliance checks must be verified by a qualified
                      professional before permit submission.
                    </p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-3">
                <motion.button
                  className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-semibold bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Download className="w-4 h-4" />
                  Export Report
                </motion.button>
                <motion.button
                  className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-semibold border-2 border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Users className="w-4 h-4" />
                  Request Professional Review
                </motion.button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
