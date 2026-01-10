import { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle2,
  Loader2,
  Eye,
  AlertTriangle,
} from 'lucide-react';
import type { PermitDocument } from '../../types';

interface DocumentUploadProps {
  documents: PermitDocument[];
  documentTypes: string[];
  isUploading: boolean;
  onUpload: (file: File, documentType: string) => Promise<void>;
  onRemove: (documentId: string) => Promise<void>;
  disabled?: boolean;
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
        rx="12"
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

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export function DocumentUpload({
  documents,
  documentTypes,
  isUploading,
  onUpload,
  onRemove,
  disabled = false,
}: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedType, setSelectedType] = useState<string>(documentTypes[0] || '');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;

      setUploadError(null);
      const files = Array.from(e.dataTransfer.files);

      for (const file of files) {
        try {
          await onUpload(file, selectedType);
        } catch (err) {
          setUploadError(err instanceof Error ? err.message : 'Upload failed');
        }
      }
    },
    [disabled, selectedType, onUpload]
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      setUploadError(null);

      for (const file of files) {
        try {
          await onUpload(file, selectedType);
        } catch (err) {
          setUploadError(err instanceof Error ? err.message : 'Upload failed');
        }
      }

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    [selectedType, onUpload]
  );

  const handleRemove = useCallback(
    async (documentId: string) => {
      setRemovingId(documentId);
      try {
        await onRemove(documentId);
      } catch (err) {
        console.error('Failed to remove document:', err);
      } finally {
        setRemovingId(null);
      }
    },
    [onRemove]
  );

  const handleSelectFilesClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-6">
      {/* Document type selector */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Document Type
        </label>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          disabled={disabled}
          className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 bg-white text-slate-900
                     focus:border-amber-500 focus:ring-4 focus:ring-amber-100 outline-none transition-all
                     disabled:bg-slate-50 disabled:text-slate-400"
        >
          {documentTypes.map((type) => (
            <option key={type} value={type}>
              {type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      {/* Upload area */}
      <div
        className={`relative rounded-xl p-8 transition-all duration-300 ${
          isDragging ? 'shadow-xl shadow-amber-100 bg-amber-50' : 'bg-white'
        } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <AnimatedBorder isDragging={isDragging} />

        <div className="text-center relative z-10">
          <motion.div
            className={`w-16 h-16 mx-auto mb-4 rounded-xl flex items-center justify-center transition-all duration-300 ${
              isDragging
                ? 'bg-gradient-to-br from-amber-500 to-amber-600 shadow-lg shadow-amber-200'
                : 'bg-slate-100'
            }`}
            animate={{
              scale: isDragging ? 1.1 : 1,
              y: isDragging ? -5 : 0,
            }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          >
            <UploadCloud
              className={`w-8 h-8 transition-colors ${
                isDragging ? 'text-white' : 'text-slate-400'
              }`}
            />
          </motion.div>

          <h3 className="font-semibold text-slate-900 mb-1">
            {isDragging ? 'Drop your files here' : 'Upload Documents'}
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            Drag and drop files or click to browse
          </p>

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg,.dwg,.dxf"
            onChange={handleFileSelect}
            className="hidden"
            disabled={disabled}
          />

          <div className="flex items-center justify-center gap-3">
            <motion.button
              type="button"
              onClick={handleSelectFilesClick}
              disabled={disabled || isUploading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold
                         bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200
                         disabled:opacity-70 disabled:cursor-not-allowed"
              whileHover={!disabled && !isUploading ? { scale: 1.02 } : {}}
              whileTap={!disabled && !isUploading ? { scale: 0.98 } : {}}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Select Files
                </>
              )}
            </motion.button>
          </div>

          <p className="mt-4 text-xs text-slate-400">
            PDF, PNG, JPG, DWG, DXF up to 50MB each
          </p>

          {/* Upload error */}
          {uploadError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-sm text-rose-700 flex items-center gap-2"
            >
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {uploadError}
            </motion.div>
          )}
        </div>
      </div>

      {/* Uploaded documents list */}
      {documents.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-700">
            Uploaded Documents ({documents.length})
          </h4>

          <div className="space-y-2">
            <AnimatePresence>
              {documents.map((doc, index) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center gap-4 p-4 bg-white rounded-xl border border-slate-200
                             hover:border-slate-300 transition-colors group"
                >
                  {/* File icon */}
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600
                                  flex items-center justify-center shadow-sm flex-shrink-0">
                    <FileText className="w-5 h-5 text-white" />
                  </div>

                  {/* File info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-900 truncate">{doc.filename}</p>
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span>{doc.document_type.replace(/_/g, ' ')}</span>
                      <span>{formatFileSize(doc.file_size_bytes)}</span>
                      {doc.verified && (
                        <span className="inline-flex items-center gap-1 text-teal-600">
                          <CheckCircle2 className="w-3 h-3" />
                          Verified
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <motion.button
                      className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      <Eye className="w-4 h-4" />
                    </motion.button>
                    {!disabled && (
                      <motion.button
                        onClick={() => handleRemove(doc.id)}
                        disabled={removingId === doc.id}
                        className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50
                                   transition-colors disabled:opacity-50"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        {removingId === doc.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </motion.button>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  );
}

// Compact document list for viewing
export function DocumentList({
  documents,
  showVerificationStatus = true,
}: {
  documents: PermitDocument[];
  showVerificationStatus?: boolean;
}) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-6">
        <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
        <p className="text-sm text-slate-500">No documents uploaded</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
            <FileText className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">{doc.filename}</p>
            <p className="text-xs text-slate-500">{doc.document_type.replace(/_/g, ' ')}</p>
          </div>
          {showVerificationStatus && (
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                doc.verified
                  ? 'bg-teal-100 text-teal-700'
                  : 'bg-amber-100 text-amber-700'
              }`}
            >
              {doc.verified ? (
                <>
                  <CheckCircle2 className="w-3 h-3" />
                  Verified
                </>
              ) : (
                <>
                  <AlertTriangle className="w-3 h-3" />
                  Pending
                </>
              )}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
