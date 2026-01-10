import { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';

// ============================================================================
// TYPES
// ============================================================================

interface IDFCoefficients {
  [key: string]: { a: number; b: number; c: number };
}

interface CatchmentInput {
  catchment_id: string;
  area_ha: number;
  land_use: string;
  runoff_c?: number;
  flow_path_length_m?: number;
  average_slope_percent?: number;
  time_of_concentration_min?: number;
  tc_method: string;
}

interface SanitaryLoadInput {
  load_id: string;
  land_use: string;
  area_ha: number;
  dwelling_units?: number;
  population?: number;
  employees?: number;
}

interface WaterLoadInput {
  load_id: string;
  land_use: string;
  area_ha: number;
  dwelling_units?: number;
  population?: number;
}

interface PipeDesignResult {
  pipe_id: string;
  diameter_mm: number;
  slope_percent: number;
  material: string;
  manning_n: number;
  design_flow_ls: number;
  full_flow_capacity_ls: number;
  velocity_ms: number;
  capacity_utilization_percent: number;
  is_capacity_adequate: boolean;
  is_velocity_adequate: boolean;
  notes: string[];
}

interface SanitaryPipeResult extends PipeDesignResult {
  min_flow_velocity_ms: number;
  is_self_cleansing: boolean;
}

interface WaterServiceResult {
  service_id: string;
  service_type: string;
  diameter_mm: number;
  material: string;
  hazen_williams_c: number;
  design_flow_ls: number;
  velocity_ms: number;
  head_loss_m: number;
  available_pressure_kpa: number;
  residual_pressure_kpa: number;
  is_pressure_adequate: boolean;
  is_velocity_adequate: boolean;
  is_fire_flow_adequate: boolean;
  notes: string[];
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

const API_BASE = '/api/v1/dssp';
const PRESETS_BASE = '/api/v1/presets';
const REPORTS_BASE = '/api/v1/reports';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function fetchHtml(url: string, options?: RequestInit): Promise<string> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.text();
}

interface PresetScenario {
  key: string;
  name: string;
  description: string;
  type: string;
}

interface StormwaterScenarioDetail {
  name: string;
  description: string;
  scenario_type: string;
  return_period_years: number;
  catchments: Array<{
    catchment_id: string;
    area_ha: number;
    land_use: string;
    runoff_c: number;
    tc_method?: string;
    flow_path_length_m?: number;
    average_slope_percent?: number;
  }>;
  design_notes: string;
  applicable_standards: string[];
}

interface SanitaryScenarioDetail {
  name: string;
  description: string;
  scenario_type: string;
  loads: Array<{
    load_id: string;
    land_use: string;
    area_ha: number;
    dwelling_units?: number;
    population?: number;
  }>;
  infiltration_rate_ls_ha: number;
  peaking_method: string;
  design_notes: string;
  applicable_standards: string[];
}

interface WaterScenarioDetail {
  name: string;
  description: string;
  building_type: string;
  dwelling_units: number;
  occupants_per_unit: number;
  service_length_m: number;
  fire_flow_required: boolean;
  min_pressure_kpa: number;
  design_notes: string;
  applicable_standards: string[];
}

const dsspApi = {
  getIDFCoefficients: () => fetchJson<{
    location: string;
    equation: string;
    return_periods: number[];
    coefficients: IDFCoefficients;
  }>(`${API_BASE}/idf/coefficients`),

  getIDFTable: () => fetchJson<{
    location: string;
    return_periods: number[];
    durations_min: number[];
    intensities: { [key: string]: { [key: string]: number } };
  }>(`${API_BASE}/idf/table`),

  getStandards: () => fetchJson<{
    stormwater: Record<string, number>;
    sanitary: Record<string, number>;
    water: Record<string, number>;
  }>(`${API_BASE}/standards/calgary`),

  getRunoffCoefficients: () => fetchJson<Record<string, { c: number; min: number; max: number }>>(`${API_BASE}/standards/runoff-coefficients`),

  designStormPipe: (data: {
    pipe_id: string;
    catchments: CatchmentInput[];
    slope_percent?: number;
    return_period_years: number;
    material: string;
    min_diameter_mm: number;
  }) => fetchJson<PipeDesignResult>(`${API_BASE}/stormwater/design-pipe`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  designSanitaryPipe: (data: {
    pipe_id: string;
    loads: SanitaryLoadInput[];
    slope_percent?: number;
    material: string;
    min_diameter_mm: number;
  }) => fetchJson<SanitaryPipeResult>(`${API_BASE}/sanitary/design-pipe`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  designWaterService: (data: {
    service_id: string;
    loads: WaterLoadInput[];
    length_m: number;
    available_pressure_kpa: number;
    elevation_change_m: number;
    material: string;
  }) => fetchJson<WaterServiceResult>(`${API_BASE}/water/design-service`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};

// Presets API
const presetsApi = {
  listStormwaterScenarios: () => fetchJson<PresetScenario[]>(`${PRESETS_BASE}/dssp/stormwater/scenarios`),
  getStormwaterScenario: (key: string) => fetchJson<StormwaterScenarioDetail>(`${PRESETS_BASE}/dssp/stormwater/scenarios/${key}`),
  listSanitaryScenarios: () => fetchJson<PresetScenario[]>(`${PRESETS_BASE}/dssp/sanitary/scenarios`),
  getSanitaryScenario: (key: string) => fetchJson<SanitaryScenarioDetail>(`${PRESETS_BASE}/dssp/sanitary/scenarios/${key}`),
  listWaterScenarios: () => fetchJson<PresetScenario[]>(`${PRESETS_BASE}/dssp/water/scenarios`),
  getWaterScenario: (key: string) => fetchJson<WaterScenarioDetail>(`${PRESETS_BASE}/dssp/water/scenarios/${key}`),
};

// Reports API
const reportsApi = {
  generateStormwaterReportHtml: (data: {
    project_name?: string;
    catchments: Array<{
      catchment_id: string;
      area_ha: number;
      land_use: string;
      runoff_c: number;
      tc_min: number;
    }>;
    return_period_years: number;
  }) => fetchHtml(`${REPORTS_BASE}/dssp/stormwater/rational/html`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  generateSanitaryReportHtml: (data: {
    project_name?: string;
    loads: Array<{
      load_id: string;
      land_use: string;
      area_ha: number;
      population?: number;
      dwelling_units?: number;
    }>;
    infiltration_rate_ls_ha?: number;
    peaking_method?: string;
  }) => fetchHtml(`${REPORTS_BASE}/dssp/sanitary/flow/html`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  generateWaterReportHtml: (data: {
    project_name?: string;
    building_type: string;
    dwelling_units: number;
    occupants_per_unit?: number;
    service_length_m?: number;
    min_pressure_kpa?: number;
  }) => fetchHtml(`${REPORTS_BASE}/dssp/water/demand/html`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};

// ============================================================================
// LAND USE OPTIONS
// ============================================================================

const LAND_USE_OPTIONS = [
  { value: 'single_family', label: 'Single Family Residential', category: 'Residential' },
  { value: 'multi_family', label: 'Multi-Family Residential', category: 'Residential' },
  { value: 'townhouse', label: 'Townhouse', category: 'Residential' },
  { value: 'commercial_small', label: 'Commercial - Small', category: 'Commercial' },
  { value: 'commercial_medium', label: 'Commercial - Medium', category: 'Commercial' },
  { value: 'commercial_large', label: 'Commercial - Large', category: 'Commercial' },
  { value: 'industrial_light', label: 'Industrial - Light', category: 'Industrial' },
  { value: 'industrial_heavy', label: 'Industrial - Heavy', category: 'Industrial' },
  { value: 'institutional', label: 'Institutional', category: 'Other' },
  { value: 'parks', label: 'Parks & Open Space', category: 'Other' },
];

const PIPE_MATERIALS = [
  { value: 'pvc', label: 'PVC', manning_n: 0.011 },
  { value: 'hdpe', label: 'HDPE', manning_n: 0.011 },
  { value: 'concrete', label: 'Concrete', manning_n: 0.013 },
  { value: 'ductile_iron', label: 'Ductile Iron', manning_n: 0.012 },
];

const RETURN_PERIODS = [2, 5, 10, 25, 50, 100];

// ============================================================================
// COMPONENTS
// ============================================================================

// Capacity Gauge Component
function CapacityGauge({ value, max = 100, label, status }: {
  value: number;
  max?: number;
  label: string;
  status: 'pass' | 'fail' | 'warning';
}) {
  const percentage = Math.min((value / max) * 100, 100);
  const angle = (percentage / 100) * 180 - 90;

  const colors = {
    pass: { ring: '#0d9488', glow: 'rgba(13, 148, 136, 0.4)' },
    warning: { ring: '#f59e0b', glow: 'rgba(245, 158, 11, 0.4)' },
    fail: { ring: '#ef4444', glow: 'rgba(239, 68, 68, 0.4)' },
  };

  return (
    <div className="relative flex flex-col items-center">
      <svg width="120" height="70" viewBox="0 0 120 70" className="overflow-visible">
        {/* Background arc */}
        <path
          d="M 10 60 A 50 50 0 0 1 110 60"
          fill="none"
          stroke="#1e293b"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d="M 10 60 A 50 50 0 0 1 110 60"
          fill="none"
          stroke={colors[status].ring}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${percentage * 1.57} 157`}
          style={{
            filter: `drop-shadow(0 0 6px ${colors[status].glow})`,
          }}
        />
        {/* Needle */}
        <g transform={`rotate(${angle}, 60, 60)`}>
          <line
            x1="60"
            y1="60"
            x2="60"
            y2="20"
            stroke="#e2e8f0"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <circle cx="60" cy="60" r="4" fill="#e2e8f0" />
        </g>
        {/* Scale marks */}
        {[0, 25, 50, 75, 100].map((mark) => {
          const markAngle = ((mark / 100) * 180 - 90) * (Math.PI / 180);
          const x1 = 60 + 42 * Math.cos(markAngle);
          const y1 = 60 + 42 * Math.sin(markAngle);
          const x2 = 60 + 48 * Math.cos(markAngle);
          const y2 = 60 + 48 * Math.sin(markAngle);
          return (
            <line
              key={mark}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#475569"
              strokeWidth="1"
            />
          );
        })}
      </svg>
      <div className="text-center -mt-1">
        <div className="font-mono text-xl font-bold text-slate-100">{value.toFixed(1)}%</div>
        <div className="text-xs text-slate-400 uppercase tracking-wider">{label}</div>
      </div>
    </div>
  );
}

// Status Badge Component
function StatusBadge({ pass, label }: { pass: boolean; label: string }) {
  return (
    <div className={`
      inline-flex items-center gap-1.5 px-2.5 py-1 rounded
      font-mono text-xs uppercase tracking-wider
      ${pass
        ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
        : 'bg-red-500/20 text-red-400 border border-red-500/30'
      }
    `}>
      <span className={`w-1.5 h-1.5 rounded-full ${pass ? 'bg-teal-400' : 'bg-red-400'}`} />
      {label}: {pass ? 'PASS' : 'FAIL'}
    </div>
  );
}

// Input Field Component
function InputField({ label, unit, value, onChange, type = 'number', min, max, step, required, placeholder }: {
  label: string;
  unit?: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: 'text' | 'number';
  min?: number;
  max?: number;
  step?: number;
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>
      <div className="relative">
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          min={min}
          max={max}
          step={step}
          placeholder={placeholder}
          className={`
            w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50
            rounded text-slate-100 font-mono text-sm
            placeholder:text-slate-500
            focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30
            ${unit ? 'pr-12' : ''}
          `}
        />
        {unit && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 font-mono">
            {unit}
          </span>
        )}
      </div>
    </div>
  );
}

// Select Field Component
function SelectField({ label, value, onChange, options, required }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string; category?: string }[];
  required?: boolean;
}) {
  // Group options by category
  const groupedOptions = options.reduce((acc, opt) => {
    const cat = opt.category || 'Options';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(opt);
    return acc;
  }, {} as Record<string, typeof options>);

  return (
    <div className="space-y-1">
      <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="
          w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50
          rounded text-slate-100 font-mono text-sm
          focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30
          cursor-pointer
        "
      >
        <option value="">Select...</option>
        {Object.entries(groupedOptions).map(([category, opts]) => (
          <optgroup key={category} label={category}>
            {opts.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </div>
  );
}

// Tab Button Component
function TabButton({ active, onClick, children, icon }: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  icon: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-5 py-3 font-medium text-sm
        border-b-2 transition-all duration-200
        ${active
          ? 'border-cyan-400 text-cyan-400 bg-cyan-500/5'
          : 'border-transparent text-slate-400 hover:text-slate-300 hover:bg-slate-800/50'
        }
      `}
    >
      {icon}
      {children}
    </button>
  );
}

// IDF Table Component
function IDFTable({ data }: {
  data: {
    return_periods: number[];
    durations_min: number[];
    intensities: { [key: string]: { [key: string]: number } };
  } | undefined;
}) {
  if (!data) return null;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="px-2 py-2 text-left text-slate-400">Duration</th>
            {data.return_periods.map((rp) => (
              <th key={rp} className="px-2 py-2 text-right text-cyan-400">
                {rp}yr
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.durations_min.slice(0, 8).map((dur) => (
            <tr key={dur} className="border-b border-slate-800/50 hover:bg-slate-800/30">
              <td className="px-2 py-1.5 text-slate-300">{dur} min</td>
              {data.return_periods.map((rp) => (
                <td key={rp} className="px-2 py-1.5 text-right text-slate-400">
                  {data.intensities[String(rp)]?.[String(dur)]?.toFixed(1) || '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Results Card Component
function ResultsCard({ title, children, status }: {
  title: string;
  children: React.ReactNode;
  status?: 'pass' | 'fail' | 'warning';
}) {
  const borderColor = status === 'pass' ? 'border-teal-500/30' : status === 'fail' ? 'border-red-500/30' : 'border-slate-700';

  return (
    <div className={`bg-slate-800/30 border ${borderColor} rounded-lg p-4`}>
      <h4 className="text-sm font-medium text-slate-300 mb-3 uppercase tracking-wider">{title}</h4>
      {children}
    </div>
  );
}

// Preset Selector Component
function PresetSelector({
  scenarios,
  isLoading,
  onSelect,
  selectedKey,
}: {
  scenarios: PresetScenario[] | undefined;
  isLoading: boolean;
  onSelect: (key: string) => void;
  selectedKey: string;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        Loading presets...
      </div>
    );
  }

  if (!scenarios || scenarios.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center gap-2">
      <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
      </svg>
      <select
        value={selectedKey}
        onChange={(e) => onSelect(e.target.value)}
        className="
          text-xs px-2 py-1 bg-slate-800/70 border border-amber-500/30
          rounded text-amber-300 font-medium
          focus:outline-none focus:border-amber-400/50 cursor-pointer
          hover:bg-slate-800
        "
      >
        <option value="">Load Preset Scenario...</option>
        {scenarios.map((s) => (
          <option key={s.key} value={s.key}>
            {s.name}
          </option>
        ))}
      </select>
    </div>
  );
}

// Export Report Button Component
function ExportReportButton({
  onClick,
  isExporting,
  label = 'Export Report',
}: {
  onClick: () => void;
  isExporting: boolean;
  label?: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={isExporting}
      className="
        flex items-center gap-1.5 text-xs px-3 py-1.5
        bg-emerald-500/10 border border-emerald-500/30 rounded
        text-emerald-400 hover:bg-emerald-500/20 hover:border-emerald-500/50
        transition-colors disabled:opacity-50 disabled:cursor-not-allowed
      "
    >
      {isExporting ? (
        <>
          <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Generating...
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}

// Helper to download HTML report
function downloadHtmlReport(html: string, filename: string) {
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ============================================================================
// MAIN TABS
// ============================================================================

// Stormwater Tab
function StormwaterTab() {
  const [pipeId, setPipeId] = useState('ST-1');
  const [projectName, setProjectName] = useState('');
  const [catchments, setCatchments] = useState<CatchmentInput[]>([{
    catchment_id: 'C1',
    area_ha: 2.5,
    land_use: 'single_family',
    tc_method: 'airport',
    flow_path_length_m: 200,
    average_slope_percent: 2,
  }]);
  const [slopePct, setSlopePct] = useState<string>('');
  const [returnPeriod, setReturnPeriod] = useState(5);
  const [material, setMaterial] = useState('pvc');
  const [minDiameter, setMinDiameter] = useState(300);
  const [result, setResult] = useState<PipeDesignResult | null>(null);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  // Fetch available presets
  const { data: presets, isLoading: presetsLoading } = useQuery({
    queryKey: ['stormwater-presets'],
    queryFn: presetsApi.listStormwaterScenarios,
  });

  const { mutate: calculate, isPending } = useMutation({
    mutationFn: dsspApi.designStormPipe,
    onSuccess: setResult,
  });

  // Load preset scenario
  const handleLoadPreset = useCallback(async (key: string) => {
    if (!key) return;
    setSelectedPreset(key);
    try {
      const scenario = await presetsApi.getStormwaterScenario(key);
      setProjectName(scenario.name);
      setReturnPeriod(scenario.return_period_years);
      setCatchments(scenario.catchments.map((c, i) => ({
        catchment_id: c.catchment_id || `C${i + 1}`,
        area_ha: c.area_ha,
        land_use: c.land_use,
        runoff_c: c.runoff_c,
        tc_method: c.tc_method || 'airport',
        flow_path_length_m: c.flow_path_length_m,
        average_slope_percent: c.average_slope_percent,
      })));
    } catch (err) {
      console.error('Failed to load preset:', err);
    }
  }, []);

  // Export report
  const handleExportReport = useCallback(async () => {
    if (!result) return;
    setIsExporting(true);
    try {
      const html = await reportsApi.generateStormwaterReportHtml({
        project_name: projectName || 'Stormwater Calculation',
        catchments: catchments.map((c) => ({
          catchment_id: c.catchment_id,
          area_ha: c.area_ha,
          land_use: c.land_use,
          runoff_c: c.runoff_c || 0.5,
          tc_min: c.time_of_concentration_min || 10,
        })),
        return_period_years: returnPeriod,
      });
      downloadHtmlReport(html, `stormwater-report-${Date.now()}.html`);
    } catch (err) {
      console.error('Failed to export report:', err);
    } finally {
      setIsExporting(false);
    }
  }, [result, projectName, catchments, returnPeriod]);

  const handleCalculate = () => {
    calculate({
      pipe_id: pipeId,
      catchments,
      slope_percent: slopePct ? parseFloat(slopePct) : undefined,
      return_period_years: returnPeriod,
      material,
      min_diameter_mm: minDiameter,
    });
  };

  const updateCatchment = (index: number, field: keyof CatchmentInput, value: string | number) => {
    const updated = [...catchments];
    updated[index] = { ...updated[index], [field]: value };
    setCatchments(updated);
  };

  const addCatchment = () => {
    setCatchments([...catchments, {
      catchment_id: `C${catchments.length + 1}`,
      area_ha: 1,
      land_use: 'single_family',
      tc_method: 'airport',
    }]);
  };

  const removeCatchment = (index: number) => {
    if (catchments.length > 1) {
      setCatchments(catchments.filter((_, i) => i !== index));
    }
  };

  const overallStatus = result
    ? (result.is_capacity_adequate && result.is_velocity_adequate ? 'pass' : 'fail')
    : undefined;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Section */}
      <div className="space-y-4">
        {/* Preset Selector */}
        <div className="flex items-center justify-between">
          <PresetSelector
            scenarios={presets}
            isLoading={presetsLoading}
            selectedKey={selectedPreset}
            onSelect={handleLoadPreset}
          />
          {result && (
            <ExportReportButton
              onClick={handleExportReport}
              isExporting={isExporting}
              label="Export Report"
            />
          )}
        </div>

        {/* Project Name */}
        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <InputField
            label="Project Name"
            value={projectName}
            onChange={setProjectName}
            type="text"
            placeholder="Enter project name for report..."
          />
        </div>

        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider">
              Catchment Areas
            </h3>
            <button
              onClick={addCatchment}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Catchment
            </button>
          </div>

          <div className="space-y-4">
            {catchments.map((catchment, index) => (
              <div key={index} className="bg-slate-900/50 rounded p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-cyan-400">
                    CATCHMENT {catchment.catchment_id}
                  </span>
                  {catchments.length > 1 && (
                    <button
                      onClick={() => removeCatchment(index)}
                      className="text-slate-500 hover:text-red-400 text-xs"
                    >
                      Remove
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <InputField
                    label="Area"
                    unit="ha"
                    value={catchment.area_ha}
                    onChange={(v) => updateCatchment(index, 'area_ha', parseFloat(v) || 0)}
                    min={0.01}
                    step={0.1}
                    required
                  />
                  <SelectField
                    label="Land Use"
                    value={catchment.land_use}
                    onChange={(v) => updateCatchment(index, 'land_use', v)}
                    options={LAND_USE_OPTIONS}
                    required
                  />
                  <InputField
                    label="Flow Path"
                    unit="m"
                    value={catchment.flow_path_length_m || ''}
                    onChange={(v) => updateCatchment(index, 'flow_path_length_m', parseFloat(v) || 0)}
                  />
                  <InputField
                    label="Slope"
                    unit="%"
                    value={catchment.average_slope_percent || ''}
                    onChange={(v) => updateCatchment(index, 'average_slope_percent', parseFloat(v) || 0)}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider mb-4">
            Pipe Parameters
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <InputField
              label="Pipe ID"
              value={pipeId}
              onChange={setPipeId}
              type="text"
              required
            />
            <SelectField
              label="Return Period"
              value={String(returnPeriod)}
              onChange={(v) => setReturnPeriod(parseInt(v))}
              options={RETURN_PERIODS.map((rp) => ({ value: String(rp), label: `${rp} years` }))}
              required
            />
            <SelectField
              label="Material"
              value={material}
              onChange={setMaterial}
              options={PIPE_MATERIALS.map((m) => ({ value: m.value, label: m.label }))}
              required
            />
            <InputField
              label="Pipe Slope"
              unit="%"
              value={slopePct}
              onChange={setSlopePct}
              placeholder="Auto"
            />
            <InputField
              label="Min Diameter"
              unit="mm"
              value={minDiameter}
              onChange={(v) => setMinDiameter(parseInt(v) || 300)}
              min={150}
              step={50}
            />
          </div>
        </div>

        <button
          onClick={handleCalculate}
          disabled={isPending}
          className="
            w-full py-3 px-4 bg-cyan-600 hover:bg-cyan-500
            text-white font-medium rounded
            transition-colors duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center justify-center gap-2
          "
        >
          {isPending ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Calculating...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              Calculate Design
            </>
          )}
        </button>
      </div>

      {/* Results Section */}
      <div className="space-y-4">
        {result ? (
          <>
            <ResultsCard title="Design Summary" status={overallStatus}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-3xl font-mono font-bold text-slate-100">
                    {result.diameter_mm} <span className="text-lg text-slate-400">mm</span>
                  </div>
                  <div className="text-xs text-slate-500 uppercase">Pipe Diameter</div>
                </div>
                <CapacityGauge
                  value={result.capacity_utilization_percent}
                  label="Capacity"
                  status={result.capacity_utilization_percent <= 80 ? 'pass' : 'fail'}
                />
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Design Flow</span>
                  <div className="font-mono text-slate-200">{result.design_flow_ls.toFixed(2)} L/s</div>
                </div>
                <div>
                  <span className="text-slate-500">Full Capacity</span>
                  <div className="font-mono text-slate-200">{result.full_flow_capacity_ls.toFixed(2)} L/s</div>
                </div>
                <div>
                  <span className="text-slate-500">Velocity</span>
                  <div className="font-mono text-slate-200">{result.velocity_ms.toFixed(2)} m/s</div>
                </div>
                <div>
                  <span className="text-slate-500">Slope</span>
                  <div className="font-mono text-slate-200">{result.slope_percent.toFixed(3)}%</div>
                </div>
              </div>
            </ResultsCard>

            <ResultsCard title="Design Checks">
              <div className="flex flex-wrap gap-2">
                <StatusBadge pass={result.is_capacity_adequate} label="Capacity" />
                <StatusBadge pass={result.is_velocity_adequate} label="Velocity" />
              </div>
              {result.notes.length > 0 && (
                <div className="mt-3 space-y-1">
                  {result.notes.map((note, i) => (
                    <p key={i} className="text-xs text-amber-400 flex items-start gap-1">
                      <svg className="w-3 h-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      {note}
                    </p>
                  ))}
                </div>
              )}
            </ResultsCard>

            <ResultsCard title="Pipe Specification">
              <div className="font-mono text-xs space-y-1 text-slate-400">
                <p>Pipe ID: <span className="text-cyan-400">{result.pipe_id}</span></p>
                <p>Material: <span className="text-slate-300">{result.material.toUpperCase()}</span></p>
                <p>Manning's n: <span className="text-slate-300">{result.manning_n}</span></p>
                <p>Diameter: <span className="text-slate-300">{result.diameter_mm} mm</span></p>
                <p>Slope: <span className="text-slate-300">{result.slope_percent.toFixed(4)}%</span></p>
              </div>
            </ResultsCard>
          </>
        ) : (
          <div className="bg-slate-800/30 border border-slate-700 border-dashed rounded-lg p-8 text-center">
            <svg className="w-12 h-12 mx-auto text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-slate-500 text-sm">Configure parameters and click Calculate to see results</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Sanitary Tab
function SanitaryTab() {
  const [pipeId, setPipeId] = useState('SAN-1');
  const [projectName, setProjectName] = useState('');
  const [loads, setLoads] = useState<SanitaryLoadInput[]>([{
    load_id: 'L1',
    land_use: 'single_family',
    area_ha: 2.5,
    dwelling_units: 60,
  }]);
  const [slopePct, setSlopePct] = useState<string>('');
  const [material, setMaterial] = useState('pvc');
  const [minDiameter, setMinDiameter] = useState(200);
  const [result, setResult] = useState<SanitaryPipeResult | null>(null);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  // Fetch available presets
  const { data: presets, isLoading: presetsLoading } = useQuery({
    queryKey: ['sanitary-presets'],
    queryFn: presetsApi.listSanitaryScenarios,
  });

  const { mutate: calculate, isPending } = useMutation({
    mutationFn: dsspApi.designSanitaryPipe,
    onSuccess: setResult,
  });

  // Load preset scenario
  const handleLoadPreset = useCallback(async (key: string) => {
    if (!key) return;
    setSelectedPreset(key);
    try {
      const scenario = await presetsApi.getSanitaryScenario(key);
      setProjectName(scenario.name);
      setLoads(scenario.loads.map((l, i) => ({
        load_id: l.load_id || `L${i + 1}`,
        land_use: l.land_use,
        area_ha: l.area_ha,
        dwelling_units: l.dwelling_units,
        population: l.population,
      })));
    } catch (err) {
      console.error('Failed to load preset:', err);
    }
  }, []);

  // Export report
  const handleExportReport = useCallback(async () => {
    if (!result) return;
    setIsExporting(true);
    try {
      const html = await reportsApi.generateSanitaryReportHtml({
        project_name: projectName || 'Sanitary Calculation',
        loads: loads.map((l) => ({
          load_id: l.load_id,
          land_use: l.land_use,
          area_ha: l.area_ha,
          population: l.population,
          dwelling_units: l.dwelling_units,
        })),
      });
      downloadHtmlReport(html, `sanitary-report-${Date.now()}.html`);
    } catch (err) {
      console.error('Failed to export report:', err);
    } finally {
      setIsExporting(false);
    }
  }, [result, projectName, loads]);

  const handleCalculate = () => {
    calculate({
      pipe_id: pipeId,
      loads,
      slope_percent: slopePct ? parseFloat(slopePct) : undefined,
      material,
      min_diameter_mm: minDiameter,
    });
  };

  const updateLoad = (index: number, field: keyof SanitaryLoadInput, value: string | number) => {
    const updated = [...loads];
    updated[index] = { ...updated[index], [field]: value };
    setLoads(updated);
  };

  const addLoad = () => {
    setLoads([...loads, {
      load_id: `L${loads.length + 1}`,
      land_use: 'single_family',
      area_ha: 1,
    }]);
  };

  const removeLoad = (index: number) => {
    if (loads.length > 1) {
      setLoads(loads.filter((_, i) => i !== index));
    }
  };

  const overallStatus = result
    ? (result.is_capacity_adequate && result.is_velocity_adequate && result.is_self_cleansing ? 'pass' : 'fail')
    : undefined;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Section */}
      <div className="space-y-4">
        {/* Preset Selector */}
        <div className="flex items-center justify-between">
          <PresetSelector
            scenarios={presets}
            isLoading={presetsLoading}
            selectedKey={selectedPreset}
            onSelect={handleLoadPreset}
          />
          {result && (
            <ExportReportButton
              onClick={handleExportReport}
              isExporting={isExporting}
              label="Export Report"
            />
          )}
        </div>

        {/* Project Name */}
        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <InputField
            label="Project Name"
            value={projectName}
            onChange={setProjectName}
            type="text"
            placeholder="Enter project name for report..."
          />
        </div>

        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider">
              Tributary Loads
            </h3>
            <button
              onClick={addLoad}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Load
            </button>
          </div>

          <div className="space-y-4">
            {loads.map((load, index) => (
              <div key={index} className="bg-slate-900/50 rounded p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-cyan-400">
                    LOAD {load.load_id}
                  </span>
                  {loads.length > 1 && (
                    <button
                      onClick={() => removeLoad(index)}
                      className="text-slate-500 hover:text-red-400 text-xs"
                    >
                      Remove
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <InputField
                    label="Area"
                    unit="ha"
                    value={load.area_ha}
                    onChange={(v) => updateLoad(index, 'area_ha', parseFloat(v) || 0)}
                    min={0.01}
                    step={0.1}
                    required
                  />
                  <SelectField
                    label="Land Use"
                    value={load.land_use}
                    onChange={(v) => updateLoad(index, 'land_use', v)}
                    options={LAND_USE_OPTIONS}
                    required
                  />
                  <InputField
                    label="Dwelling Units"
                    value={load.dwelling_units || ''}
                    onChange={(v) => updateLoad(index, 'dwelling_units', parseInt(v) || 0)}
                  />
                  <InputField
                    label="Population"
                    value={load.population || ''}
                    onChange={(v) => updateLoad(index, 'population', parseInt(v) || 0)}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider mb-4">
            Pipe Parameters
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <InputField
              label="Pipe ID"
              value={pipeId}
              onChange={setPipeId}
              type="text"
              required
            />
            <SelectField
              label="Material"
              value={material}
              onChange={setMaterial}
              options={PIPE_MATERIALS.map((m) => ({ value: m.value, label: m.label }))}
              required
            />
            <InputField
              label="Pipe Slope"
              unit="%"
              value={slopePct}
              onChange={setSlopePct}
              placeholder="Auto"
            />
            <InputField
              label="Min Diameter"
              unit="mm"
              value={minDiameter}
              onChange={(v) => setMinDiameter(parseInt(v) || 200)}
              min={100}
              step={50}
            />
          </div>
        </div>

        <button
          onClick={handleCalculate}
          disabled={isPending}
          className="
            w-full py-3 px-4 bg-cyan-600 hover:bg-cyan-500
            text-white font-medium rounded
            transition-colors duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center justify-center gap-2
          "
        >
          {isPending ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Calculating...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              Calculate Design
            </>
          )}
        </button>
      </div>

      {/* Results Section */}
      <div className="space-y-4">
        {result ? (
          <>
            <ResultsCard title="Design Summary" status={overallStatus}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-3xl font-mono font-bold text-slate-100">
                    {result.diameter_mm} <span className="text-lg text-slate-400">mm</span>
                  </div>
                  <div className="text-xs text-slate-500 uppercase">Pipe Diameter</div>
                </div>
                <CapacityGauge
                  value={result.capacity_utilization_percent}
                  label="Capacity"
                  status={result.capacity_utilization_percent <= 75 ? 'pass' : 'fail'}
                />
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Design Flow</span>
                  <div className="font-mono text-slate-200">{result.design_flow_ls.toFixed(2)} L/s</div>
                </div>
                <div>
                  <span className="text-slate-500">Full Capacity</span>
                  <div className="font-mono text-slate-200">{result.full_flow_capacity_ls.toFixed(2)} L/s</div>
                </div>
                <div>
                  <span className="text-slate-500">Design Velocity</span>
                  <div className="font-mono text-slate-200">{result.velocity_ms.toFixed(2)} m/s</div>
                </div>
                <div>
                  <span className="text-slate-500">Min Flow Velocity</span>
                  <div className="font-mono text-slate-200">{result.min_flow_velocity_ms.toFixed(2)} m/s</div>
                </div>
              </div>
            </ResultsCard>

            <ResultsCard title="Design Checks">
              <div className="flex flex-wrap gap-2">
                <StatusBadge pass={result.is_capacity_adequate} label="Capacity" />
                <StatusBadge pass={result.is_velocity_adequate} label="Velocity" />
                <StatusBadge pass={result.is_self_cleansing} label="Self-Cleansing" />
              </div>
              {result.notes.length > 0 && (
                <div className="mt-3 space-y-1">
                  {result.notes.map((note, i) => (
                    <p key={i} className="text-xs text-amber-400 flex items-start gap-1">
                      <svg className="w-3 h-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      {note}
                    </p>
                  ))}
                </div>
              )}
            </ResultsCard>
          </>
        ) : (
          <div className="bg-slate-800/30 border border-slate-700 border-dashed rounded-lg p-8 text-center">
            <svg className="w-12 h-12 mx-auto text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-slate-500 text-sm">Configure parameters and click Calculate to see results</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Water Tab
function WaterTab() {
  const [serviceId, setServiceId] = useState('WM-1');
  const [projectName, setProjectName] = useState('');
  const [loads, setLoads] = useState<WaterLoadInput[]>([{
    load_id: 'W1',
    land_use: 'single_family',
    area_ha: 2.5,
    dwelling_units: 60,
  }]);
  const [lengthM, setLengthM] = useState(150);
  const [availablePressure, setAvailablePressure] = useState(400);
  const [elevationChange, setElevationChange] = useState(0);
  const [material, setMaterial] = useState('ductile_iron_new');
  const [result, setResult] = useState<WaterServiceResult | null>(null);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  // Fetch available presets
  const { data: presets, isLoading: presetsLoading } = useQuery({
    queryKey: ['water-presets'],
    queryFn: presetsApi.listWaterScenarios,
  });

  const { mutate: calculate, isPending } = useMutation({
    mutationFn: dsspApi.designWaterService,
    onSuccess: setResult,
  });

  // Load preset scenario
  const handleLoadPreset = useCallback(async (key: string) => {
    if (!key) return;
    setSelectedPreset(key);
    try {
      const scenario = await presetsApi.getWaterScenario(key);
      setProjectName(scenario.name);
      setLengthM(scenario.service_length_m);
      // Set loads based on scenario
      setLoads([{
        load_id: 'W1',
        land_use: scenario.building_type,
        area_ha: 1,
        dwelling_units: scenario.dwelling_units,
        population: Math.round(scenario.dwelling_units * scenario.occupants_per_unit),
      }]);
    } catch (err) {
      console.error('Failed to load preset:', err);
    }
  }, []);

  // Export report
  const handleExportReport = useCallback(async () => {
    if (!result) return;
    setIsExporting(true);
    try {
      const totalDwellingUnits = loads.reduce((sum, l) => sum + (l.dwelling_units || 0), 0);
      const html = await reportsApi.generateWaterReportHtml({
        project_name: projectName || 'Water Service Calculation',
        building_type: loads[0]?.land_use || 'single_family',
        dwelling_units: totalDwellingUnits || 1,
        service_length_m: lengthM,
      });
      downloadHtmlReport(html, `water-service-report-${Date.now()}.html`);
    } catch (err) {
      console.error('Failed to export report:', err);
    } finally {
      setIsExporting(false);
    }
  }, [result, projectName, loads, lengthM]);

  const handleCalculate = () => {
    calculate({
      service_id: serviceId,
      loads,
      length_m: lengthM,
      available_pressure_kpa: availablePressure,
      elevation_change_m: elevationChange,
      material,
    });
  };

  const updateLoad = (index: number, field: keyof WaterLoadInput, value: string | number) => {
    const updated = [...loads];
    updated[index] = { ...updated[index], [field]: value };
    setLoads(updated);
  };

  const addLoad = () => {
    setLoads([...loads, {
      load_id: `W${loads.length + 1}`,
      land_use: 'single_family',
      area_ha: 1,
    }]);
  };

  const removeLoad = (index: number) => {
    if (loads.length > 1) {
      setLoads(loads.filter((_, i) => i !== index));
    }
  };

  const overallStatus = result
    ? (result.is_pressure_adequate && result.is_velocity_adequate && result.is_fire_flow_adequate ? 'pass' : 'fail')
    : undefined;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Section */}
      <div className="space-y-4">
        {/* Preset Selector */}
        <div className="flex items-center justify-between">
          <PresetSelector
            scenarios={presets}
            isLoading={presetsLoading}
            selectedKey={selectedPreset}
            onSelect={handleLoadPreset}
          />
          {result && (
            <ExportReportButton
              onClick={handleExportReport}
              isExporting={isExporting}
              label="Export Report"
            />
          )}
        </div>

        {/* Project Name */}
        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <InputField
            label="Project Name"
            value={projectName}
            onChange={setProjectName}
            type="text"
            placeholder="Enter project name for report..."
          />
        </div>

        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider">
              Service Loads
            </h3>
            <button
              onClick={addLoad}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Load
            </button>
          </div>

          <div className="space-y-4">
            {loads.map((load, index) => (
              <div key={index} className="bg-slate-900/50 rounded p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-cyan-400">
                    LOAD {load.load_id}
                  </span>
                  {loads.length > 1 && (
                    <button
                      onClick={() => removeLoad(index)}
                      className="text-slate-500 hover:text-red-400 text-xs"
                    >
                      Remove
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <InputField
                    label="Area"
                    unit="ha"
                    value={load.area_ha}
                    onChange={(v) => updateLoad(index, 'area_ha', parseFloat(v) || 0)}
                    min={0.01}
                    step={0.1}
                    required
                  />
                  <SelectField
                    label="Land Use"
                    value={load.land_use}
                    onChange={(v) => updateLoad(index, 'land_use', v)}
                    options={LAND_USE_OPTIONS}
                    required
                  />
                  <InputField
                    label="Dwelling Units"
                    value={load.dwelling_units || ''}
                    onChange={(v) => updateLoad(index, 'dwelling_units', parseInt(v) || 0)}
                  />
                  <InputField
                    label="Population"
                    value={load.population || ''}
                    onChange={(v) => updateLoad(index, 'population', parseInt(v) || 0)}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider mb-4">
            Service Parameters
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <InputField
              label="Service ID"
              value={serviceId}
              onChange={setServiceId}
              type="text"
              required
            />
            <InputField
              label="Pipe Length"
              unit="m"
              value={lengthM}
              onChange={(v) => setLengthM(parseFloat(v) || 0)}
              min={1}
              required
            />
            <InputField
              label="Available Pressure"
              unit="kPa"
              value={availablePressure}
              onChange={(v) => setAvailablePressure(parseFloat(v) || 0)}
              min={0}
              required
            />
            <InputField
              label="Elevation Change"
              unit="m"
              value={elevationChange}
              onChange={(v) => setElevationChange(parseFloat(v) || 0)}
            />
            <SelectField
              label="Material"
              value={material}
              onChange={setMaterial}
              options={[
                { value: 'ductile_iron_new', label: 'Ductile Iron (New)' },
                { value: 'ductile_iron_aged', label: 'Ductile Iron (Aged)' },
                { value: 'pvc', label: 'PVC' },
                { value: 'hdpe', label: 'HDPE' },
              ]}
              required
            />
          </div>
        </div>

        <button
          onClick={handleCalculate}
          disabled={isPending}
          className="
            w-full py-3 px-4 bg-cyan-600 hover:bg-cyan-500
            text-white font-medium rounded
            transition-colors duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center justify-center gap-2
          "
        >
          {isPending ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Calculating...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              Calculate Design
            </>
          )}
        </button>
      </div>

      {/* Results Section */}
      <div className="space-y-4">
        {result ? (
          <>
            <ResultsCard title="Design Summary" status={overallStatus}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-3xl font-mono font-bold text-slate-100">
                    {result.diameter_mm} <span className="text-lg text-slate-400">mm</span>
                  </div>
                  <div className="text-xs text-slate-500 uppercase">Service Diameter</div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-mono font-bold text-slate-100">
                    {result.residual_pressure_kpa.toFixed(0)}
                  </div>
                  <div className="text-xs text-slate-500 uppercase">kPa Residual</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Design Flow</span>
                  <div className="font-mono text-slate-200">{result.design_flow_ls.toFixed(2)} L/s</div>
                </div>
                <div>
                  <span className="text-slate-500">Velocity</span>
                  <div className="font-mono text-slate-200">{result.velocity_ms.toFixed(2)} m/s</div>
                </div>
                <div>
                  <span className="text-slate-500">Head Loss</span>
                  <div className="font-mono text-slate-200">{result.head_loss_m.toFixed(2)} m</div>
                </div>
                <div>
                  <span className="text-slate-500">H-W C Value</span>
                  <div className="font-mono text-slate-200">{result.hazen_williams_c}</div>
                </div>
              </div>
            </ResultsCard>

            <ResultsCard title="Design Checks">
              <div className="flex flex-wrap gap-2">
                <StatusBadge pass={result.is_pressure_adequate} label="Pressure" />
                <StatusBadge pass={result.is_velocity_adequate} label="Velocity" />
                <StatusBadge pass={result.is_fire_flow_adequate} label="Fire Flow" />
              </div>
              {result.notes.length > 0 && (
                <div className="mt-3 space-y-1">
                  {result.notes.map((note, i) => (
                    <p key={i} className="text-xs text-amber-400 flex items-start gap-1">
                      <svg className="w-3 h-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      {note}
                    </p>
                  ))}
                </div>
              )}
            </ResultsCard>
          </>
        ) : (
          <div className="bg-slate-800/30 border border-slate-700 border-dashed rounded-lg p-8 text-center">
            <svg className="w-12 h-12 mx-auto text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-slate-500 text-sm">Configure parameters and click Calculate to see results</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export function DSSPCalculatorPage() {
  const [activeTab, setActiveTab] = useState<'stormwater' | 'sanitary' | 'water'>('stormwater');
  const [showIDF, setShowIDF] = useState(false);

  // Fetch IDF data
  const { data: idfTable } = useQuery({
    queryKey: ['idf-table'],
    queryFn: dsspApi.getIDFTable,
  });

  // Fetch standards
  const { data: standards } = useQuery({
    queryKey: ['calgary-standards'],
    queryFn: dsspApi.getStandards,
  });

  return (
    <div className="min-h-screen bg-slate-900 relative">
      {/* Blueprint Grid Background */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #0891b2 1px, transparent 1px),
            linear-gradient(to bottom, #0891b2 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Content */}
      <div className="relative max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded">
              <svg className="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
                DSSP Calculator
              </h1>
              <p className="text-sm text-slate-400">
                Development Site Servicing Plan — Calgary Standards
              </p>
            </div>
          </div>

          {/* Quick Reference Toggle */}
          <div className="flex items-center gap-4 mt-4">
            <button
              onClick={() => setShowIDF(!showIDF)}
              className={`
                text-xs px-3 py-1.5 rounded border transition-colors
                ${showIDF
                  ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                  : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:text-slate-300'
                }
              `}
            >
              IDF Reference Table
            </button>
          </div>
        </div>

        {/* IDF Reference Panel */}
        {showIDF && (
          <div className="mb-6 bg-slate-800/30 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider">
                Calgary IDF Curves — Rainfall Intensity (mm/hr)
              </h3>
              <button onClick={() => setShowIDF(false)} className="text-slate-500 hover:text-slate-400">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <IDFTable data={idfTable} />
            <p className="mt-3 text-xs text-slate-500">
              Formula: i = a / (t + b)<sup>c</sup> where t = duration (min)
            </p>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="border-b border-slate-700 mb-6">
          <div className="flex">
            <TabButton
              active={activeTab === 'stormwater'}
              onClick={() => setActiveTab('stormwater')}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                </svg>
              }
            >
              Stormwater
            </TabButton>
            <TabButton
              active={activeTab === 'sanitary'}
              onClick={() => setActiveTab('sanitary')}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              }
            >
              Sanitary
            </TabButton>
            <TabButton
              active={activeTab === 'water'}
              onClick={() => setActiveTab('water')}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              }
            >
              Water Service
            </TabButton>
          </div>
        </div>

        {/* Tab Content */}
        <div className="min-h-[500px]">
          {activeTab === 'stormwater' && <StormwaterTab />}
          {activeTab === 'sanitary' && <SanitaryTab />}
          {activeTab === 'water' && <WaterTab />}
        </div>

        {/* Standards Reference Footer */}
        {standards && (
          <div className="mt-8 pt-6 border-t border-slate-800">
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
              Calgary Design Standards Quick Reference
            </h4>
            <div className="grid grid-cols-3 gap-4 text-xs font-mono">
              <div className="bg-slate-800/30 rounded p-3">
                <div className="text-slate-400 mb-1">Stormwater</div>
                <div className="text-slate-300">Min Velocity: {standards.stormwater?.min_velocity || 0.6} m/s</div>
                <div className="text-slate-300">Max Velocity: {standards.stormwater?.max_velocity || 4.5} m/s</div>
                <div className="text-slate-300">Min Cover: {standards.stormwater?.min_cover || 2.0} m</div>
              </div>
              <div className="bg-slate-800/30 rounded p-3">
                <div className="text-slate-400 mb-1">Sanitary</div>
                <div className="text-slate-300">Min Velocity: {standards.sanitary?.min_velocity_design || 0.6} m/s</div>
                <div className="text-slate-300">Self-Clean: {standards.sanitary?.min_velocity_self_clean || 0.75} m/s</div>
                <div className="text-slate-300">Infiltration: {standards.sanitary?.infiltration_rate || 0.28} L/s/ha</div>
              </div>
              <div className="bg-slate-800/30 rounded p-3">
                <div className="text-slate-400 mb-1">Water</div>
                <div className="text-slate-300">Min Pressure: {standards.water?.min_pressure_normal || 275} kPa</div>
                <div className="text-slate-300">Fire Pressure: {standards.water?.min_pressure_during_fire || 140} kPa</div>
                <div className="text-slate-300">Max Velocity: {standards.water?.max_velocity || 2.5} m/s</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DSSPCalculatorPage;
