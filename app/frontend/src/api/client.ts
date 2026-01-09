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
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || `HTTP ${response.status}`);
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

export { ApiError };
