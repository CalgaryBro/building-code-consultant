import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

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
  description: string;
  area_sf: number;
  quality: string;
  project_type?: string;  // Optional, may not be in summary
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

// Material Price Types
interface PriceSource {
  name: string;
  url: string | null;
  reliability: string;
  update_frequency: string;
}

interface MaterialItem {
  description: string;
  unit: string;
  price: number;
  price_range: { low: number; high: number };
  source: string;
  last_updated: string;
  notes?: string;
}

interface MaterialCategory {
  category: string;
  items: Record<string, MaterialItem>;
}

interface MaterialPricesData {
  metadata: {
    title: string;
    version: string;
    last_updated: string;
    currency: string;
  };
  price_sources: Record<string, PriceSource>;
  materials: Record<string, MaterialCategory>;
  labor_rates: Record<string, { rate: number; source: string; notes: string }>;
  market_trends: Record<string, { trend: string; change_ytd_percent: number; forecast_2026: string; source: string }>;
}

interface PriceSyncStatus {
  [source: string]: {
    source_name: string;
    source_url: string | null;
    cache_valid: boolean;
    last_sync: string | null;
    cache_ttl_hours: number;
  };
}

interface ScheduledJob {
  id: string;
  name: string;
  next_run: string | null;
  trigger: string;
}

