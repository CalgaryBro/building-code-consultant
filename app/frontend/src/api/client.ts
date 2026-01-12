/**
 * API Client for Calgary Building Code Expert System
 */

// Use relative path for proxy in development, or full URL if VITE_API_URL is set
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const config: RequestInit = {
    ...options,
    credentials: 'include', // Include cookies for session management
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

    // Handle FastAPI validation errors (array of objects)
    let errorMessage: string;
    if (Array.isArray(error.detail)) {
      // Format validation errors: "field: message"
      errorMessage = error.detail
        .map((e: { loc?: string[]; msg?: string }) => {
          const field = e.loc?.slice(-1)[0] || 'field';
          return `${field}: ${e.msg || 'Invalid value'}`;
        })
        .join(', ');
    } else if (typeof error.detail === 'string') {
      errorMessage = error.detail;
    } else if (error.detail?.message) {
      errorMessage = error.detail.message;
    } else {
      errorMessage = `HTTP ${response.status}`;
    }

    throw new ApiError(response.status, errorMessage);
  }

  return response.json();
}

// --- EXPLORE Mode API ---
export const exploreApi = {
  // List all codes
  listCodes: (params?: { code_type?: string; current_only?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.code_type) searchParams.set('code_type', params.code_type);
    if (params?.current_only !== undefined) searchParams.set('current_only', String(params.current_only));
    return request<import('../types').Code[]>(`/explore/codes?${searchParams}`);
  },

  // Get specific code
  getCode: (codeId: string) => {
    return request<import('../types').Code>(`/explore/codes/${codeId}`);
  },

  // List articles for a code
  listArticles: (codeId: string, params?: { part_number?: number; division_number?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.part_number) searchParams.set('part_number', String(params.part_number));
    if (params?.division_number) searchParams.set('division_number', String(params.division_number));
    return request<import('../types').Article[]>(`/explore/codes/${codeId}/articles?${searchParams}`);
  },

  // Get specific article
  getArticle: (articleId: string) => {
    return request<import('../types').Article>(`/explore/articles/${articleId}`);
  },

  // Get article requirements
  getArticleRequirements: (articleId: string) => {
    return request<import('../types').Requirement[]>(`/explore/articles/${articleId}/requirements`);
  },

  // Search codes
  search: (query: import('../types').CodeSearchQuery) => {
    return request<import('../types').CodeSearchResponse>('/explore/search', {
      method: 'POST',
      body: JSON.stringify(query),
    });
  },

  // Search requirements
  searchRequirements: (params?: {
    element?: string;
    requirement_type?: string;
    occupancy_group?: string;
    part_9_only?: boolean;
    verified_only?: boolean;
    limit?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.element) searchParams.set('element', params.element);
    if (params?.requirement_type) searchParams.set('requirement_type', params.requirement_type);
    if (params?.occupancy_group) searchParams.set('occupancy_group', params.occupancy_group);
    if (params?.part_9_only) searchParams.set('part_9_only', 'true');
    if (params?.verified_only) searchParams.set('verified_only', 'true');
    if (params?.limit) searchParams.set('limit', String(params.limit));
    return request<import('../types').Requirement[]>(`/explore/requirements?${searchParams}`);
  },

  // Browse code structure
  browseStructure: (codeType: string) => {
    return request<{
      code: { id: string; name: string; short_name: string; version: string };
      parts: { part_number: number; title?: string; article_count: number }[];
    }>(`/explore/browse/${codeType}`);
  },

  // Get related Standata bulletins for an article
  getRelatedStandata: (articleNumber: string) => {
    return request<import('../types').StandataByCodeResponse>(
      `/explore/articles/${encodeURIComponent(articleNumber)}/related-standata`
    );
  },

  // List all Standata bulletins
  listStandata: (params?: { category?: string; search?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set('category', params.category);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    return request<import('../types').StandataSummary[]>(`/explore/standata?${searchParams}`);
  },

  // Get full Standata bulletin details
  getStandataBulletin: (bulletinNumber: string) => {
    return request<import('../types').StandataDetail>(
      `/explore/standata/${encodeURIComponent(bulletinNumber)}`
    );
  },
};

// --- Zones API ---
export const zonesApi = {
  // List zones
  listZones: (category?: string) => {
    const searchParams = new URLSearchParams();
    if (category) searchParams.set('category', category);
    return request<import('../types').ZoneSummary[]>(`/zones/zones?${searchParams}`);
  },

  // Get zone by code
  getZone: (zoneCode: string) => {
    return request<import('../types').Zone>(`/zones/zones/${zoneCode}`);
  },

  // Get zone rules
  getZoneRules: (zoneCode: string, ruleType?: string) => {
    const searchParams = new URLSearchParams();
    if (ruleType) searchParams.set('rule_type', ruleType);
    return request<import('../types').ZoneRule[]>(`/zones/zones/${zoneCode}/rules?${searchParams}`);
  },

  // Search parcels
  searchParcels: (query: string, community?: string, limit?: number) => {
    const searchParams = new URLSearchParams({ query });
    if (community) searchParams.set('community', community);
    if (limit) searchParams.set('limit', String(limit));
    return request<import('../types').ParcelSearchResult[]>(`/zones/parcels/search?${searchParams}`);
  },

  // Get parcel by ID
  getParcel: (parcelId: string) => {
    return request<import('../types').Parcel>(`/zones/parcels/${parcelId}`);
  },

  // Check zoning compliance
  checkZoning: (data: import('../types').ZoningCheckRequest) => {
    return request<import('../types').ZoningCheckResponse>('/zones/check-zoning', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // List communities
  listCommunities: (quadrant?: string) => {
    const searchParams = new URLSearchParams();
    if (quadrant) searchParams.set('quadrant', quadrant);
    return request<{ community_name: string; community_code: string; quadrant: string; parcel_count: number }[]>(
      `/zones/communities?${searchParams}`
    );
  },
};

// --- GUIDE Mode API ---
export const guideApi = {
  // Analyze project
  analyze: (data: import('../types').GuideProjectInput) => {
    return request<import('../types').GuideResponse>('/guide/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // List projects
  listProjects: (status?: string, limit?: number) => {
    const searchParams = new URLSearchParams();
    if (status) searchParams.set('status', status);
    if (limit) searchParams.set('limit', String(limit));
    return request<import('../types').Project[]>(`/guide/projects?${searchParams}`);
  },

  // Get project
  getProject: (projectId: string) => {
    return request<import('../types').Project>(`/guide/projects/${projectId}`);
  },

  // Get classification explanation
  getClassificationInfo: () => {
    return request<{
      overview: string;
      part_9: { name: string; applies_to: string[]; benefits: string[] };
      part_3: { name: string; applies_to: string[]; requirements: string[] };
    }>('/guide/classification');
  },
};

// --- REVIEW Mode API ---
export const reviewApi = {
  // Upload document
  uploadDocument: async (projectId: string, file: File, documentType?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (documentType) formData.append('document_type', documentType);

    const url = `${API_BASE_URL}/review/projects/${projectId}/documents`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new ApiError(response.status, error.detail);
    }

    return response.json() as Promise<import('../types').Document>;
  },

  // List documents
  listDocuments: (projectId: string) => {
    return request<import('../types').Document[]>(`/review/projects/${projectId}/documents`);
  },

  // Start extraction
  startExtraction: (documentId: string) => {
    return request<{ message: string; document_id: string; status: string }>(
      `/review/documents/${documentId}/extract`,
      { method: 'POST' }
    );
  },

  // Get extraction status
  getExtractionStatus: (documentId: string) => {
    return request<{
      document_id: string;
      status: string;
      started_at?: string;
      completed_at?: string;
      error?: string;
      extracted_values_count: number;
    }>(`/review/documents/${documentId}/extraction-status`);
  },

  // Get extracted data
  getExtractedData: (documentId: string, verifiedOnly?: boolean) => {
    const searchParams = new URLSearchParams();
    if (verifiedOnly) searchParams.set('verified_only', 'true');
    return request<import('../types').ExtractedData[]>(`/review/documents/${documentId}/extracted?${searchParams}`);
  },

  // Verify extracted data
  verifyExtractedData: (extractedId: string, data: { verified_value: string; verified_by: string; verification_notes?: string }) => {
    return request<import('../types').ExtractedData>(`/review/extracted/${extractedId}/verify`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Run compliance checks
  runChecks: (projectId: string, checkCategories?: string[], useUnverified?: boolean) => {
    const searchParams = new URLSearchParams();
    if (checkCategories?.length) searchParams.set('check_categories', checkCategories.join(','));
    if (useUnverified) searchParams.set('use_unverified', 'true');
    return request<import('../types').ReviewSummary>(`/review/projects/${projectId}/run-checks?${searchParams}`, {
      method: 'POST',
    });
  },

  // Get project checks
  getProjectChecks: (projectId: string, category?: string, status?: string) => {
    const searchParams = new URLSearchParams();
    if (category) searchParams.set('category', category);
    if (status) searchParams.set('status', status);
    return request<import('../types').ComplianceCheck[]>(`/review/projects/${projectId}/checks?${searchParams}`);
  },
};

// --- PERMITS API ---
export const permitsApi = {
  // Create new permit application
  createApplication: (data: import('../types').CreatePermitApplicationInput) => {
    return request<import('../types').PermitApplication>('/permits/applications', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // List applications with filtering/pagination
  listApplications: (params?: import('../types').PermitApplicationsListParams) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.permit_type) searchParams.set('permit_type', params.permit_type);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    return request<import('../types').PaginatedResponse<import('../types').PermitApplication>>(
      `/permits/applications?${searchParams}`
    );
  },

  // Get application details
  getApplication: (id: string) => {
    return request<import('../types').PermitApplication>(`/permits/applications/${id}`);
  },

  // Update application
  updateApplication: (id: string, data: import('../types').UpdatePermitApplicationInput) => {
    return request<import('../types').PermitApplication>(`/permits/applications/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  // Submit for review
  submitApplication: (id: string) => {
    return request<import('../types').PermitApplication>(`/permits/applications/${id}/submit`, {
      method: 'POST',
    });
  },

  // Update status
  updateStatus: (id: string, status: import('../types').PermitStatus, notes?: string) => {
    return request<import('../types').PermitApplication>(`/permits/applications/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ status, notes }),
    });
  },

  // Get timeline
  getTimeline: (id: string) => {
    return request<import('../types').PermitTimelineEvent[]>(`/permits/applications/${id}/timeline`);
  },

  // Upload document
  uploadDocument: async (id: string, file: File, documentType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const url = `${API_BASE_URL}/permits/applications/${id}/documents`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new ApiError(response.status, error.detail);
    }

    return response.json() as Promise<import('../types').PermitDocument>;
  },

  // List documents
  listDocuments: (id: string) => {
    return request<import('../types').PermitDocument[]>(`/permits/applications/${id}/documents`);
  },

  // Remove document
  removeDocument: (applicationId: string, documentId: string) => {
    return request<{ message: string }>(`/permits/applications/${applicationId}/documents/${documentId}`, {
      method: 'DELETE',
    });
  },

  // Record deficiency
  recordDeficiency: (id: string, data: {
    deficiency_type: string;
    description: string;
    code_reference?: string;
    severity: 'critical' | 'major' | 'minor';
  }) => {
    return request<import('../types').PermitDeficiency>(`/permits/applications/${id}/deficiencies`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // List deficiencies
  listDeficiencies: (id: string) => {
    return request<import('../types').PermitDeficiency[]>(`/permits/applications/${id}/deficiencies`);
  },

  // List comments
  listComments: (id: string) => {
    return request<import('../types').PermitComment[]>(`/permits/applications/${id}/comments`);
  },

  // Get statistics
  getStatistics: () => {
    return request<import('../types').PermitStatistics>('/permits/statistics');
  },

  // Get valid document types
  getDocumentTypes: () => {
    return request<string[]>('/permits/document-types');
  },

  // Get upload constraints
  getUploadConstraints: () => {
    return request<{
      max_file_size_mb: number;
      allowed_extensions: string[];
      max_files_per_application: number;
    }>('/permits/upload-constraints');
  },
};

// --- Fees API ---
export interface FeeBreakdown {
  processing_fee: number;
  base_fee: number;
  scc_fee: number;
  subtotal: number;
  gst: number;
  total: number;
  notes: string[];
}

export interface BuildingPermitFeeResponse {
  building_type: string;
  construction_value: number;
  fee_breakdown: FeeBreakdown;
  includes_trade_permits: boolean;
  work_started_multiplier: number;
}

export interface TradePermitFeeResponse {
  trades: Array<{
    trade_type: string;
    construction_value: number;
    fee_breakdown: FeeBreakdown;
  }>;
  combined_total: number;
  work_started_multiplier: number;
}

export interface ProjectFeeEstimateResponse {
  project_name: string;
  development_permit?: {
    required: boolean;
    estimated_fee: number;
    notes: string[];
  };
  building_permit: BuildingPermitFeeResponse;
  trade_permits?: TradePermitFeeResponse;
  lot_grading?: {
    fee: number;
    notes: string;
  };
  additional_fees: Array<{
    fee_type: string;
    amount: number;
    description: string;
  }>;
  subtotal: number;
  gst: number;
  grand_total: number;
  fee_schedule_version: string;
  disclaimer: string;
}

export const feesApi = {
  // Get complete project fee estimate
  estimateProjectFees: (data: {
    project_name?: string;
    project_type: string;
    building_type: string;
    construction_value: number;
    floor_area_sqm?: number;
    dwelling_units?: number;
    requires_development_permit?: boolean;
    requires_building_permit?: boolean;
    include_lot_grading?: boolean;
    work_started_without_permit?: boolean;
  }) => {
    return request<ProjectFeeEstimateResponse>('/fees/estimate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Get building permit fee
  calculateBuildingPermitFee: (data: {
    building_type: string;
    construction_value?: number;
    floor_area_sqm?: number;
    alteration_type?: string;
    dwelling_units?: number;
    work_started_without_permit?: boolean;
  }) => {
    return request<BuildingPermitFeeResponse>('/fees/building-permit', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Get quick estimate
  quickEstimate: (data: {
    building_type: string;
    construction_value: number;
  }) => {
    return request<{
      building_permit_fee: number;
      trade_permit_fee: number | null;
      total_estimate: number;
      notes: string[];
    }>('/fees/quick-estimate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Get fee schedule
  getFeeSchedule: () => {
    return request<{
      building_permits: Record<string, unknown>;
      trade_permits: Record<string, unknown>;
      additional_fees: Record<string, unknown>;
      policies: Record<string, unknown>;
      effective_date: string;
      version: string;
    }>('/fees/schedule');
  },

  // Get building types
  getBuildingTypes: () => {
    return request<{
      residential: Array<{ value: string; label: string }>;
      multi_family: Array<{ value: string; label: string }>;
      commercial: Array<{ value: string; label: string }>;
      other: Array<{ value: string; label: string }>;
    }>('/fees/building-types');
  },

  // Get alteration types
  getAlterationTypes: () => {
    return request<{
      alterations: Array<{
        value: string;
        label: string;
        total_fee: number;
      }>;
    }>('/fees/alteration-types');
  },
};

// --- Public API (Rate Limited) ---
export const publicApi = {
  // Get rate limit status
  getRateLimitStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/public/rate-limit-status`, {
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, error.detail);
    }

    return response.json() as Promise<{
      ip_address: string;
      queries_used: number;
      queries_remaining: number;
      daily_limit: number;
      resets_at: string;
    }>;
  },

  // Public explore search (rate limited)
  search: async (query: import('../types').CodeSearchQuery) => {
    const response = await fetch(`${API_BASE_URL}/public/explore`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });

    // Get rate limit info from headers
    const queriesRemaining = response.headers.get('X-Queries-Remaining');
    const dailyLimit = response.headers.get('X-Daily-Limit');

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

      // Handle rate limit exceeded
      if (response.status === 429) {
        return {
          error: true,
          rateLimitExceeded: true,
          message: error.detail?.message || 'Daily query limit exceeded',
          queriesRemaining: 0,
          upgradeUrl: error.detail?.upgrade_url || '/signup',
        };
      }

      throw new ApiError(response.status, error.detail);
    }

    const data = await response.json();

    return {
      ...data,
      queriesRemaining: queriesRemaining ? parseInt(queriesRemaining, 10) : null,
      dailyLimit: dailyLimit ? parseInt(dailyLimit, 10) : null,
      error: false,
      rateLimitExceeded: false,
    };
  },

  // Get sample questions
  getSampleQuestions: () => {
    return request<{
      questions: {
        question: string;
        category: string;
        code_type: string;
      }[];
      cta: {
        message: string;
        url: string;
        benefits: string[];
      };
    }>('/public/sample-questions');
  },
};

// --- ADDRESSES API ---
export interface AddressAutocompleteResult {
  address: string;
  community: string | null;
  zone_code: string | null;
  parcel_id: string | null;
  latitude: number | null;
  longitude: number | null;
}

export const addressesApi = {
  // Address autocomplete
  autocomplete: (query: string, limit?: number) => {
    const searchParams = new URLSearchParams({ q: query });
    if (limit) searchParams.set('limit', String(limit));
    return request<AddressAutocompleteResult[]>(`/addresses/autocomplete?${searchParams}`);
  },

  // Advanced address search
  search: (query: string, params?: { community?: string; zone?: string; limit?: number }) => {
    const searchParams = new URLSearchParams({ query });
    if (params?.community) searchParams.set('community', params.community);
    if (params?.zone) searchParams.set('zone', params.zone);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    return request<AddressAutocompleteResult[]>(`/addresses/search?${searchParams}`);
  },
};

// --- Chat API ---
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ContextItem {
  source_type: string;
  source_id: string;
  source_title: string;
  source_reference: string;
  excerpt: string;
  relevance_score: number;
  search_type?: string;  // 'vector' | 'keyword' | 'both'
  citation_number?: number;  // [1], [2], etc.
}

export interface Reference {
  number: number;  // [1], [2], etc.
  source_type: string;  // 'article' | 'standata' | 'guide'
  reference: string;  // e.g., "ABC 9.25.3.1" or "STANDATA 05-BCI-001"
  title: string;  // Title of the source
  source_id: string;  // UUID for linking
}

export interface ChatResponse {
  answer: string;
  answer_with_citations: string;  // Answer with [1], [2] markers
  sources: ContextItem[];
  references: Reference[];  // Formatted reference list
  search_query: string;
  search_method: string;  // 'hybrid' | 'keyword' | 'vector'
  llm_available: boolean;
  disclaimer: string;
}

export interface SuggestedQuestion {
  name: string;
  questions: string[];
}

export const chatApi = {
  // Ask a question
  ask: (message: string, options?: { include_standata?: boolean; include_guides?: boolean; max_context_items?: number }) => {
    return request<ChatResponse>('/chat/ask', {
      method: 'POST',
      body: JSON.stringify({
        message,
        include_standata: options?.include_standata ?? true,
        include_guides: options?.include_guides ?? true,
        max_context_items: options?.max_context_items ?? 5,
      }),
    });
  },

  // Get suggested questions
  getSuggestedQuestions: () => {
    return request<{ categories: SuggestedQuestion[] }>('/chat/suggested-questions');
  },
};

export { ApiError };
