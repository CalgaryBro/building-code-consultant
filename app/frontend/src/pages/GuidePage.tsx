import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin,
  Building,
  Ruler,
  Users,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  FileText,
  Clock,
  DollarSign,
  Info,
  Loader2,
  Home,
  Store,
  Factory,
  Layers,
  Compass,
  FileCheck,
  AlertTriangle,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import type { GuideProjectInput, GuideResponse } from '../types';

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

      {/* Subtle diagonal lines */}
      <div
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `repeating-linear-gradient(
            45deg,
            transparent,
            transparent 100px,
            #1e3a5f 100px,
            #1e3a5f 101px
          )`,
        }}
      />

      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-64 h-64 border-l-2 border-t-2 border-slate-200/50 pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-64 h-64 border-r-2 border-b-2 border-slate-200/50 pointer-events-none" />
    </div>
  );
}

// Animated step connector
function StepConnector({ active, completed }: { active: boolean; completed: boolean }) {
  return (
    <div className="relative w-20 h-0.5 mx-2">
      <div className="absolute inset-0 bg-slate-200 rounded-full" />
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-amber-500 to-teal-500 rounded-full origin-left"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: completed ? 1 : active ? 0.5 : 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      />
    </div>
  );
}

// Step indicator component
function StepIndicator({ currentStep }: { currentStep: number }) {
  const steps = [
    { num: 1, label: 'Location', icon: MapPin },
    { num: 2, label: 'Project', icon: Building },
    { num: 3, label: 'Details', icon: Ruler },
    { num: 4, label: 'Results', icon: FileCheck },
  ];

  return (
    <div className="flex items-center justify-center">
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
                initial={false}
                animate={{
                  scale: isCurrent ? 1.1 : 1,
                }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  <Icon className="w-5 h-5" />
                )}

                {/* Pulse ring for current step */}
                {isCurrent && (
                  <motion.div
                    className="absolute inset-0 rounded-xl border-2 border-amber-400"
                    initial={{ opacity: 0.5, scale: 1 }}
                    animate={{ opacity: 0, scale: 1.3 }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
              </motion.div>

              <span className={`
                mt-2 text-xs font-medium transition-colors
                ${isCurrent ? 'text-amber-600' : isCompleted ? 'text-teal-600' : 'text-slate-400'}
              `}>
                {step.label}
              </span>
            </div>

            {index < steps.length - 1 && (
              <StepConnector
                active={currentStep === step.num + 1}
                completed={currentStep > step.num + 1 || (currentStep === step.num + 1 && index < currentStep - 2)}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

const projectTypes = [
  { id: 'new_construction', label: 'New Construction', icon: Building, description: 'Building from ground up' },
  { id: 'addition', label: 'Addition', icon: Layers, description: 'Expanding existing structure' },
  { id: 'renovation', label: 'Renovation', icon: Ruler, description: 'Interior or exterior changes' },
  { id: 'change_of_use', label: 'Change of Use', icon: Users, description: 'Different occupancy type' },
];

const occupancyTypes = [
  { id: 'residential', label: 'Residential', icon: Home, description: 'Houses, apartments, condos' },
  { id: 'commercial', label: 'Commercial', icon: Store, description: 'Offices, retail, restaurants' },
  { id: 'industrial', label: 'Industrial', icon: Factory, description: 'Warehouses, manufacturing' },
  { id: 'mixed', label: 'Mixed Use', icon: Layers, description: 'Residential + commercial' },
];

// Mock response for demonstration
const mockGuideResponse: GuideResponse = {
  project: {
    id: '1',
    project_name: 'Project at 123 Example St NW',
    address: '123 Example St NW',
    classification: 'PART_9',
    occupancy_group: 'C',
    building_height_storeys: 2,
    building_area_sqm: 250,
    project_type: 'new_construction',
    development_permit_required: true,
    building_permit_required: true,
    estimated_permit_fee: 5500,
    status: 'draft',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  classification: 'PART_9',
  classification_reason: 'Building qualifies for Part 9: ≤3 storeys, ≤600 m² footprint, residential occupancy',
  zoning_status: 'compliant',
  permits_required: [
    {
      permit_type: 'development_permit',
      required: true,
      description: 'Development Permit from City of Calgary Planning',
      estimated_fee: 2500,
      typical_timeline_days: 60,
      documents_required: ['Site plan', 'Building elevations', 'Floor plans', 'Landscaping plan'],
      notes: undefined,
    },
    {
      permit_type: 'building_permit',
      required: true,
      description: 'Building Permit from City of Calgary Building Safety',
      estimated_fee: 3000,
      typical_timeline_days: 30,
      documents_required: ['Architectural drawings', 'Structural drawings', 'HVAC design', 'Energy compliance'],
      notes: 'Part 9 building - design by qualified person acceptable',
    },
    {
      permit_type: 'electrical_permit',
      required: true,
      description: 'Electrical Permit',
      estimated_fee: 200,
      typical_timeline_days: 5,
      documents_required: ['Electrical drawings', 'Load calculations'],
      notes: undefined,
    },
  ],
  key_requirements: [
    'NBC(AE) 2023 Part 9 applies - residential and small buildings',
    'Maximum 3 storeys, 600 m² footprint',
    'Minimum ceiling height: 2.3 m (habitable rooms)',
    'Stairs: minimum 860 mm wide, maximum 200 mm rise, minimum 255 mm run',
    'Egress windows required in bedrooms',
    'Zone R-C1: Max height 10 m, 2 storeys',
  ],
  next_steps: [
    'Confirm address and verify current zoning designation',
    'Prepare preliminary site plan showing setbacks and building footprint',
    'Prepare Part 9 compliant drawings',
    'Submit Development Permit application',
    'Wait for DP approval before submitting Building Permit',
    'Submit Building Permit with complete drawing package',
  ],
  warnings: [],
};

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
  icon: React.ElementType;
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
      {/* Selection indicator */}
      <motion.div
        className={`
          absolute top-3 right-3 w-5 h-5 rounded-full border-2
          flex items-center justify-center transition-colors
          ${selected ? 'border-amber-500 bg-amber-500' : 'border-slate-300'}
        `}
        initial={false}
        animate={{ scale: selected ? 1 : 0.9 }}
      >
        {selected && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          >
            <CheckCircle2 className="w-4 h-4 text-white" />
          </motion.div>
        )}
      </motion.div>

      {/* Icon */}
      <div className={`
        w-10 h-10 rounded-lg flex items-center justify-center mb-3
        ${selected
          ? 'bg-gradient-to-br from-amber-500 to-amber-600 text-white'
          : 'bg-slate-100 text-slate-500'
        }
      `}>
        <Icon className="w-5 h-5" />
      </div>

      {/* Content */}
      <h4 className={`font-semibold mb-1 ${selected ? 'text-amber-900' : 'text-slate-900'}`}>
        {label}
      </h4>
      <p className={`text-sm ${selected ? 'text-amber-700' : 'text-slate-500'}`}>
        {description}
      </p>
    </motion.button>
  );
}

// Input field component
function FormInput({
  label,
  icon: Icon,
  hint,
  ...props
}: {
  label: string;
  icon?: React.ElementType;
  hint?: string;
} & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-2">
        {label}
      </label>
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        )}
        <input
          {...props}
          className={`
            w-full px-4 py-3 rounded-xl border-2 border-slate-200
            bg-white text-slate-900 placeholder:text-slate-400
            focus:border-amber-500 focus:ring-4 focus:ring-amber-100
            outline-none transition-all duration-200
            ${Icon ? 'pl-12' : ''}
          `}
        />
      </div>
      {hint && (
        <p className="mt-2 text-sm text-slate-500 flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5" />
          {hint}
        </p>
      )}
    </div>
  );
}

// Result card component
function ResultCard({
  title,
  icon: Icon,
  iconBg,
  children,
  delay = 0,
}: {
  title: string;
  icon: React.ElementType;
  iconBg: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconBg}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <h3 className="font-display text-lg text-slate-900">{title}</h3>
      </div>
      <div className="p-6">
        {children}
      </div>
    </motion.div>
  );
}

