import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  ArrowRight,
  Save,
  Send,
  Loader2,
  MapPin,
  Building,
  User,
  FileText,
  DollarSign,
  Ruler,
  Layers,
  Home,
  Store,
  Factory,
  Wrench,
  CheckCircle2,
  AlertTriangle,
  Info,
} from 'lucide-react';
import type { CreatePermitApplicationInput } from '../types';
import { permitsApi, ApiError, type AddressAutocompleteResult } from '../api/client';
import { DocumentUpload } from '../components/permits/DocumentUpload';
import { AddressAutocomplete } from '../components/AddressAutocomplete';

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

// Step indicator component
function StepIndicator({ currentStep, steps }: { currentStep: number; steps: { num: number; label: string; icon: typeof User }[] }) {
  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, index) => {
        const Icon = step.icon;
        const isCompleted = currentStep > step.num;
        const isCurrent = currentStep === step.num;

        return (
          <div key={step.num} className="flex items-center">
            <div className="flex flex-col items-center">
              <motion.div
                className={`
                  relative w-12 h-12 rounded-xl flex items-center justify-center
                  transition-all duration-300 shadow-sm
                  ${isCompleted
                    ? 'bg-gradient-to-br from-teal-500 to-teal-600 text-white shadow-teal-200'
                    : isCurrent
                      ? 'bg-gradient-to-br from-amber-500 to-amber-600 text-white shadow-amber-200'
                      : 'bg-white border-2 border-slate-200 text-slate-400'
                  }
                `}
                animate={{ scale: isCurrent ? 1.1 : 1 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              >
                {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                {isCurrent && (
                  <motion.div
                    className="absolute inset-0 rounded-xl border-2 border-amber-400"
                    initial={{ opacity: 0.5, scale: 1 }}
                    animate={{ opacity: 0, scale: 1.3 }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
              </motion.div>
              <span className={`mt-2 text-xs font-medium ${isCurrent ? 'text-amber-600' : isCompleted ? 'text-teal-600' : 'text-slate-400'}`}>
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div className="relative w-16 h-0.5 mx-2">
                <div className="absolute inset-0 bg-slate-200 rounded-full" />
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-amber-500 to-teal-500 rounded-full origin-left"
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: isCompleted ? 1 : 0 }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Form input component
function FormInput({
  label,
  icon: Icon,
  hint,
  error,
  required,
  ...props
}: {
  label: string;
  icon?: typeof MapPin;
  hint?: string;
  error?: string;
  required?: boolean;
} & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-2">
        {label}
        {required && <span className="text-rose-500 ml-1">*</span>}
      </label>
      <div className="relative">
        {Icon && <Icon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />}
        <input
          {...props}
          className={`
            w-full px-4 py-3 rounded-xl border-2
            bg-white text-slate-900 placeholder:text-slate-400
            focus:ring-4 outline-none transition-all duration-200
            ${Icon ? 'pl-12' : ''}
            ${error
              ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-100'
              : 'border-slate-200 focus:border-amber-500 focus:ring-amber-100'
            }
          `}
        />
      </div>
      {hint && !error && (
        <p className="mt-2 text-sm text-slate-500 flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5" />
          {hint}
        </p>
      )}
      {error && (
        <p className="mt-2 text-sm text-rose-600 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5" />
          {error}
        </p>
      )}
    </div>
  );
}

// Selection card component
function SelectionCard({
  selected,
  onClick,
  icon: Icon,
  label,
  description,
}: {
  selected: boolean;
  onClick: () => void;
  icon: typeof Building;
  label: string;
  description: string;
}) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      className={`
        relative p-5 rounded-xl border-2 text-left transition-all duration-200
        ${selected
          ? 'border-amber-500 bg-gradient-to-br from-amber-50 to-orange-50 shadow-lg shadow-amber-100'
          : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-md'
        }
      `}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <motion.div
        className={`
          absolute top-3 right-3 w-5 h-5 rounded-full border-2 flex items-center justify-center
          ${selected ? 'border-amber-500 bg-amber-500' : 'border-slate-300'}
        `}
      >
        {selected && <CheckCircle2 className="w-4 h-4 text-white" />}
      </motion.div>
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${
        selected ? 'bg-gradient-to-br from-amber-500 to-amber-600 text-white' : 'bg-slate-100 text-slate-500'
      }`}>
        <Icon className="w-5 h-5" />
      </div>
      <h4 className={`font-semibold mb-1 ${selected ? 'text-amber-900' : 'text-slate-900'}`}>{label}</h4>
      <p className={`text-sm ${selected ? 'text-amber-700' : 'text-slate-500'}`}>{description}</p>
    </motion.button>
  );
}

const permitTypes = [
  { id: 'BP', label: 'Building Permit', icon: Building, description: 'New construction, additions, alterations' },
  { id: 'DP', label: 'Development Permit', icon: Layers, description: 'Land use and zoning approval' },
  { id: 'TP_ELECTRICAL', label: 'Electrical Permit', icon: FileText, description: 'Electrical system work' },
  { id: 'TP_PLUMBING', label: 'Plumbing Permit', icon: FileText, description: 'Plumbing system work' },
  { id: 'TP_GAS', label: 'Gas Permit', icon: FileText, description: 'Gas system work' },
  { id: 'TP_HVAC', label: 'HVAC Permit', icon: FileText, description: 'Heating and cooling systems' },
];

const workTypes = [
  { id: 'new_construction', label: 'New Construction', icon: Building, description: 'Building from ground up' },
  { id: 'addition', label: 'Addition', icon: Layers, description: 'Expanding existing structure' },
  { id: 'renovation', label: 'Renovation', icon: Wrench, description: 'Interior or exterior changes' },
  { id: 'alteration', label: 'Alteration', icon: Ruler, description: 'Structural modifications' },
  { id: 'repair', label: 'Repair', icon: Wrench, description: 'Fixing existing elements' },
  { id: 'change_of_use', label: 'Change of Use', icon: Store, description: 'Different occupancy type' },
];

const occupancyTypes = [
  { id: 'residential', label: 'Residential', icon: Home, description: 'Houses, apartments, condos' },
  { id: 'commercial', label: 'Commercial', icon: Store, description: 'Offices, retail, restaurants' },
  { id: 'industrial', label: 'Industrial', icon: Factory, description: 'Warehouses, manufacturing' },
  { id: 'mixed', label: 'Mixed Use', icon: Layers, description: 'Residential + commercial' },
];

const steps = [
  { num: 1, label: 'Applicant', icon: User },
  { num: 2, label: 'Project', icon: Building },
  { num: 3, label: 'Details', icon: Ruler },
  { num: 4, label: 'Documents', icon: FileText },
];

export function PermitApplicationPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = !!id;

  const [step, setStep] = useState(1);
  const [formError, setFormError] = useState<string | null>(null);
  // Local form state for user-friendly form fields
  const [applicantName, setApplicantName] = useState('');
  const [applicantEmail, setApplicantEmail] = useState('');
  const [applicantPhone, setApplicantPhone] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [formData, setFormData] = useState<CreatePermitApplicationInput>({
    permit_type: '',
    address: '',
    description: '',
    project_type: '',
    estimated_value: undefined,
    building_area_sqm: undefined,
    building_height_storeys: undefined,
    occupancy_group: '',
  });

  // Load existing application if editing
  const { data: existingApplication, isLoading: isLoadingApplication } = useQuery({
    queryKey: ['permits', 'application', id],
    queryFn: () => permitsApi.getApplication(id!),
    enabled: isEditing,
  });

  // Load document types
  const { data: documentTypes = [] } = useQuery({
    queryKey: ['permits', 'document-types'],
    queryFn: () => permitsApi.getDocumentTypes(),
  });

  // Load documents if editing
  const { data: documents = [], refetch: refetchDocuments } = useQuery({
    queryKey: ['permits', 'documents', id],
    queryFn: () => permitsApi.listDocuments(id!),
    enabled: isEditing,
  });

  useEffect(() => {
    if (existingApplication) {
      // Load applicant info
      setApplicantName(existingApplication.applicant?.name || '');
      setApplicantEmail(existingApplication.applicant?.email || '');
      setApplicantPhone(existingApplication.applicant?.phone || '');
      setCompanyName(existingApplication.applicant?.company || '');

      setFormData({
        permit_type: existingApplication.permit_type,
        address: existingApplication.address,
        project_name: existingApplication.project_name || '',
        description: existingApplication.description || '',
        project_type: existingApplication.project_type || '',
        estimated_value: existingApplication.estimated_value,
        building_area_sqm: existingApplication.building_area_sqm,
        building_height_storeys: existingApplication.building_height_storeys,
        occupancy_group: existingApplication.occupancy_group || '',
      });
    }
  }, [existingApplication]);

  // Create/update mutation
  const saveMutation = useMutation({
    mutationFn: async (data: CreatePermitApplicationInput) => {
      if (isEditing) {
        return permitsApi.updateApplication(id!, data);
      }
      return permitsApi.createApplication(data);
    },
    onSuccess: (application) => {
      if (!isEditing) {
        navigate(`/permits/${application.id}`, { replace: true });
      }
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        setFormError(error.message);
      } else {
        setFormError('Failed to save application');
      }
    },
  });

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: () => permitsApi.submitApplication(id!),
    onSuccess: () => {
      navigate(`/permits/${id}`);
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        setFormError(error.message);
      } else {
        setFormError('Failed to submit application');
      }
    },
  });

  // Upload document mutation
  const uploadMutation = useMutation({
    mutationFn: async ({ file, documentType }: { file: File; documentType: string }) => {
      return permitsApi.uploadDocument(id!, file, documentType);
    },
    onSuccess: () => {
      refetchDocuments();
    },
  });

  const handleUpload = async (file: File, documentType: string) => {
    await uploadMutation.mutateAsync({ file, documentType });
  };

  const handleRemove = async (documentId: string) => {
    await permitsApi.removeDocument(id!, documentId);
    refetchDocuments();
  };

  const canProceed = (currentStep: number): boolean => {
    switch (currentStep) {
      case 1:
        return applicantName.length >= 2 && applicantEmail.includes('@');
      case 2:
        return !!formData.permit_type && !!formData.project_type && formData.address.length >= 5;
      case 3:
        return true; // Optional fields
      case 4:
        return true;
      default:
        return false;
    }
  };

  const buildApplicationData = (): CreatePermitApplicationInput => {
    return {
      ...formData,
      applicant: {
        name: applicantName,
        email: applicantEmail,
        phone: applicantPhone || undefined,
        company: companyName || undefined,
      },
    };
  };

  const handleSaveDraft = async () => {
    setFormError(null);
    await saveMutation.mutateAsync(buildApplicationData());
  };

  const handleSubmit = async () => {
    if (!isEditing) {
      // First save, then submit
      setFormError(null);
      await saveMutation.mutateAsync(buildApplicationData());
      await submitMutation.mutateAsync();
    } else {
      await saveMutation.mutateAsync(buildApplicationData());
      await submitMutation.mutateAsync();
    }
  };

  const slideVariants = {
    enter: { x: 100, opacity: 0 },
    center: { x: 0, opacity: 1 },
    exit: { x: -100, opacity: 0 },
  };

  if (isLoadingApplication) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <BlueprintBackground />

      <div className="p-8 max-w-4xl mx-auto">
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
          <h1 className="font-display text-4xl text-slate-900">
            {isEditing ? 'Edit Application' : 'New Permit Application'}
          </h1>
          <p className="text-slate-600 mt-2">
            Complete the form below to {isEditing ? 'update your' : 'create a new'} permit application.
          </p>
        </motion.div>

        {/* Step indicator */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <StepIndicator currentStep={step} steps={steps} />
        </motion.div>

        {/* Form steps */}
        <AnimatePresence mode="wait">
          {/* Step 1: Applicant Information */}
          {step === 1 && (
            <motion.div
              key="step1"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-lg p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-slate-900">Applicant Information</h2>
                  <p className="text-slate-500">Who is applying for this permit?</p>
                </div>
              </div>

              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <FormInput
                    label="Full Name"
                    icon={User}
                    required
                    placeholder="John Smith"
                    value={applicantName}
                    onChange={(e) => setApplicantName(e.target.value)}
                  />
                  <FormInput
                    label="Company Name"
                    placeholder="Optional"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <FormInput
                    label="Email Address"
                    type="email"
                    required
                    placeholder="john@example.com"
                    value={applicantEmail}
                    onChange={(e) => setApplicantEmail(e.target.value)}
                  />
                  <FormInput
                    label="Phone Number"
                    type="tel"
                    placeholder="(403) 555-0123"
                    value={applicantPhone}
                    onChange={(e) => setApplicantPhone(e.target.value)}
                  />
                </div>
              </div>

              <div className="mt-8 flex justify-end">
                <motion.button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={!canProceed(1)}
                  className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                    canProceed(1)
                      ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200'
                      : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  }`}
                  whileHover={canProceed(1) ? { scale: 1.02 } : {}}
                  whileTap={canProceed(1) ? { scale: 0.98 } : {}}
                >
                  Continue
                  <ArrowRight className="w-4 h-4" />
                </motion.button>
              </div>
            </motion.div>
          )}

          {/* Step 2: Project Information */}
          {step === 2 && (
            <motion.div
              key="step2"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-lg p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center">
                  <Building className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-slate-900">Project Information</h2>
                  <p className="text-slate-500">What type of permit do you need?</p>
                </div>
              </div>

              <div className="space-y-8">
                {/* Permit type */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-4">
                    Permit Type <span className="text-rose-500">*</span>
                  </label>
                  <div className="grid grid-cols-3 gap-4">
                    {permitTypes.map((type) => (
                      <SelectionCard
                        key={type.id}
                        selected={formData.permit_type === type.id}
                        onClick={() => setFormData({ ...formData, permit_type: type.id })}
                        icon={type.icon}
                        label={type.label}
                        description={type.description}
                      />
                    ))}
                  </div>
                </div>

                {/* Work type */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-4">
                    Type of Work <span className="text-rose-500">*</span>
                  </label>
                  <div className="grid grid-cols-3 gap-4">
                    {workTypes.map((type) => (
                      <SelectionCard
                        key={type.id}
                        selected={formData.project_type === type.id}
                        onClick={() => setFormData({ ...formData, project_type: type.id })}
                        icon={type.icon}
                        label={type.label}
                        description={type.description}
                      />
                    ))}
                  </div>
                </div>

                {/* Project address */}
                <AddressAutocomplete
                  label="Project Address"
                  required
                  placeholder="123 Main Street NW, Calgary, AB"
                  value={formData.address}
                  onChange={(value) => setFormData({ ...formData, address: value })}
                  onSelect={(result: AddressAutocompleteResult) => {
                    setFormData({ ...formData, address: result.address });
                  }}
                  hint="Start typing to search Calgary addresses"
                />

                {/* Project description */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Project Description
                  </label>
                  <textarea
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Describe your project briefly..."
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 bg-white text-slate-900
                               placeholder:text-slate-400 focus:border-amber-500 focus:ring-4 focus:ring-amber-100
                               outline-none transition-all resize-none"
                  />
                </div>
              </div>

              <div className="mt-8 flex justify-between">
                <motion.button
                  type="button"
                  onClick={() => setStep(1)}
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-medium text-slate-600 hover:bg-slate-100 transition-colors"
                  whileHover={{ x: -2 }}
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </motion.button>
                <motion.button
                  type="button"
                  onClick={() => setStep(3)}
                  disabled={!canProceed(2)}
                  className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                    canProceed(2)
                      ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200'
                      : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  }`}
                  whileHover={canProceed(2) ? { scale: 1.02 } : {}}
                  whileTap={canProceed(2) ? { scale: 0.98 } : {}}
                >
                  Continue
                  <ArrowRight className="w-4 h-4" />
                </motion.button>
              </div>
            </motion.div>
          )}

          {/* Step 3: Building Details */}
          {step === 3 && (
            <motion.div
              key="step3"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-lg p-8"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center">
                  <Ruler className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-slate-900">Building Details</h2>
                  <p className="text-slate-500">Optional but helps with accurate processing</p>
                </div>
              </div>

              <div className="mt-6 p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3">
                <Info className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-slate-600">
                  These details help determine permit fees and review requirements. Leave blank if unknown.
                </p>
              </div>

              <div className="space-y-8 mt-8">
                {/* Occupancy type */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-4">
                    Occupancy Type
                  </label>
                  <div className="grid grid-cols-4 gap-4">
                    {occupancyTypes.map((type) => (
                      <SelectionCard
                        key={type.id}
                        selected={formData.occupancy_group === type.id}
                        onClick={() => setFormData({ ...formData, occupancy_group: type.id })}
                        icon={type.icon}
                        label={type.label}
                        description={type.description}
                      />
                    ))}
                  </div>
                </div>

                {/* Numeric inputs */}
                <div className="grid grid-cols-3 gap-6">
                  <FormInput
                    label="Estimated Value (CAD)"
                    icon={DollarSign}
                    type="number"
                    min={0}
                    placeholder="500000"
                    value={formData.estimated_value || ''}
                    onChange={(e) => setFormData({ ...formData, estimated_value: parseFloat(e.target.value) || undefined })}
                  />
                  <FormInput
                    label="Building Area (m²)"
                    type="number"
                    min={0}
                    placeholder="250"
                    value={formData.building_area_sqm || ''}
                    onChange={(e) => setFormData({ ...formData, building_area_sqm: parseFloat(e.target.value) || undefined })}
                  />
                  <FormInput
                    label="Number of Storeys"
                    type="number"
                    min={1}
                    max={100}
                    placeholder="2"
                    value={formData.building_height_storeys || ''}
                    onChange={(e) => setFormData({ ...formData, building_height_storeys: parseInt(e.target.value) || undefined })}
                  />
                </div>

                {/* Construction type */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Construction Type
                  </label>
                  <select
                    value={formData.construction_type}
                    onChange={(e) => setFormData({ ...formData, construction_type: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 bg-white text-slate-900
                               focus:border-amber-500 focus:ring-4 focus:ring-amber-100 outline-none transition-all"
                  >
                    <option value="">Select construction type...</option>
                    <option value="combustible">Combustible</option>
                    <option value="non_combustible">Non-Combustible</option>
                    <option value="heavy_timber">Heavy Timber</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
              </div>

              <div className="mt-8 flex justify-between">
                <motion.button
                  type="button"
                  onClick={() => setStep(2)}
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-medium text-slate-600 hover:bg-slate-100 transition-colors"
                  whileHover={{ x: -2 }}
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </motion.button>
                <motion.button
                  type="button"
                  onClick={() => {
                    if (!isEditing) {
                      handleSaveDraft();
                    }
                    setStep(4);
                  }}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold
                             bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Continue
                  <ArrowRight className="w-4 h-4" />
                </motion.button>
              </div>
            </motion.div>
          )}

          {/* Step 4: Documents */}
          {step === 4 && (
            <motion.div
              key="step4"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-lg p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-slate-900">Supporting Documents</h2>
                  <p className="text-slate-500">Upload required documents for your application</p>
                </div>
              </div>

              {isEditing ? (
                <DocumentUpload
                  documents={documents}
                  documentTypes={documentTypes}
                  isUploading={uploadMutation.isPending}
                  onUpload={handleUpload}
                  onRemove={handleRemove}
                />
              ) : (
                <div className="text-center py-8">
                  <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <h3 className="font-semibold text-slate-900 mb-2">Save Draft First</h3>
                  <p className="text-slate-600 mb-4">
                    You can upload documents after saving your application as a draft.
                  </p>
                </div>
              )}

              {/* Error display */}
              {formError && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3"
                >
                  <AlertTriangle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-rose-900">Error</p>
                    <p className="text-sm text-rose-700 mt-1">{formError}</p>
                  </div>
                </motion.div>
              )}

              <div className="mt-8 flex justify-between">
                <motion.button
                  type="button"
                  onClick={() => setStep(3)}
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-medium text-slate-600 hover:bg-slate-100 transition-colors"
                  whileHover={{ x: -2 }}
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </motion.button>

                <div className="flex items-center gap-3">
                  <motion.button
                    type="button"
                    onClick={handleSaveDraft}
                    disabled={saveMutation.isPending}
                    className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-semibold
                               border-2 border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors
                               disabled:opacity-70"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {saveMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        Save Draft
                      </>
                    )}
                  </motion.button>

                  {isEditing && existingApplication?.status === 'draft' && (
                    <motion.button
                      type="button"
                      onClick={handleSubmit}
                      disabled={submitMutation.isPending || saveMutation.isPending}
                      className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold
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
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
