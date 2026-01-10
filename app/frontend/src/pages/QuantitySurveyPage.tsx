import { useState, useEffect, useCallback } from 'react';

// ============================================================================
// API CONSTANTS
// ============================================================================

const PRESETS_BASE = '/api/v1/presets';
const REPORTS_BASE = '/api/v1/reports';

// ============================================================================
// TYPES
// ============================================================================

interface ProjectTypeInfo {
  code: string;
  name: string;
  description: string;
}

interface PresetSummary {
  key: string;
  name: string;
  project_type: string;
  quality_level: string;
  gross_floor_area_sf: number;
}

interface ProjectPresetDetail {
  name: string;
  description: string;
  project_type: string;
  quality_level: string;
  gross_floor_area_sf: number;
  num_floors: number;
  basement_area_sf: number;
  garage_area_sf: number;
  has_basement: boolean;
  has_garage: boolean;
  num_bedrooms: number;
  num_bathrooms: number;
  special_features: string[];
  design_notes: string;
  typical_permit_fees: number;
  applicable_standards: string[];
}

interface QualityLevelInfo {
  code: string;
  name: string;
  cost_range_residential: { low: number; mid: number; high: number };
}

interface DivisionBreakdown {
  division_code: string;
  division_name: string;
  percentage: number;
  amount: number;
}

interface EstimateResult {
  project_type: string;
  quality_level: string;
  gross_floor_area_sf: number;
  cost_per_sf: number;
  construction_subtotal: number;
  division_breakdown: DivisionBreakdown[];
  location_factor: number;
  inflation_factor: number;
  adjusted_construction: number;
  contingency_percent: number;
  contingency_amount: number;
  design_fees_percent: number;
  design_fees_amount: number;
  permit_fees: number;
  other_soft_costs: number;
  total_soft_costs: number;
  total_project_cost: number;
  final_cost_per_sf: number;
}

interface BOQLineItem {
  item_number: string;
  csi_division: string;
  csi_code: string;
  description: string;
  quantity: number;
  unit: string;
  unit_rate: number;
  total_amount: number;
  notes: string;
}

interface BOQSection {
  division_code: string;
  division_name: string;
  line_items: BOQLineItem[];
  section_total: number;
}

interface BOQResult {
  project_name: string;
  sections: BOQSection[];
  subtotal: number;
  contingency_percent: number;
  contingency_amount: number;
  grand_total: number;
}

