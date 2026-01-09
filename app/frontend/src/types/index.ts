// API Types for Calgary Building Code Expert System

// --- Code Types ---
export interface Code {
  id: string;
  code_type: string;
  name: string;
  short_name: string;
  version: string;
  jurisdiction: string;
  effective_date: string;
  expiry_date?: string;
  source_url?: string;
  is_current: boolean;
  created_at: string;
}

export interface Article {
  id: string;
  code_id: string;
  article_number: string;
  title?: string;
  full_text: string;
  parent_article_id?: string;
  part_number?: number;
  division_number?: number;
  section_number?: number;
  page_number?: number;
  created_at: string;
  updated_at: string;
}

export interface ArticleSearchResult {
  id: string;
  article_number: string;
  title?: string;
  full_text: string;
  code_short_name: string;
  code_version: string;
  relevance_score?: number;
  highlight?: string;
}

export interface Requirement {
  id: string;
  article_id: string;
  requirement_type: string;
  element: string;
  description?: string;
  min_value?: number;
  max_value?: number;
  exact_value?: string;
  unit?: string;
  exact_quote: string;
  is_mandatory: boolean;
  applies_to_part_9: boolean;
  applies_to_part_3: boolean;
  occupancy_groups?: string[];
  extraction_method: string;
  extraction_confidence?: string;
  is_verified: boolean;
  verified_by?: string;
  verified_date?: string;
  created_at: string;
}

// --- Zone Types ---
export interface Zone {
  id: string;
  zone_code: string;
  zone_name: string;
  category: string;
  district?: string;
  description?: string;
  bylaw_url?: string;
  max_height_m?: number;
  max_storeys?: number;
  max_far?: number;
  min_front_setback_m?: number;
  min_side_setback_m?: number;
  min_rear_setback_m?: number;
  min_parking_stalls?: number;
  rules?: ZoneRule[];
  created_at: string;
  updated_at: string;
}

export interface ZoneRule {
  id: string;
  rule_type: string;
  description?: string;
  min_value?: number;
  max_value?: number;
  unit?: string;
  calculation_formula?: string;
  conditions?: Record<string, unknown>;
  exceptions?: string;
  bylaw_reference?: string;
}

export interface Parcel {
  id: string;
  address: string;
  street_name?: string;
  street_type?: string;
  street_direction?: string;
  house_number?: string;
  unit_number?: string;
  community_name?: string;
  community_code?: string;
  quadrant?: string;
  postal_code?: string;
  land_use_designation?: string;
  legal_description?: string;
  roll_number?: string;
  area_sqm?: number;
  frontage_m?: number;
  depth_m?: number;
  latitude?: number;
  longitude?: number;
  zone_id?: string;
  zone?: ZoneSummary;
  created_at: string;
  updated_at: string;
}

export interface ZoneSummary {
  id: string;
  zone_code: string;
  zone_name: string;
  category: string;
}

export interface ParcelSearchResult {
  id: string;
  address: string;
  community_name?: string;
  land_use_designation?: string;
  zone_code?: string;
  zone_name?: string;
  latitude?: number;
  longitude?: number;
}

// --- Project Types ---
export interface Project {
  id: string;
  project_name?: string;
  description?: string;
  address: string;
  parcel_id?: string;
  classification?: string;
  occupancy_group?: string;
  construction_type?: string;
  building_height_storeys?: number;
  building_height_m?: number;
  building_area_sqm?: number;
  footprint_area_sqm?: number;
  dwelling_units?: number;
  project_type?: string;
  development_permit_required?: boolean;
  building_permit_required?: boolean;
  estimated_permit_fee?: number;
  status: string;
  overall_compliance?: string;
  created_at: string;
  updated_at: string;
}

export interface ComplianceCheck {
  id: string;
  project_id: string;
  requirement_id?: string;
  check_category: string;
  check_name: string;
  element?: string;
  required_value?: string;
  actual_value?: string;
  unit?: string;
  status: 'pass' | 'fail' | 'warning' | 'needs_review';
  message?: string;
  code_reference?: string;
  extraction_confidence?: string;
  is_verified: boolean;
  created_at: string;
}

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  file_path: string;
  file_type?: string;
  file_size_bytes?: number;
  document_type?: string;
  extraction_status: string;
  extraction_started_at?: string;
  extraction_completed_at?: string;
  extraction_error?: string;
  created_at: string;
}

export interface ExtractedData {
  id: string;
  document_id: string;
  field_name: string;
  field_category?: string;
  value_raw?: string;
  value_numeric?: number;
  unit?: string;
  page_number?: number;
  location_description?: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'NOT_FOUND';
  extraction_notes?: string;
  is_verified: boolean;
  verified_value?: string;
  verified_by?: string;
  verified_at?: string;
  created_at: string;
}

// --- Guide Mode Types ---
export interface GuideProjectInput {
  address: string;
  project_type: string;
  occupancy_type: string;
  building_height_storeys?: number;
  building_area_sqm?: number;
  footprint_area_sqm?: number;
  dwelling_units?: number;
  description?: string;
}

export interface PermitRequirement {
  permit_type: string;
  required: boolean;
  description: string;
  estimated_fee?: number;
  typical_timeline_days?: number;
  documents_required: string[];
  notes?: string;
}

export interface GuideResponse {
  project: Project;
  classification: string;
  classification_reason: string;
  zoning_status: string;
  permits_required: PermitRequirement[];
  key_requirements: string[];
  next_steps: string[];
  warnings: string[];
}

// --- Zoning Check Types ---
export interface ZoningCheckRequest {
  parcel_id?: string;
  address?: string;
  building_height_m?: number;
  building_storeys?: number;
  building_area_sqm?: number;
  floor_area_ratio?: number;
  front_setback_m?: number;
  side_setback_m?: number;
  rear_setback_m?: number;
  parking_stalls?: number;
}

export interface ZoningCheckResult {
  check_name: string;
  rule_type: string;
  required_value?: string;
  proposed_value?: string;
  status: 'pass' | 'fail' | 'warning' | 'needs_review';
  message?: string;
  bylaw_reference?: string;
}

export interface ZoningCheckResponse {
  parcel: Parcel;
  zone: Zone;
  checks: ZoningCheckResult[];
  overall_status: string;
  summary: string;
}

// --- Search Types ---
export interface CodeSearchQuery {
  query: string;
  code_types?: string[];
  part_numbers?: number[];
  limit?: number;
  use_semantic?: boolean;
}

export interface CodeSearchResponse {
  query: string;
  total_results: number;
  results: ArticleSearchResult[];
  search_type: string;
}

// --- Review Summary ---
export interface ReviewSummary {
  project_id: string;
  overall_status: string;
  total_checks: number;
  passed: number;
  failed: number;
  warnings: number;
  needs_review: number;
  critical_issues: ComplianceCheck[];
  all_checks: ComplianceCheck[];
  recommendations: string[];
}

// --- App Mode ---
export type AppMode = 'explore' | 'guide' | 'review';