export function GuidePage() {
  const [step, setStep] = useState(1);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<GuideResponse | null>(null);
  const [formData, setFormData] = useState<GuideProjectInput>({
    address: '',
    project_type: '',
    occupancy_type: '',
    building_height_storeys: undefined,
    building_area_sqm: undefined,
    footprint_area_sqm: undefined,
    dwelling_units: undefined,
    description: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAnalyzing(true);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));

    setResult(mockGuideResponse);
    setIsAnalyzing(false);
    setStep(4);
  };

  const canProceed = (currentStep: number): boolean => {
    switch (currentStep) {
      case 1:
        return formData.address.length >= 5;
      case 2:
        return !!formData.project_type && !!formData.occupancy_type;
      case 3:
        return true; // Optional fields
      default:
        return false;
    }
  };

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 100 : -100,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction < 0 ? 100 : -100,
      opacity: 0,
    }),
  };

  return (
    <div className="min-h-screen">
      <BlueprintBackground />

      <div className="p-8 max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-100 text-amber-700 text-sm font-medium mb-4">
            <Compass className="w-4 h-4" />
            Permit Navigator
          </div>
          <h1 className="font-display text-4xl md:text-5xl text-slate-900 mb-3">
            What permits do you need?
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Answer a few questions about your project and we'll determine the permits,
            fees, and code requirements for your Calgary construction project.
          </p>
        </motion.div>

        {/* Step indicator */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-10"
        >
          <StepIndicator currentStep={step} />
        </motion.div>

        {/* Form steps */}
        <form onSubmit={handleSubmit}>
          <AnimatePresence mode="wait" custom={step}>
            {/* Step 1: Location */}
            {step === 1 && (
              <motion.div
                key="step1"
                custom={1}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
                className="bg-white rounded-2xl border border-slate-200 shadow-lg p-8"
              >
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center">
                    <MapPin className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="font-display text-2xl text-slate-900">
                      Project Location
                    </h2>
                    <p className="text-slate-500">We'll look up zoning and parcel information</p>
                  </div>
                </div>

                <FormInput
                  label="Calgary Address"
                  icon={MapPin}
                  placeholder="Enter street address, e.g., 123 Main St NW"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  hint="We'll automatically verify zoning designation and lot details"
                />

                <div className="mt-8 flex justify-end">
                  <motion.button
                    type="button"
                    onClick={() => setStep(2)}
                    disabled={!canProceed(1)}
                    className={`
                      inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold
                      transition-all duration-200
                      ${canProceed(1)
                        ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200 hover:shadow-xl hover:shadow-amber-200'
                        : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                      }
                    `}
                    whileHover={canProceed(1) ? { scale: 1.02 } : {}}
                    whileTap={canProceed(1) ? { scale: 0.98 } : {}}
                  >
                    Continue
                    <ArrowRight className="w-4 h-4" />
                  </motion.button>
                </div>
              </motion.div>
            )}

            {/* Step 2: Project Type */}
            {step === 2 && (
              <motion.div
                key="step2"
                custom={1}
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
                    <h2 className="font-display text-2xl text-slate-900">
                      Project Classification
                    </h2>
                    <p className="text-slate-500">What type of work are you planning?</p>
                  </div>
                </div>

                <div className="space-y-8">
                  {/* Project type */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-4">
                      Project Type
                    </label>
                    <div className="grid grid-cols-2 gap-4">
                      {projectTypes.map((type) => (
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

                  {/* Occupancy type */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-4">
                      Building Use / Occupancy
                    </label>
                    <div className="grid grid-cols-2 gap-4">
                      {occupancyTypes.map((type) => (
                        <SelectionCard
                          key={type.id}
                          selected={formData.occupancy_type === type.id}
                          onClick={() => setFormData({ ...formData, occupancy_type: type.id })}
                          icon={type.icon}
                          label={type.label}
                          description={type.description}
                        />
                      ))}
                    </div>
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
                    className={`
                      inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold
                      transition-all duration-200
                      ${canProceed(2)
                        ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200 hover:shadow-xl hover:shadow-amber-200'
                        : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                      }
                    `}
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
                custom={1}
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
                    <h2 className="font-display text-2xl text-slate-900">
                      Building Details
                    </h2>
                    <p className="text-slate-500">Optional but helps with accurate classification</p>
                  </div>
                </div>

                <div className="mt-6 p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3">
                  <Info className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-slate-600">
                    These details help determine if your project falls under <strong>Part 9</strong> (small buildings)
                    or <strong>Part 3</strong> (larger buildings) of the building code. Leave blank if unknown.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-6 mt-8">
                  <FormInput
                    label="Number of Storeys"
                    type="number"
                    min={1}
                    max={100}
                    placeholder="e.g., 2"
                    value={formData.building_height_storeys || ''}
                    onChange={(e) => setFormData({ ...formData, building_height_storeys: parseInt(e.target.value) || undefined })}
                  />
                  <FormInput
                    label="Total Floor Area (m²)"
                    type="number"
                    min={1}
                    placeholder="e.g., 250"
                    value={formData.building_area_sqm || ''}
                    onChange={(e) => setFormData({ ...formData, building_area_sqm: parseFloat(e.target.value) || undefined })}
                  />
                  <FormInput
                    label="Building Footprint (m²)"
                    type="number"
                    min={1}
                    placeholder="Ground floor area"
                    value={formData.footprint_area_sqm || ''}
                    onChange={(e) => setFormData({ ...formData, footprint_area_sqm: parseFloat(e.target.value) || undefined })}
                  />
                  <FormInput
                    label="Number of Dwelling Units"
                    type="number"
                    min={1}
                    placeholder="e.g., 1"
                    value={formData.dwelling_units || ''}
                    onChange={(e) => setFormData({ ...formData, dwelling_units: parseInt(e.target.value) || undefined })}
                  />
                </div>

                <div className="mt-6">
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Project Description (optional)
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Describe your project briefly..."
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:border-amber-500 focus:ring-4 focus:ring-amber-100 outline-none transition-all duration-200 resize-none"
                  />
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
                    type="submit"
                    disabled={isAnalyzing}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-200 hover:shadow-xl hover:shadow-amber-200 transition-all duration-200 disabled:opacity-70"
                    whileHover={!isAnalyzing ? { scale: 1.02 } : {}}
                    whileTap={!isAnalyzing ? { scale: 0.98 } : {}}
                  >
                    {isAnalyzing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analyzing Project...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        Get Permit Requirements
                      </>
                    )}
                  </motion.button>
                </div>
              </motion.div>
            )}

            {/* Step 4: Results */}
            {step === 4 && result && (
              <motion.div
                key="step4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                {/* Classification badge */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`
                    p-6 rounded-2xl border-2
                    ${result.classification === 'PART_9'
                      ? 'bg-gradient-to-br from-teal-50 to-emerald-50 border-teal-200'
                      : 'bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200'
                    }
                  `}
                >
                  <div className="flex items-start gap-4">
                    <div className={`
                      w-14 h-14 rounded-xl flex items-center justify-center
                      ${result.classification === 'PART_9'
                        ? 'bg-gradient-to-br from-teal-500 to-teal-600'
                        : 'bg-gradient-to-br from-amber-500 to-amber-600'
                      }
                    `}>
                      <Building className="w-7 h-7 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h3 className="font-display text-2xl text-slate-900">
                          {result.classification === 'PART_9' ? 'Part 9 Building' : 'Part 3 Building'}
                        </h3>
                        <span className={`
                          inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold
                          ${result.classification === 'PART_9'
                            ? 'bg-teal-500 text-white'
                            : 'bg-amber-500 text-white'
                          }
                        `}>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {result.classification}
                        </span>
                      </div>
                      <p className="text-slate-600 mt-2">{result.classification_reason}</p>
                    </div>
                  </div>
                </motion.div>

                {/* Permits required */}
                <ResultCard
                  title="Permits Required"
                  icon={FileText}
                  iconBg="bg-gradient-to-br from-blue-500 to-blue-600"
                  delay={0.1}
                >
                  <div className="space-y-4">
                    {result.permits_required.filter(p => p.required).map((permit, index) => (
                      <motion.div
                        key={permit.permit_type}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 + index * 0.1 }}
                        className="p-4 bg-slate-50 rounded-xl border border-slate-100 hover:border-slate-200 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-start gap-3 flex-1">
                            <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center flex-shrink-0">
                              <FileCheck className="w-4 h-4 text-slate-500" />
                            </div>
                            <div>
                              <h4 className="font-semibold text-slate-900">{permit.description}</h4>
                              {permit.notes && (
                                <p className="text-sm text-slate-500 mt-1">{permit.notes}</p>
                              )}
                            </div>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <div className="flex items-center gap-1.5 text-sm font-semibold text-slate-900">
                              <DollarSign className="w-4 h-4 text-amber-500" />
                              ~${permit.estimated_fee?.toLocaleString()}
                            </div>
                            <div className="flex items-center gap-1.5 text-sm text-slate-500 mt-1">
                              <Clock className="w-3.5 h-3.5" />
                              ~{permit.typical_timeline_days} days
                            </div>
                          </div>
                        </div>
                        {permit.documents_required.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-slate-200">
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                              Required Documents
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {permit.documents_required.map((doc) => (
                                <span
                                  key={doc}
                                  className="inline-flex items-center gap-1 text-xs bg-white px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600"
                                >
                                  <ChevronRight className="w-3 h-3 text-slate-400" />
                                  {doc}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>

                  {/* Total fees */}
                  <div className="mt-6 pt-6 border-t border-slate-200 flex justify-between items-center">
                    <span className="text-slate-600 font-medium">Estimated Total Permit Fees</span>
                    <div className="flex items-center gap-2">
                      <span className="font-display text-3xl text-slate-900">
                        ${result.project.estimated_permit_fee?.toLocaleString()}
                      </span>
                      <span className="text-slate-400 text-sm">CAD</span>
                    </div>
                  </div>
                </ResultCard>

                {/* Key requirements */}
                <ResultCard
                  title="Key Code Requirements"
                  icon={AlertTriangle}
                  iconBg="bg-gradient-to-br from-amber-500 to-amber-600"
                  delay={0.2}
                >
                  <ul className="space-y-3">
                    {result.key_requirements.map((req, index) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 + index * 0.05 }}
                        className="flex items-start gap-3 text-slate-700"
                      >
                        <div className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <Info className="w-3 h-3 text-amber-600" />
                        </div>
                        <span>{req}</span>
                      </motion.li>
                    ))}
                  </ul>
                </ResultCard>

                {/* Next steps */}
                <ResultCard
                  title="Recommended Next Steps"
                  icon={ArrowRight}
                  iconBg="bg-gradient-to-br from-teal-500 to-teal-600"
                  delay={0.3}
                >
                  <ol className="space-y-3">
                    {result.next_steps.map((nextStep, index) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 + index * 0.05 }}
                        className="flex items-start gap-3"
                      >
                        <span className="w-6 h-6 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                          {index + 1}
                        </span>
                        <span className="text-slate-700 pt-0.5">{nextStep.replace(/^\d+\.\s*/, '')}</span>
                      </motion.li>
                    ))}
                  </ol>
                </ResultCard>

                {/* Actions */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="flex flex-wrap gap-4 pt-4"
                >
                  <motion.button
                    type="button"
                    onClick={() => {
                      setStep(1);
                      setResult(null);
                      setFormData({
                        address: '',
                        project_type: '',
                        occupancy_type: '',
                      });
                    }}
                    className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-semibold border-2 border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <ArrowLeft className="w-4 h-4" />
                    Start New Project
                  </motion.button>
                  <motion.button
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-lg shadow-teal-200 hover:shadow-xl hover:shadow-teal-200 transition-all duration-200"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Continue to Review Mode
                    <ArrowRight className="w-4 h-4" />
                  </motion.button>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </form>
      </div>
    </div>
  );
}