// ============================================================================
// COMPONENTS
// ============================================================================

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatNumber = (value: number, decimals: number = 0): string => {
  return new Intl.NumberFormat('en-CA', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

// ============================================================================
// API FUNCTIONS
// ============================================================================

const presetsApi = {
  listAllProjects: async (): Promise<{ residential: PresetSummary[]; commercial: PresetSummary[]; industrial: PresetSummary[] }> => {
    const response = await fetch(`${PRESETS_BASE}/qs/projects`);
    if (!response.ok) throw new Error('Failed to fetch presets');
    return response.json();
  },
  getProjectPreset: async (key: string): Promise<ProjectPresetDetail> => {
    const response = await fetch(`${PRESETS_BASE}/qs/projects/${key}`);
    if (!response.ok) throw new Error('Failed to fetch preset');
    return response.json();
  },
};

const reportsApi = {
  generateParametricEstimateHtml: async (data: {
    project_name?: string;
    project_type: string;
    gross_floor_area_sf: number;
    quality_level: string;
    num_floors: number;
    basement_area_sf: number;
    garage_area_sf: number;
    contingency_percent: number;
    design_fees_percent: number;
  }): Promise<string> => {
    const response = await fetch(`${REPORTS_BASE}/qs/parametric-estimate/html`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to generate report');
    return response.text();
  },
  generateBOQHtml: async (data: {
    project_name: string;
    gross_floor_area_sf: number;
    num_floors: number;
    num_bedrooms: number;
    num_bathrooms: number;
    has_basement: boolean;
    basement_area_sf: number;
    quality_level: string;
  }): Promise<string> => {
    const response = await fetch(`${REPORTS_BASE}/qs/boq/html`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to generate report');
    return response.text();
  },
};

// Helper to download HTML report
const downloadHtmlReport = (html: string, filename: string) => {
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// ============================================================================
// PRESET SELECTOR COMPONENT
// ============================================================================

const PresetSelector = ({
  presets,
  isLoading,
  selectedKey,
  onSelect,
}: {
  presets: { residential: PresetSummary[]; commercial: PresetSummary[]; industrial: PresetSummary[] } | null;
  isLoading: boolean;
  selectedKey: string;
  onSelect: (key: string) => void;
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        Loading presets...
      </div>
    );
  }

  if (!presets) return null;

  const allPresets = [
    ...presets.residential.map(p => ({ ...p, category: 'Residential' })),
    ...presets.commercial.map(p => ({ ...p, category: 'Commercial' })),
    ...presets.industrial.map(p => ({ ...p, category: 'Industrial' })),
  ];

  if (allPresets.length === 0) return null;

  return (
    <div className="flex items-center gap-2">
      <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
      </svg>
      <select
        value={selectedKey}
        onChange={(e) => onSelect(e.target.value)}
        className="text-xs px-2 py-1 bg-gray-800 border border-amber-500/30 rounded text-amber-300 font-medium focus:outline-none focus:border-amber-400/50 cursor-pointer hover:bg-gray-700"
      >
        <option value="">Load Preset Project...</option>
        {['Residential', 'Commercial', 'Industrial'].map(category => {
          const categoryPresets = allPresets.filter(p => p.category === category);
          if (categoryPresets.length === 0) return null;
          return (
            <optgroup key={category} label={category}>
              {categoryPresets.map(p => (
                <option key={p.key} value={p.key}>
                  {p.name} ({formatNumber(p.gross_floor_area_sf)} SF)
                </option>
              ))}
            </optgroup>
          );
        })}
      </select>
    </div>
  );
};

// ============================================================================
// EXPORT BUTTON COMPONENT
// ============================================================================

const ExportReportButton = ({
  onClick,
  isExporting,
  label = 'Export Report',
}: {
  onClick: () => void;
  isExporting: boolean;
  label?: string;
}) => (
  <button
    onClick={onClick}
    disabled={isExporting}
    className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-emerald-600/20 border border-emerald-500/30 rounded text-emerald-400 hover:bg-emerald-600/30 hover:border-emerald-500/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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

// Cost Gauge Component
const CostGauge = ({
  value,
  max,
  label,
  color = '#0ff'
}: {
  value: number;
  max: number;
  label: string;
  color?: string;
}) => {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div className="relative">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span style={{ color }}>{formatCurrency(value)}</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden border border-gray-700">
        <div
          className="h-full transition-all duration-500 ease-out"
          style={{
            width: `${percentage}%`,
            background: `linear-gradient(90deg, ${color}33, ${color})`,
            boxShadow: `0 0 10px ${color}66`
          }}
        />
      </div>
    </div>
  );
};

// Division Bar Chart
const DivisionBarChart = ({ breakdown }: { breakdown: DivisionBreakdown[] }) => {
  const maxAmount = Math.max(...breakdown.map(d => d.amount));
  const colors = [
    '#0ff', '#0f0', '#ff0', '#f80', '#f0f', '#80f', '#08f',
    '#0ff', '#0f0', '#ff0', '#f80', '#f0f', '#80f', '#08f'
  ];

  return (
    <div className="space-y-2">
      {breakdown.map((div, idx) => {
        const width = (div.amount / maxAmount) * 100;
        return (
          <div key={div.division_code} className="group">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-400 truncate max-w-[200px]" title={div.division_name}>
                {div.division_name.replace('Division ', 'Div ')}
              </span>
              <span className="text-gray-300 ml-2">{div.percentage.toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-4 bg-gray-800 rounded overflow-hidden border border-gray-700">
                <div
                  className="h-full transition-all duration-300"
                  style={{
                    width: `${width}%`,
                    backgroundColor: colors[idx % colors.length],
                    opacity: 0.7
                  }}
                />
              </div>
              <span className="text-xs text-gray-400 w-20 text-right">
                {formatCurrency(div.amount)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Summary Card
const SummaryCard = ({
  title,
  value,
  subtitle,
  highlight = false
}: {
  title: string;
  value: string;
  subtitle?: string;
  highlight?: boolean;
}) => (
  <div className={`p-4 rounded-lg border ${
    highlight
      ? 'bg-cyan-900/30 border-cyan-500/50'
      : 'bg-gray-800/50 border-gray-700'
  }`}>
    <div className="text-xs text-gray-400 uppercase tracking-wide">{title}</div>
    <div className={`text-2xl font-mono font-bold mt-1 ${
      highlight ? 'text-cyan-400' : 'text-white'
    }`}>
      {value}
    </div>
    {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
  </div>
);

// BOQ Table Component
const BOQTable = ({ boq }: { boq: BOQResult }) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const toggleSection = (code: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(code)) {
      newExpanded.delete(code);
    } else {
      newExpanded.add(code);
    }
    setExpandedSections(newExpanded);
  };

  return (
    <div className="space-y-2">
      {boq.sections.map((section) => (
        <div key={section.division_code} className="border border-gray-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection(section.division_code)}
            className="w-full flex items-center justify-between p-3 bg-gray-800/50 hover:bg-gray-800 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="text-cyan-400 font-mono text-sm">
                {expandedSections.has(section.division_code) ? '▼' : '▶'}
              </span>
              <span className="text-gray-300 font-medium">{section.division_name}</span>
              <span className="text-xs text-gray-500">({section.line_items.length} items)</span>
            </div>
            <span className="text-cyan-400 font-mono">{formatCurrency(section.section_total)}</span>
          </button>

          {expandedSections.has(section.division_code) && (
            <div className="bg-gray-900/50">
              <table className="w-full text-sm">
                <thead className="bg-gray-800/30 text-gray-400">
                  <tr>
                    <th className="text-left p-2 w-12">#</th>
                    <th className="text-left p-2">Description</th>
                    <th className="text-right p-2 w-20">Qty</th>
                    <th className="text-center p-2 w-12">Unit</th>
                    <th className="text-right p-2 w-24">Rate</th>
                    <th className="text-right p-2 w-28">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {section.line_items.map((item) => (
                    <tr key={item.item_number} className="border-t border-gray-800 hover:bg-gray-800/30">
                      <td className="p-2 text-gray-500 font-mono text-xs">{item.item_number}</td>
                      <td className="p-2 text-gray-300">{item.description}</td>
                      <td className="p-2 text-right text-gray-400 font-mono">{formatNumber(item.quantity, 1)}</td>
                      <td className="p-2 text-center text-gray-500 uppercase text-xs">{item.unit}</td>
                      <td className="p-2 text-right text-gray-400 font-mono">${formatNumber(item.unit_rate, 2)}</td>
                      <td className="p-2 text-right text-cyan-400 font-mono">{formatCurrency(item.total_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}

      {/* Totals */}
      <div className="border-t-2 border-cyan-500/50 pt-4 mt-4 space-y-2">
        <div className="flex justify-between text-gray-300">
          <span>Subtotal</span>
          <span className="font-mono">{formatCurrency(boq.subtotal)}</span>
        </div>
        <div className="flex justify-between text-gray-400">
          <span>Contingency ({boq.contingency_percent}%)</span>
          <span className="font-mono">{formatCurrency(boq.contingency_amount)}</span>
        </div>
        <div className="flex justify-between text-xl font-bold text-cyan-400 pt-2 border-t border-gray-700">
          <span>Grand Total</span>
          <span className="font-mono">{formatCurrency(boq.grand_total)}</span>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function QuantitySurveyPage() {
  // State
  const [activeTab, setActiveTab] = useState<'estimate' | 'boq'>('estimate');
  const [projectTypes, setProjectTypes] = useState<ProjectTypeInfo[]>([]);
  const [qualityLevels, setQualityLevels] = useState<QualityLevelInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Preset State
  const [presets, setPresets] = useState<{ residential: PresetSummary[]; commercial: PresetSummary[]; industrial: PresetSummary[] } | null>(null);
  const [presetsLoading, setPresetsLoading] = useState(true);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  // Estimate Form State
  const [estimateForm, setEstimateForm] = useState({
    project_name: '',
    project_type: 'residential_single',
    gross_floor_area_sf: 2000,
    quality_level: 'standard',
    estimate_level: 'mid',
    num_floors: 2,
    basement_area_sf: 800,
    garage_area_sf: 400,
    location: 'calgary',
    contingency_percent: 10,
    design_fees_percent: 8,
  });

  // BOQ Form State
  const [boqForm, setBoqForm] = useState({
    project_name: 'New Residential Home',
    gross_floor_area_sf: 2000,
    num_floors: 2,
    num_bedrooms: 3,
    num_bathrooms: 2,
    has_basement: true,
    basement_area_sf: 800,
    has_garage: true,
    garage_area_sf: 400,
    quality_level: 'standard',
    contingency_percent: 10,
  });

  // Results
  const [estimateResult, setEstimateResult] = useState<EstimateResult | null>(null);
  const [boqResult, setBoqResult] = useState<BOQResult | null>(null);

  // Load reference data and presets
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [typesRes, levelsRes] = await Promise.all([
          fetch('/api/v1/quantity-survey/project-types'),
          fetch('/api/v1/quantity-survey/quality-levels'),
        ]);

        if (typesRes.ok) setProjectTypes(await typesRes.json());
        if (levelsRes.ok) setQualityLevels(await levelsRes.json());
      } catch (err) {
        console.error('Failed to load reference data:', err);
      }
    };
    fetchData();
  }, []);

  // Load presets
  useEffect(() => {
    const fetchPresets = async () => {
      setPresetsLoading(true);
      try {
        const data = await presetsApi.listAllProjects();
        setPresets(data);
      } catch (err) {
        console.error('Failed to load presets:', err);
      } finally {
        setPresetsLoading(false);
      }
    };
    fetchPresets();
  }, []);

  // Load preset into form
  const handleLoadPreset = useCallback(async (key: string) => {
    if (!key) return;
    setSelectedPreset(key);
    try {
      const preset = await presetsApi.getProjectPreset(key);
      // Update both forms with preset data
      setEstimateForm(prev => ({
        ...prev,
        project_name: preset.name,
        project_type: preset.project_type,
        gross_floor_area_sf: preset.gross_floor_area_sf,
        quality_level: preset.quality_level,
        num_floors: preset.num_floors,
        basement_area_sf: preset.basement_area_sf,
        garage_area_sf: preset.garage_area_sf,
      }));
      setBoqForm(prev => ({
        ...prev,
        project_name: preset.name,
        gross_floor_area_sf: preset.gross_floor_area_sf,
        num_floors: preset.num_floors,
        num_bedrooms: preset.num_bedrooms,
        num_bathrooms: preset.num_bathrooms,
        has_basement: preset.has_basement,
        basement_area_sf: preset.basement_area_sf,
        has_garage: preset.has_garage,
        garage_area_sf: preset.garage_area_sf,
        quality_level: preset.quality_level,
      }));
    } catch (err) {
      console.error('Failed to load preset:', err);
    }
  }, []);

  // Export estimate report
  const handleExportEstimate = useCallback(async () => {
    if (!estimateResult) return;
    setIsExporting(true);
    try {
      const html = await reportsApi.generateParametricEstimateHtml({
        project_name: estimateForm.project_name || 'Cost Estimate',
        project_type: estimateForm.project_type,
        gross_floor_area_sf: estimateForm.gross_floor_area_sf,
        quality_level: estimateForm.quality_level,
        num_floors: estimateForm.num_floors,
        basement_area_sf: estimateForm.basement_area_sf,
        garage_area_sf: estimateForm.garage_area_sf,
        contingency_percent: estimateForm.contingency_percent,
        design_fees_percent: estimateForm.design_fees_percent,
      });
      downloadHtmlReport(html, `cost-estimate-${Date.now()}.html`);
    } catch (err) {
      console.error('Failed to export report:', err);
    } finally {
      setIsExporting(false);
    }
  }, [estimateResult, estimateForm]);

  // Export BOQ report
  const handleExportBOQ = useCallback(async () => {
    if (!boqResult) return;
    setIsExporting(true);
    try {
      const html = await reportsApi.generateBOQHtml({
        project_name: boqForm.project_name,
        gross_floor_area_sf: boqForm.gross_floor_area_sf,
        num_floors: boqForm.num_floors,
        num_bedrooms: boqForm.num_bedrooms,
        num_bathrooms: boqForm.num_bathrooms,
        has_basement: boqForm.has_basement,
        basement_area_sf: boqForm.basement_area_sf,
        quality_level: boqForm.quality_level,
      });
      downloadHtmlReport(html, `boq-report-${Date.now()}.html`);
    } catch (err) {
      console.error('Failed to export report:', err);
    } finally {
      setIsExporting(false);
    }
  }, [boqResult, boqForm]);

  // Calculate estimate
  const calculateEstimate = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/quantity-survey/parametric-estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(estimateForm),
      });

      if (!response.ok) {
        throw new Error('Failed to calculate estimate');
      }

      const result = await response.json();
      setEstimateResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation failed');
    } finally {
      setIsLoading(false);
    }
  }, [estimateForm]);

  // Generate BOQ
  const generateBOQ = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/quantity-survey/residential-boq', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(boqForm),
      });

      if (!response.ok) {
        throw new Error('Failed to generate BOQ');
      }

      const result = await response.json();
      setBoqResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setIsLoading(false);
    }
  }, [boqForm]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-cyan-400 tracking-tight">
                Quantity Survey Calculator
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Calgary Construction Cost Estimation • CIQS Methodology
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
                Bylaw 5M2004
              </span>
              <span className="text-xs text-gray-500 bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
                2024 Costs
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Tab Navigation and Actions */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex gap-1 bg-gray-900 p-1 rounded-lg w-fit">
            <button
              onClick={() => setActiveTab('estimate')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === 'estimate'
                  ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/25'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              Parametric Estimate
            </button>
            <button
              onClick={() => setActiveTab('boq')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === 'boq'
                  ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/25'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              Bill of Quantities
            </button>
          </div>

          {/* Preset Selector and Export */}
          <div className="flex items-center gap-4">
            <PresetSelector
              presets={presets}
              isLoading={presetsLoading}
              selectedKey={selectedPreset}
              onSelect={handleLoadPreset}
            />
            {activeTab === 'estimate' && estimateResult && (
              <ExportReportButton
                onClick={handleExportEstimate}
                isExporting={isExporting}
                label="Export Estimate"
              />
            )}
            {activeTab === 'boq' && boqResult && (
              <ExportReportButton
                onClick={handleExportBOQ}
                isExporting={isExporting}
                label="Export BOQ"
              />
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Panel */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
              <h2 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-cyan-600 rounded-lg flex items-center justify-center text-sm">📐</span>
                Project Parameters
              </h2>

              {activeTab === 'estimate' ? (
                <div className="space-y-4">
                  {/* Project Name */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Project Name
                    </label>
                    <input
                      type="text"
                      value={estimateForm.project_name}
                      onChange={(e) => setEstimateForm({ ...estimateForm, project_name: e.target.value })}
                      placeholder="Enter project name for report..."
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-cyan-500 placeholder-gray-600"
                    />
                  </div>

                  {/* Project Type */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Project Type
                    </label>
                    <select
                      value={estimateForm.project_type}
                      onChange={(e) => setEstimateForm({ ...estimateForm, project_type: e.target.value })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-cyan-500"
                    >
                      {projectTypes.map((type) => (
                        <option key={type.code} value={type.code}>{type.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Floor Area */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Gross Floor Area (SF)
                    </label>
                    <input
                      type="number"
                      value={estimateForm.gross_floor_area_sf}
                      onChange={(e) => setEstimateForm({ ...estimateForm, gross_floor_area_sf: Number(e.target.value) })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  {/* Quality Level */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Quality Level
                    </label>
                    <select
                      value={estimateForm.quality_level}
                      onChange={(e) => setEstimateForm({ ...estimateForm, quality_level: e.target.value })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-cyan-500"
                    >
                      {qualityLevels.map((level) => (
                        <option key={level.code} value={level.code}>{level.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Number of Floors */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Number of Floors
                    </label>
                    <input
                      type="number"
                      value={estimateForm.num_floors}
                      onChange={(e) => setEstimateForm({ ...estimateForm, num_floors: Number(e.target.value) })}
                      min={1}
                      max={50}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  {/* Basement Area */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Basement Area (SF)
                    </label>
                    <input
                      type="number"
                      value={estimateForm.basement_area_sf}
                      onChange={(e) => setEstimateForm({ ...estimateForm, basement_area_sf: Number(e.target.value) })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  {/* Garage Area */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Garage Area (SF)
                    </label>
                    <input
                      type="number"
                      value={estimateForm.garage_area_sf}
                      onChange={(e) => setEstimateForm({ ...estimateForm, garage_area_sf: Number(e.target.value) })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  {/* Contingency */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Contingency (%)
                    </label>
                    <input
                      type="number"
                      value={estimateForm.contingency_percent}
                      onChange={(e) => setEstimateForm({ ...estimateForm, contingency_percent: Number(e.target.value) })}
                      min={0}
                      max={30}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  {/* Calculate Button */}
                  <button
                    onClick={calculateEstimate}
                    disabled={isLoading}
                    className="w-full py-3 bg-gradient-to-r from-cyan-600 to-cyan-500 text-white font-semibold rounded-lg hover:from-cyan-500 hover:to-cyan-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/25"
                  >
                    {isLoading ? 'Calculating...' : 'Calculate Estimate'}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Project Name */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Project Name
                    </label>
                    <input
                      type="text"
                      value={boqForm.project_name}
                      onChange={(e) => setBoqForm({ ...boqForm, project_name: e.target.value })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  {/* Floor Area */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Gross Floor Area (SF)
                    </label>
                    <input
                      type="number"
                      value={boqForm.gross_floor_area_sf}
                      onChange={(e) => setBoqForm({ ...boqForm, gross_floor_area_sf: Number(e.target.value) })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    {/* Floors */}
                    <div>
                      <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                        Floors
                      </label>
                      <input
                        type="number"
                        value={boqForm.num_floors}
                        onChange={(e) => setBoqForm({ ...boqForm, num_floors: Number(e.target.value) })}
                        min={1}
                        max={4}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    {/* Bedrooms */}
                    <div>
                      <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                        Bedrooms
                      </label>
                      <input
                        type="number"
                        value={boqForm.num_bedrooms}
                        onChange={(e) => setBoqForm({ ...boqForm, num_bedrooms: Number(e.target.value) })}
                        min={1}
                        max={10}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>

                  {/* Bathrooms */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Bathrooms
                    </label>
                    <input
                      type="number"
                      value={boqForm.num_bathrooms}
                      onChange={(e) => setBoqForm({ ...boqForm, num_bathrooms: Number(e.target.value) })}
                      min={1}
                      max={6}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  {/* Basement Toggle */}
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-400">Has Basement</label>
                    <button
                      onClick={() => setBoqForm({ ...boqForm, has_basement: !boqForm.has_basement })}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        boqForm.has_basement ? 'bg-cyan-600' : 'bg-gray-700'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-full bg-white shadow transform transition-transform ${
                        boqForm.has_basement ? 'translate-x-6' : 'translate-x-0.5'
                      }`} />
                    </button>
                  </div>

                  {boqForm.has_basement && (
                    <div>
                      <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                        Basement Area (SF)
                      </label>
                      <input
                        type="number"
                        value={boqForm.basement_area_sf}
                        onChange={(e) => setBoqForm({ ...boqForm, basement_area_sf: Number(e.target.value) })}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  )}

                  {/* Quality */}
                  <div>
                    <label className="block text-xs text-gray-400 uppercase tracking-wide mb-1">
                      Quality Level
                    </label>
                    <select
                      value={boqForm.quality_level}
                      onChange={(e) => setBoqForm({ ...boqForm, quality_level: e.target.value })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-cyan-500"
                    >
                      {qualityLevels.map((level) => (
                        <option key={level.code} value={level.code}>{level.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Generate Button */}
                  <button
                    onClick={generateBOQ}
                    disabled={isLoading}
                    className="w-full py-3 bg-gradient-to-r from-cyan-600 to-cyan-500 text-white font-semibold rounded-lg hover:from-cyan-500 hover:to-cyan-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/25"
                  >
                    {isLoading ? 'Generating...' : 'Generate BOQ'}
                  </button>
                </div>
              )}
            </div>

            {/* Calgary Standards Reference */}
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Calgary Permit Fees</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between text-gray-400">
                  <span>Building Permit</span>
                  <span className="font-mono text-cyan-400">$10.14 / $1,000</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Trade Permits</span>
                  <span className="font-mono text-cyan-400">$9.79 / $1,000</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Minimum Fee</span>
                  <span className="font-mono text-cyan-400">$114.00</span>
                </div>
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {activeTab === 'estimate' && estimateResult && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <SummaryCard
                    title="Construction Cost"
                    value={formatCurrency(estimateResult.adjusted_construction)}
                    subtitle="Hard costs"
                  />
                  <SummaryCard
                    title="Soft Costs"
                    value={formatCurrency(estimateResult.total_soft_costs)}
                    subtitle="Fees, contingency"
                  />
                  <SummaryCard
                    title="Permit Fees"
                    value={formatCurrency(estimateResult.permit_fees)}
                    subtitle="City of Calgary"
                  />
                  <SummaryCard
                    title="Total Project"
                    value={formatCurrency(estimateResult.total_project_cost)}
                    subtitle={`${formatCurrency(estimateResult.final_cost_per_sf)}/SF`}
                    highlight
                  />
                </div>

                {/* Cost Breakdown */}
                <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
                  <h3 className="text-lg font-semibold text-gray-200 mb-4">Cost Breakdown by CSI Division</h3>
                  <DivisionBarChart breakdown={estimateResult.division_breakdown} />
                </div>

                {/* Detailed Costs */}
                <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
                  <h3 className="text-lg font-semibold text-gray-200 mb-4">Cost Analysis</h3>
                  <div className="space-y-4">
                    <CostGauge
                      value={estimateResult.adjusted_construction}
                      max={estimateResult.total_project_cost}
                      label="Construction"
                      color="#0ff"
                    />
                    <CostGauge
                      value={estimateResult.contingency_amount}
                      max={estimateResult.total_project_cost}
                      label={`Contingency (${estimateResult.contingency_percent}%)`}
                      color="#ff0"
                    />
                    <CostGauge
                      value={estimateResult.design_fees_amount}
                      max={estimateResult.total_project_cost}
                      label={`Design Fees (${estimateResult.design_fees_percent}%)`}
                      color="#0f0"
                    />
                    <CostGauge
                      value={estimateResult.permit_fees}
                      max={estimateResult.total_project_cost}
                      label="Permit Fees"
                      color="#f80"
                    />
                    <CostGauge
                      value={estimateResult.other_soft_costs}
                      max={estimateResult.total_project_cost}
                      label="Other Soft Costs"
                      color="#80f"
                    />
                  </div>
                </div>

                {/* Adjustment Factors */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wide">Location Factor</div>
                    <div className="text-2xl font-mono text-cyan-400 mt-1">
                      {estimateResult.location_factor.toFixed(2)}x
                    </div>
                    <div className="text-xs text-gray-500">Calgary base</div>
                  </div>
                  <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wide">Inflation Factor</div>
                    <div className="text-2xl font-mono text-cyan-400 mt-1">
                      {estimateResult.inflation_factor.toFixed(3)}x
                    </div>
                    <div className="text-xs text-gray-500">2024 adjustment</div>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'boq' && boqResult && (
              <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-200">{boqResult.project_name}</h3>
                    <p className="text-sm text-gray-500">Bill of Quantities</p>
                  </div>
                  <ExportReportButton
                    onClick={handleExportBOQ}
                    isExporting={isExporting}
                    label="Export BOQ"
                  />
                </div>
                <BOQTable boq={boqResult} />
              </div>
            )}

            {/* Empty State */}
            {((activeTab === 'estimate' && !estimateResult) || (activeTab === 'boq' && !boqResult)) && (
              <div className="bg-gray-900 rounded-lg border border-gray-800 p-12 text-center">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-xl text-gray-300 mb-2">
                  {activeTab === 'estimate' ? 'No Estimate Generated' : 'No BOQ Generated'}
                </h3>
                <p className="text-gray-500">
                  {activeTab === 'estimate'
                    ? 'Enter project parameters and click Calculate to generate a cost estimate'
                    : 'Enter project details and click Generate to create a Bill of Quantities'
                  }
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default QuantitySurveyPage;