interface PriceRefreshResult {
  success: boolean;
  message: string;
  result?: {
    sources_refreshed?: string[];
    results?: Record<string, { success: boolean; prices_fetched: number; cached: boolean; error: string | null }>;
  };
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

// Material Prices API
const materialPricesApi = {
  getAll: async (): Promise<MaterialPricesData> => {
    const response = await fetch('/api/v1/quantity-survey/material-prices');
    if (!response.ok) throw new Error('Failed to fetch material prices');
    return response.json();
  },
  updatePrice: async (category: string, itemId: string, price: number, notes?: string): Promise<void> => {
    const response = await fetch(`/api/v1/quantity-survey/material-prices/item/${category}/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ price, notes }),
    });
    if (!response.ok) throw new Error('Failed to update price');
  },
  search: async (query: string): Promise<{ results: Array<{ category: string; item_id: string; description: string; price: number; unit: string; source: string }> }> => {
    const response = await fetch(`/api/v1/quantity-survey/material-prices/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search');
    return response.json();
  },
  getSyncStatus: async (): Promise<PriceSyncStatus> => {
    const response = await fetch('/api/v1/quantity-survey/prices/sync-status');
    if (!response.ok) throw new Error('Failed to fetch sync status');
    const data = await response.json();
    // The API returns source_status nested inside a larger status object
    return data.source_status || data;
  },
  getScheduledJobs: async (): Promise<ScheduledJob[]> => {
    const response = await fetch('/api/v1/quantity-survey/prices/scheduled-jobs');
    if (!response.ok) throw new Error('Failed to fetch scheduled jobs');
    const data = await response.json();
    // The API returns jobs nested inside { scheduler_running: bool, jobs: [] }
    return data.jobs || data;
  },
  refreshPrices: async (source?: string, force: boolean = true): Promise<PriceRefreshResult> => {
    const params = new URLSearchParams();
    if (source) params.append('source', source);
    if (force) params.append('force', 'true');
    const response = await fetch(`/api/v1/quantity-survey/prices/refresh?${params.toString()}`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Refresh failed' }));
      throw new Error(error.detail || 'Failed to refresh prices');
    }
    return response.json();
  },
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
        className="text-sm px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-gray-700 font-medium focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 cursor-pointer shadow-sm hover:border-gray-400"
      >
        <option value="">Load Preset Project...</option>
        {['Residential', 'Commercial', 'Industrial'].map(category => {
          const categoryPresets = allPresets.filter(p => p.category === category);
          if (categoryPresets.length === 0) return null;
          return (
            <optgroup key={category} label={category}>
              {categoryPresets.map(p => (
                <option key={p.key} value={p.key}>
                  {p.name} ({formatNumber(p.area_sf)} SF)
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
    className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-700 hover:bg-emerald-100 hover:border-emerald-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
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
  color = '#f59e0b'
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
        <span className="text-gray-600">{label}</span>
        <span className="text-gray-900 font-medium">{formatCurrency(value)}</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full transition-all duration-500 ease-out"
          style={{
            width: `${percentage}%`,
            background: `linear-gradient(90deg, ${color}66, ${color})`,
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
    '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16',
    '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
  ];

  return (
    <div className="space-y-2">
      {breakdown.map((div, idx) => {
        const width = (div.amount / maxAmount) * 100;
        return (
          <div key={div.division_code} className="group">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-600 truncate max-w-[200px]" title={div.division_name}>
                {div.division_name.replace('Division ', 'Div ')}
              </span>
              <span className="text-gray-800 font-medium ml-2">{div.percentage.toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-4 bg-gray-100 rounded-lg overflow-hidden border border-gray-200">
                <div
                  className="h-full transition-all duration-300"
                  style={{
                    width: `${width}%`,
                    backgroundColor: colors[idx % colors.length],
                    opacity: 0.85
                  }}
                />
              </div>
              <span className="text-xs text-gray-700 w-20 text-right font-medium">
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
  <div className={`p-4 rounded-xl border shadow-sm ${
    highlight
      ? 'bg-amber-50 border-amber-200'
      : 'bg-white border-gray-200'
  }`}>
    <div className="text-xs text-gray-500 uppercase tracking-wide">{title}</div>
    <div className={`text-2xl font-mono font-bold mt-1 ${
      highlight ? 'text-amber-600' : 'text-gray-900'
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
        <div key={section.division_code} className="border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <button
            onClick={() => toggleSection(section.division_code)}
            className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="text-amber-600 font-mono text-sm">
                {expandedSections.has(section.division_code) ? '▼' : '▶'}
              </span>
              <span className="text-gray-800 font-medium">{section.division_name}</span>
              <span className="text-xs text-gray-500">({section.line_items.length} items)</span>
            </div>
            <span className="text-amber-600 font-mono font-semibold">{formatCurrency(section.section_total)}</span>
          </button>

          {expandedSections.has(section.division_code) && (
            <div className="bg-white">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-600">
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
                    <tr key={item.item_number} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="p-2 text-gray-400 font-mono text-xs">{item.item_number}</td>
                      <td className="p-2 text-gray-700">{item.description}</td>
                      <td className="p-2 text-right text-gray-600 font-mono">{formatNumber(item.quantity, 1)}</td>
                      <td className="p-2 text-center text-gray-500 uppercase text-xs">{item.unit}</td>
                      <td className="p-2 text-right text-gray-600 font-mono">${formatNumber(item.unit_rate, 2)}</td>
                      <td className="p-2 text-right text-amber-600 font-mono font-medium">{formatCurrency(item.total_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}

      {/* Totals */}
      <div className="border-t-2 border-amber-200 pt-4 mt-4 space-y-2">
        <div className="flex justify-between text-gray-700">
          <span>Subtotal</span>
          <span className="font-mono">{formatCurrency(boq.subtotal)}</span>
        </div>
        <div className="flex justify-between text-gray-500">
          <span>Contingency ({boq.contingency_percent}%)</span>
          <span className="font-mono">{formatCurrency(boq.contingency_amount)}</span>
        </div>
        <div className="flex justify-between text-xl font-bold text-amber-600 pt-2 border-t border-gray-200">
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
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  // State
  const [activeTab, setActiveTab] = useState<'estimate' | 'boq' | 'prices'>('estimate');
  const [projectTypes, setProjectTypes] = useState<ProjectTypeInfo[]>([]);
  const [qualityLevels, setQualityLevels] = useState<QualityLevelInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Preset State
  const [presets, setPresets] = useState<{ residential: PresetSummary[]; commercial: PresetSummary[]; industrial: PresetSummary[] } | null>(null);
  const [presetsLoading, setPresetsLoading] = useState(true);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  // Material Prices State
  const [materialPrices, setMaterialPrices] = useState<MaterialPricesData | null>(null);
  const [pricesLoading, setPricesLoading] = useState(false);
  const [selectedPriceCategory, setSelectedPriceCategory] = useState<string>('lumber');
  const [priceSearchQuery, setPriceSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{ category: string; item_id: string; description: string; price: number; unit: string; source: string }>>([]);
  const [editingPrice, setEditingPrice] = useState<{ category: string; itemId: string; value: string } | null>(null);
  const [syncStatus, setSyncStatus] = useState<PriceSyncStatus | null>(null);
  const [scheduledJobs, setScheduledJobs] = useState<ScheduledJob[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

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

  // Load material prices and sync status when prices tab is selected
  useEffect(() => {
    if (activeTab === 'prices') {
      const fetchPricesAndStatus = async () => {
        if (!materialPrices) {
          setPricesLoading(true);
          try {
            const data = await materialPricesApi.getAll();
            setMaterialPrices(data);
          } catch (err) {
            console.error('Failed to load material prices:', err);
          } finally {
            setPricesLoading(false);
          }
        }
        // Always fetch sync status when entering prices tab
        try {
          const [status, jobs] = await Promise.all([
            materialPricesApi.getSyncStatus(),
            materialPricesApi.getScheduledJobs(),
          ]);
          setSyncStatus(status);
          setScheduledJobs(jobs);
        } catch (err) {
          console.error('Failed to load sync status:', err);
        }
      };
      fetchPricesAndStatus();
    }
  }, [activeTab, materialPrices]);

  // Handle manual price refresh from external sources
  const handleRefreshPrices = useCallback(async (source?: string) => {
    setIsRefreshing(true);
    setRefreshMessage(null);
    try {
      const result = await materialPricesApi.refreshPrices(source, true);
      // Reload prices and sync status after refresh
      const [prices, status] = await Promise.all([
        materialPricesApi.getAll(),
        materialPricesApi.getSyncStatus(),
      ]);
      setMaterialPrices(prices);
      setSyncStatus(status);
      setRefreshMessage({
        type: 'success',
        text: result.message || 'Prices refreshed successfully',
      });
    } catch (err) {
      setRefreshMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to refresh prices',
      });
    } finally {
      setIsRefreshing(false);
      // Clear message after 5 seconds
      setTimeout(() => setRefreshMessage(null), 5000);
    }
  }, []);

  // Handle price search
  const handlePriceSearch = useCallback(async () => {
    if (!priceSearchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const data = await materialPricesApi.search(priceSearchQuery);
      setSearchResults(data.results);
    } catch (err) {
      console.error('Search failed:', err);
    }
  }, [priceSearchQuery]);

  // Handle price update
  const handlePriceUpdate = useCallback(async (category: string, itemId: string, newPrice: number) => {
    try {
      await materialPricesApi.updatePrice(category, itemId, newPrice);
      // Refresh prices
      const data = await materialPricesApi.getAll();
      setMaterialPrices(data);
      setEditingPrice(null);
    } catch (err) {
      console.error('Failed to update price:', err);
    }
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          {/* Back Button */}
          <button
            onClick={() => navigate('/explore')}
            className="inline-flex items-center gap-2 px-3 py-1.5 mb-3 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors border border-gray-200 shadow-sm"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span className="text-sm font-medium">Back to Explore</span>
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
                Quantity Survey Calculator
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Calgary Construction Cost Estimation • CIQS Methodology
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-600 bg-gray-100 px-3 py-1 rounded-full border border-gray-200">
                Bylaw 5M2004
              </span>
              <span className="text-xs text-gray-600 bg-gray-100 px-3 py-1 rounded-full border border-gray-200">
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
          <div className="flex gap-1 bg-white border border-gray-200 p-1 rounded-xl shadow-sm w-fit">
            <button
              onClick={() => setActiveTab('estimate')}
              className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'estimate'
                  ? 'bg-amber-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }`}
            >
              Parametric Estimate
            </button>
            <button
              onClick={() => setActiveTab('boq')}
              className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'boq'
                  ? 'bg-amber-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }`}
            >
              Bill of Quantities
            </button>
            <button
              onClick={() => setActiveTab('prices')}
              className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'prices'
                  ? 'bg-emerald-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }`}
            >
              Price Database
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
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 shadow-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Panel */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm ${
                  activeTab === 'prices' ? 'bg-emerald-500 text-white' : 'bg-amber-500 text-white'
                }`}>
                  {activeTab === 'prices' ? '💰' : '📐'}
                </span>
                {activeTab === 'prices' ? 'Price Database' : 'Project Parameters'}
              </h2>

              {activeTab === 'prices' ? (
                <div className="space-y-4">
                  {/* Search */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Search Materials
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={priceSearchQuery}
                        onChange={(e) => setPriceSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handlePriceSearch()}
                        placeholder="Search materials..."
                        className="flex-1 bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 placeholder-gray-400 shadow-sm"
                      />
                      <button
                        onClick={handlePriceSearch}
                        className="px-3 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors shadow-sm"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Category Selector */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-2">
                      Material Categories
                    </label>
                    <div className="space-y-1 max-h-[400px] overflow-y-auto">
                      {materialPrices && Object.entries(materialPrices.materials).map(([key, cat]) => (
                        <button
                          key={key}
                          onClick={() => {
                            setSelectedPriceCategory(key);
                            setSearchResults([]);
                            setPriceSearchQuery('');
                          }}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                            selectedPriceCategory === key
                              ? 'bg-amber-500 text-white shadow-sm'
                              : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                          }`}
                        >
                          <div className="font-medium capitalize">{cat.category}</div>
                          <div className="text-xs opacity-75">
                            {Object.keys(cat.items).length} items
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Last Updated Info */}
                  {materialPrices && (
                    <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                      <div className="text-xs text-gray-500 mb-1">Database Info</div>
                      <div className="text-sm text-amber-700 font-medium">{materialPrices.metadata.title}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        v{materialPrices.metadata.version} • Updated {materialPrices.metadata.last_updated}
                      </div>
                    </div>
                  )}
                </div>
              ) : activeTab === 'estimate' ? (
                <div className="space-y-4">
                  {/* Project Name */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Project Name
                    </label>
                    <input
                      type="text"
                      value={estimateForm.project_name}
                      onChange={(e) => setEstimateForm({ ...estimateForm, project_name: e.target.value })}
                      placeholder="Enter project name for report..."
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 placeholder-gray-400 shadow-sm"
                    />
                  </div>

                  {/* Project Type */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Project Type
                    </label>
                    <select
                      value={estimateForm.project_type}
                      onChange={(e) => setEstimateForm({ ...estimateForm, project_type: e.target.value })}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    >
                      {projectTypes.map((type) => (
                        <option key={type.code} value={type.code}>{type.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Floor Area */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Gross Floor Area (SF)
                    </label>
                    <input
                      type="number"
                      value={estimateForm.gross_floor_area_sf}
                      onChange={(e) => setEstimateForm({ ...estimateForm, gross_floor_area_sf: Number(e.target.value) })}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    />
                  </div>

                  {/* Quality Level */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Quality Level
                    </label>
                    <select
                      value={estimateForm.quality_level}
                      onChange={(e) => setEstimateForm({ ...estimateForm, quality_level: e.target.value })}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    >
                      {qualityLevels.map((level) => (
                        <option key={level.code} value={level.code}>{level.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Number of Floors */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Number of Floors
                    </label>
                    <input
                      type="number"
                      value={estimateForm.num_floors}
                      onChange={(e) => setEstimateForm({ ...estimateForm, num_floors: Number(e.target.value) })}
                      min={1}
                      max={50}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    />
                  </div>

                  {/* Basement Area */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Basement Area (SF)
                    </label>
                    <input
                      type="number"
                      value={estimateForm.basement_area_sf}
                      onChange={(e) => setEstimateForm({ ...estimateForm, basement_area_sf: Number(e.target.value) })}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    />
                  </div>

                  {/* Garage Area */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Garage Area (SF)
                    </label>
                    <input
                      type="number"
                      value={estimateForm.garage_area_sf}
                      onChange={(e) => setEstimateForm({ ...estimateForm, garage_area_sf: Number(e.target.value) })}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    />
                  </div>

                  {/* Contingency */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Contingency (%)
                    </label>
                    <input
                      type="number"
                      value={estimateForm.contingency_percent}
                      onChange={(e) => setEstimateForm({ ...estimateForm, contingency_percent: Number(e.target.value) })}
                      min={0}
                      max={30}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    />
                  </div>

                  {/* Calculate Button */}
                  <button
                    onClick={calculateEstimate}
                    disabled={isLoading}
                    className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                  >
                    {isLoading ? 'Calculating...' : 'Calculate Estimate'}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Project Name */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Project Name
                    </label>
                    <input
                      type="text"
                      value={boqForm.project_name}
                      onChange={(e) => setBoqForm({ ...boqForm, project_name: e.target.value })}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    />
                  </div>

                  {/* Floor Area */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Gross Floor Area (SF)
                    </label>
                    <input
                      type="number"
                      value={boqForm.gross_floor_area_sf}
                      onChange={(e) => setBoqForm({ ...boqForm, gross_floor_area_sf: Number(e.target.value) })}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    {/* Floors */}
                    <div>
                      <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                        Floors
                      </label>
                      <input
                        type="number"
                        value={boqForm.num_floors}
                        onChange={(e) => setBoqForm({ ...boqForm, num_floors: Number(e.target.value) })}
                        min={1}
                        max={4}
                        className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                      />
                    </div>

                    {/* Bedrooms */}
                    <div>
                      <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                        Bedrooms
                      </label>
                      <input
                        type="number"
                        value={boqForm.num_bedrooms}
                        onChange={(e) => setBoqForm({ ...boqForm, num_bedrooms: Number(e.target.value) })}
                        min={1}
                        max={10}
                        className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                      />
                    </div>
                  </div>

                  {/* Bathrooms */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Bathrooms
                    </label>
                    <input
                      type="number"
                      value={boqForm.num_bathrooms}
                      onChange={(e) => setBoqForm({ ...boqForm, num_bathrooms: Number(e.target.value) })}
                      min={1}
                      max={6}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                    />
                  </div>

                  {/* Basement Toggle */}
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-600">Has Basement</label>
                    <button
                      onClick={() => setBoqForm({ ...boqForm, has_basement: !boqForm.has_basement })}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        boqForm.has_basement ? 'bg-amber-500' : 'bg-gray-300'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-full bg-white shadow transform transition-transform ${
                        boqForm.has_basement ? 'translate-x-6' : 'translate-x-0.5'
                      }`} />
                    </button>
                  </div>

                  {boqForm.has_basement && (
                    <div>
                      <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                        Basement Area (SF)
                      </label>
                      <input
                        type="number"
                        value={boqForm.basement_area_sf}
                        onChange={(e) => setBoqForm({ ...boqForm, basement_area_sf: Number(e.target.value) })}
                        className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 font-mono focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
                      />
                    </div>
                  )}

                  {/* Quality */}
                  <div>
                    <label className="block text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Quality Level
                    </label>
                    <select
                      value={boqForm.quality_level}
                      onChange={(e) => setBoqForm({ ...boqForm, quality_level: e.target.value })}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-800 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm"
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
                    className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                  >
                    {isLoading ? 'Generating...' : 'Generate BOQ'}
                  </button>
                </div>
              )}
            </div>

            {/* Calgary Standards Reference - hidden for prices tab */}
            {activeTab !== 'prices' && (
              <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Calgary Permit Fees</h3>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between text-gray-600">
                    <span>Building Permit</span>
                    <span className="font-mono text-amber-600 font-medium">$10.14 / $1,000</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Trade Permits</span>
                    <span className="font-mono text-amber-600 font-medium">$9.79 / $1,000</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Minimum Fee</span>
                    <span className="font-mono text-amber-600 font-medium">$114.00</span>
                  </div>
                </div>
              </div>
            )}
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
                <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">Cost Breakdown by CSI Division</h3>
                  <DivisionBarChart breakdown={estimateResult.division_breakdown} />
                </div>

                {/* Detailed Costs */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">Cost Analysis</h3>
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
                  <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Location Factor</div>
                    <div className="text-2xl font-mono text-amber-600 mt-1">
                      {estimateResult.location_factor.toFixed(2)}x
                    </div>
                    <div className="text-xs text-gray-500">Calgary base</div>
                  </div>
                  <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Inflation Factor</div>
                    <div className="text-2xl font-mono text-amber-600 mt-1">
                      {estimateResult.inflation_factor.toFixed(3)}x
                    </div>
                    <div className="text-xs text-gray-500">2024 adjustment</div>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'boq' && boqResult && (
              <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">{boqResult.project_name}</h3>
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

            {/* Price Database Panel */}
            {activeTab === 'prices' && (
              <div className="space-y-6">
                {pricesLoading ? (
                  <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
                    <div className="flex flex-col items-center gap-4">
                      <svg className="animate-spin h-10 w-10 text-amber-500" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      <p className="text-gray-500">Loading material prices...</p>
                    </div>
                  </div>
                ) : materialPrices ? (
                  <>
                    {/* Search Results */}
                    {searchResults.length > 0 && (
                      <div className="bg-amber-50 rounded-xl border border-amber-200 p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold text-amber-700">
                            Search Results ({searchResults.length} items)
                          </h3>
                          <button
                            onClick={() => {
                              setSearchResults([]);
                              setPriceSearchQuery('');
                            }}
                            className="text-xs text-gray-500 hover:text-gray-700"
                          >
                            Clear Results
                          </button>
                        </div>
                        <div className="space-y-2">
                          {searchResults.map((result, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 shadow-sm">
                              <div>
                                <div className="text-gray-800">{result.description}</div>
                                <div className="text-xs text-gray-500">
                                  {result.category} • {result.unit} • Source: {result.source}
                                </div>
                              </div>
                              <div className="text-amber-600 font-mono text-lg font-semibold">
                                ${result.price.toFixed(2)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Live Price Sync Status */}
                    <div className="bg-white rounded-xl border border-emerald-200 p-6 shadow-sm">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                          <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Live Price Sources
                        </h3>
                        {isAdmin && (
                          <button
                            onClick={() => handleRefreshPrices()}
                            disabled={isRefreshing}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                              isRefreshing
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-sm'
                            }`}
                          >
                            <svg
                              className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`}
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            {isRefreshing ? 'Refreshing...' : 'Refresh Prices'}
                          </button>
                        )}
                      </div>

                      {/* Refresh Message */}
                      {refreshMessage && (
                        <div className={`mb-4 p-3 rounded-lg text-sm ${
                          refreshMessage.type === 'success'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-red-50 text-red-700 border border-red-200'
                        }`}>
                          {refreshMessage.text}
                        </div>
                      )}

                      {/* Sync Status Grid */}
                      {syncStatus && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                          {Object.entries(syncStatus).map(([key, status]) => (
                            <div
                              key={key}
                              className={`p-3 rounded-lg border ${
                                status.cache_valid
                                  ? 'bg-emerald-50 border-emerald-200'
                                  : 'bg-yellow-50 border-yellow-200'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <div className={`w-2 h-2 rounded-full ${status.cache_valid ? 'bg-emerald-500' : 'bg-yellow-500'}`} />
                                  <span className="font-medium text-gray-800 uppercase text-sm">{status.source_name}</span>
                                </div>
                                {isAdmin && (
                                  <button
                                    onClick={() => handleRefreshPrices(key)}
                                    disabled={isRefreshing}
                                    className="text-xs text-gray-500 hover:text-emerald-600 transition-colors disabled:opacity-50"
                                  >
                                    Refresh
                                  </button>
                                )}
                              </div>
                              <div className="text-xs text-gray-500 mt-1">
                                {status.last_sync ? (
                                  <>Last sync: {new Date(status.last_sync).toLocaleDateString()} {new Date(status.last_sync).toLocaleTimeString()}</>
                                ) : (
                                  'Never synced'
                                )}
                              </div>
                              <div className="text-xs text-gray-400 mt-0.5">
                                Cache TTL: {status.cache_ttl_hours}h • {status.cache_valid ? 'Valid' : 'Stale'}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Scheduled Jobs */}
                      {scheduledJobs.length > 0 && (
                        <div className="border-t border-gray-200 pt-4 mt-4">
                          <h4 className="text-sm font-medium text-gray-600 mb-2">Scheduled Updates</h4>
                          <div className="space-y-1">
                            {scheduledJobs.map((job) => (
                              <div key={job.id} className="flex items-center justify-between text-xs">
                                <span className="text-gray-600">{job.name}</span>
                                <span className="text-gray-500">
                                  Next: {job.next_run ? new Date(job.next_run).toLocaleDateString() : 'Not scheduled'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Price Sources Reference */}
                    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                        Price Data Sources
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {Object.entries(materialPrices.price_sources).map(([key, source]) => (
                          <div key={key} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                            <div className="flex items-start justify-between">
                              <div>
                                <div className="font-medium text-gray-800">{source.name}</div>
                                <div className="text-xs text-gray-500 mt-1">
                                  {source.reliability} reliability • {source.update_frequency}
                                </div>
                              </div>
                              {source.url && (
                                <a
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-amber-600 hover:text-amber-700 transition-colors"
                                >
                                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                  </svg>
                                </a>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Material Prices Table */}
                    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-800 capitalize">
                          {materialPrices.materials[selectedPriceCategory]?.category || selectedPriceCategory} Materials
                        </h3>
                        <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-lg border border-gray-200">
                          2025/2026 Calgary Prices (CAD)
                        </span>
                      </div>

                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 text-gray-600">
                            <tr>
                              <th className="text-left p-3">Description</th>
                              <th className="text-center p-3 w-20">Unit</th>
                              <th className="text-right p-3 w-28">Price</th>
                              <th className="text-right p-3 w-36">Range</th>
                              <th className="text-center p-3 w-32">Source</th>
                              <th className="text-center p-3 w-28">Updated</th>
                              <th className="text-center p-3 w-16">Edit</th>
                            </tr>
                          </thead>
                          <tbody>
                            {materialPrices.materials[selectedPriceCategory] &&
                              Object.entries(materialPrices.materials[selectedPriceCategory].items).map(([itemId, item]) => (
                                <tr key={itemId} className="border-t border-gray-100 hover:bg-gray-50">
                                  <td className="p-3 text-gray-800">
                                    {item.description}
                                    {item.notes && (
                                      <div className="text-xs text-gray-500 mt-1">{item.notes}</div>
                                    )}
                                  </td>
                                  <td className="p-3 text-center text-gray-500 uppercase text-xs">{item.unit}</td>
                                  <td className="p-3 text-right">
                                    {editingPrice?.category === selectedPriceCategory && editingPrice?.itemId === itemId ? (
                                      <input
                                        type="number"
                                        value={editingPrice.value}
                                        onChange={(e) => setEditingPrice({ ...editingPrice, value: e.target.value })}
                                        className="w-24 bg-white border border-amber-500 rounded px-2 py-1 text-amber-600 font-mono text-right focus:outline-none focus:ring-2 focus:ring-amber-500/20"
                                        autoFocus
                                      />
                                    ) : (
                                      <span className="text-amber-600 font-mono font-semibold">${item.price.toFixed(2)}</span>
                                    )}
                                  </td>
                                  <td className="p-3 text-right text-gray-500 font-mono text-xs">
                                    ${item.price_range.low.toFixed(2)} - ${item.price_range.high.toFixed(2)}
                                  </td>
                                  <td className="p-3 text-center">
                                    <span className="text-xs px-2 py-1 rounded-lg bg-gray-100 text-gray-600 border border-gray-200">
                                      {item.source}
                                    </span>
                                  </td>
                                  <td className="p-3 text-center text-gray-500 text-xs">{item.last_updated}</td>
                                  <td className="p-3 text-center">
                                    {editingPrice?.category === selectedPriceCategory && editingPrice?.itemId === itemId ? (
                                      <div className="flex gap-1 justify-center">
                                        <button
                                          onClick={() => handlePriceUpdate(selectedPriceCategory, itemId, parseFloat(editingPrice.value))}
                                          className="p-1 text-emerald-500 hover:text-emerald-600"
                                        >
                                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                          </svg>
                                        </button>
                                        <button
                                          onClick={() => setEditingPrice(null)}
                                          className="p-1 text-red-500 hover:text-red-600"
                                        >
                                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                          </svg>
                                        </button>
                                      </div>
                                    ) : (
                                      <button
                                        onClick={() => setEditingPrice({
                                          category: selectedPriceCategory,
                                          itemId,
                                          value: item.price.toString()
                                        })}
                                        className="p-1 text-gray-400 hover:text-amber-600 transition-colors"
                                      >
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                        </svg>
                                      </button>
                                    )}
                                  </td>
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Labor Rates */}
                    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        2025 Calgary Labor Rates
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {Object.entries(materialPrices.labor_rates).map(([trade, data]) => (
                          <div key={trade} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between">
                              <span className="text-gray-700 capitalize">{trade.replace(/_/g, ' ')}</span>
                              <span className="text-blue-600 font-mono font-semibold">${data.rate}/hr</span>
                            </div>
                            <div className="text-xs text-gray-500 mt-1">{data.notes}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Market Trends */}
                    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                        2025 Market Trends
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(materialPrices.market_trends).map(([material, data]) => (
                          <div key={material} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-gray-800 font-medium capitalize">{material}</span>
                              <span className={`text-sm font-mono ${
                                data.change_ytd_percent > 0 ? 'text-red-500' :
                                data.change_ytd_percent < 0 ? 'text-emerald-500' : 'text-gray-500'
                              }`}>
                                {data.change_ytd_percent > 0 ? '+' : ''}{data.change_ytd_percent}% YTD
                              </span>
                            </div>
                            <div className="text-sm text-gray-600">{data.trend}</div>
                            <div className="text-xs text-gray-500 mt-2">
                              <span className="text-amber-600 font-medium">2026 Forecast:</span> {data.forecast_2026}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">Source: {data.source}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
                    <div className="text-6xl mb-4">💰</div>
                    <h3 className="text-xl text-gray-700 mb-2">Price Database</h3>
                    <p className="text-gray-500">
                      Failed to load material prices. Please try again.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Empty State */}
            {((activeTab === 'estimate' && !estimateResult) || (activeTab === 'boq' && !boqResult)) && activeTab !== 'prices' && (
              <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-xl text-gray-700 mb-2">
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
