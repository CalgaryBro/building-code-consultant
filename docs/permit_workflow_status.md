# Calgary Building Permit Workflow Status Report

**Generated:** January 9, 2026
**Project:** Calgary Building Code Expert System
**Report Type:** Implementation Status Assessment

---

## Executive Summary

This report documents the current implementation status of permit workflow features in the Calgary Building Code Expert System. The system is designed to assist users with Development Permits (DP), Building Permits (BP), and Subdivision and Development Appeal Board (SDAB) processes.

---

## 1. Permit Types Covered in the Plan

### 1.1 Development Permit (DP)

**Status:** Partially Implemented

The Development Permit is the primary planning approval required before most construction projects. Key features defined:

| Feature | Plan Reference | Implementation Status |
|---------|---------------|----------------------|
| DP requirement determination | Guide Mode Step 3 | Implemented in `guide.py` |
| Zoning compliance check | Guide Mode Step 1-2 | Implemented via zones API |
| Document checklist generation | Guide Mode Step 5 | Schema defined, basic implementation |
| DP refusal issue checklist | Checklists API | Fully implemented |
| Fee estimation | Guide Mode | Implemented (`_calculate_dp_fee`) |

**Data Available:**
- `development-permits.json`: 188,019 historical permits (256 MB)
- `dp_refusal_checklist.json`: 12 issue categories with prevention tips

### 1.2 Building Permit (BP)

**Status:** Partially Implemented

The Building Permit is required for actual construction work. Key features:

| Feature | Plan Reference | Implementation Status |
|---------|---------------|----------------------|
| Part 9 vs Part 3 classification | Rule Engine | Implemented in `guide.py` |
| BP requirement determination | Guide Mode | Implemented |
| Required documents list | Guide Mode Step 5 | Defined in response schemas |
| Fee estimation | Guide Mode | Implemented (`_calculate_bp_fee`) |
| Trade permits (electrical, plumbing, gas) | Guide Mode | Basic implementation |

**Data Available:**
- `building-trade-permit-fee-schedule-2026.pdf`: Current fee schedule
- NBC(AE) 2023, NECB 2020, NFC(AE) 2023 codes in `/data/codes/`

### 1.3 Subdivision and Development Appeal Board (SDAB)

**Status:** Fully Implemented (Analysis Layer)

The SDAB handles appeals of permit decisions. Implementation includes:

| Feature | Plan Reference | Implementation Status |
|---------|---------------|----------------------|
| SDAB issue types catalog | Checklists API | Fully implemented |
| Risk assessment by project type | Checklists API | Fully implemented |
| Historical success rates | Checklists API | Fully implemented |
| Sample citations | Checklists API | Fully implemented |
| General guidance | Checklists API | Fully implemented |

**Data Available:**
- `sdab-decisions.json`: 1,433 historical SDAB decisions
- `sdab_issues_checklist.json`: 20 issue types with detailed analysis

---

## 2. Workflow Steps Defined Per Permit Type

### 2.1 Development Permit Workflow

As defined in the project plan (Guide Mode):

```
Step 1: Enter Project Location
    - Address lookup
    - Parcel identification
    - Zone determination

Step 2: Describe Your Project
    - Project type selection
    - Building parameters input
    - Features specification

Step 3: Project Classification
    - Part 9 vs Part 3 determination
    - Occupancy classification
    - Permit requirements identification
    - Professional requirements
    - Cost estimation

Step 4: Requirements Dashboard
    - Zoning requirements display
    - Fire safety requirements
    - Egress requirements
    - Energy requirements

Step 5: Document Checklist
    - DP required documents list
    - BP required documents list
    - Downloadable checklist PDF
```

**Implementation Status:** Steps 1-3 implemented in Guide API, Steps 4-5 partially implemented

### 2.2 Building Permit Workflow

```
Pre-Application:
    - DP approval (or concurrent application)
    - Professional engagement (if Part 3)

Drawing Preparation:
    - Architectural drawings
    - Structural drawings
    - Mechanical drawings
    - Electrical drawings
    - Energy compliance documentation

Submission:
    - Complete drawing package
    - Application forms
    - Supporting documentation

Review Process:
    - Initial review
    - Corrections (if needed)
    - Approval

Inspections:
    - Foundation
    - Framing
    - Insulation
    - Final
```

**Implementation Status:** Review Mode partially implemented, inspection tracking not implemented

### 2.3 SDAB Appeal Workflow

```
Appeal Filing (within 21 days):
    - Decision appeal filed
    - Documentation prepared

Initial Meeting:
    - Case introduction
    - Scheduling

Final Session:
    - Evidence presentation
    - Board deliberation

Decision:
    - Written decision (within 15 days)
    - Possible outcomes: ALLOWED, DENIED, ALLOWED IN PART, WITHDRAWN, STRUCK
```

**Implementation Status:** Historical data analysis complete, workflow tracking not implemented

---

## 3. Checklists and Issue Lists Created

### 3.1 DP Refusal Checklist (`dp_refusal_checklist.json`)

**Metadata:**
- Total permits analyzed: 188,019
- Refused permits: 4,293 (2.28% refusal rate)
- Generated: January 9, 2026

**12 Issue Categories:**

| Issue ID | Category | Frequency | Relaxation Success Rate |
|----------|----------|-----------|------------------------|
| DP-REF-001 | Other Violations | 995 | N/A |
| DP-REF-002 | Signage Issues | 778 | N/A |
| DP-REF-003 | Setback Violation | 685 | 92% |
| DP-REF-004 | Change of Use | 469 | N/A |
| DP-REF-005 | Home Occupation | 454 | N/A |
| DP-REF-006 | Accessory Building | 258 | N/A |
| DP-REF-007 | Height Violation | 240 | 85% |
| DP-REF-008 | Secondary Suite | 154 | N/A |
| DP-REF-009 | Parking Deficiency | 107 | N/A |
| DP-REF-010 | Driveway Access | 104 | N/A |
| DP-REF-011 | Coverage Violation | 37 | 84% |
| DP-REF-012 | Fence Violation | 12 | N/A |

Each issue includes:
- Common zones affected
- Typical deficiency description
- Code references (Land Use Bylaw 1P2007 sections)
- Sample citations with real permit numbers
- Prevention tips

### 3.2 SDAB Issues Checklist (`sdab_issues_checklist.json`)

**Metadata:**
- Total cases analyzed: 1,433
- Generated: January 9, 2026

**Overall Outcomes:**
- WITHDRAWN: 205
- DENIED: 416
- ALLOWED IN PART: 297
- ALLOWED: 322
- STRUCK: 104
- Unknown: 89

**20 Issue Types:**

| Issue ID | Type | Frequency | Risk Level | Success Rate |
|----------|------|-----------|------------|--------------|
| SDAB-001 | Single Residential | 318 | MODERATE | 66.4% |
| SDAB-002 | Commercial | 182 | MODERATE | 66.7% |
| SDAB-003 | Other | 151 | MODERATE | 56.9% |
| SDAB-004 | Single Detached Dwelling | 116 | MEDIUM | 52.3% |
| SDAB-005 | Cannabis | 112 | MEDIUM | 40.8% |
| SDAB-006 | Secondary Suite | 93 | MEDIUM | 52.1% |
| SDAB-007 | Multi-Residential Development | 60 | MODERATE | 63.6% |
| SDAB-008 | Accessory Residential Building | 56 | MEDIUM | 48.6% |
| SDAB-009 | Sign | 50 | MODERATE | 61.4% |
| SDAB-010 | Rowhouse Building | 49 | LOW | 71.8% |
| SDAB-011 | Home Occupation | 41 | MEDIUM | 50.0% |
| SDAB-012 | Multi Residential | 32 | LOW | 76.9% |
| SDAB-013 | SDD w/ Accessory Building | 30 | MEDIUM | 42.1% |
| SDAB-014 | Cannabis Store | 21 | MEDIUM | 50.0% |
| SDAB-015 | Liquor Store | 20 | HIGH | 38.5% |
| SDAB-016 | Semi-Detached Dwelling | 17 | LOW | 78.6% |
| SDAB-017 | Retail and Consumer Service | 15 | HIGH | 37.5% |
| SDAB-018 | Mixed Use | 12 | LOW | 87.5% |
| SDAB-019 | Subdivision | 9 | MODERATE | 60.0% |
| SDAB-020 | Child Care Service | 8 | MODERATE | 57.1% |

Each issue includes:
- Key factors for approval/denial
- Sample citations with decision numbers
- Recommendations for success

---

## 4. API Endpoints Implemented

### 4.1 Current Backend API Structure

**Location:** `/Users/mohmmadhanafy/Building-code-consultant/app/backend/app/api/`

| Endpoint Group | File | Prefix | Status |
|----------------|------|--------|--------|
| EXPLORE Mode | `explore.py` | `/api/v1/explore` | Implemented |
| GUIDE Mode | `guide.py` | `/api/v1/guide` | Implemented |
| REVIEW Mode | `review.py` | `/api/v1/review` | Implemented |
| Zones & Parcels | `zones.py` | `/api/v1/zones` | Implemented |
| Checklists | `checklists.py` | `/api/v1/checklists` | Implemented |

### 4.2 Checklists API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/checklists/sdab` | GET | List all SDAB issue types |
| `/api/v1/checklists/sdab/{issue_id}` | GET | Get SDAB issue details |
| `/api/v1/checklists/sdab/guidance/general` | GET | Get SDAB general guidance |
| `/api/v1/checklists/dp` | GET | List DP refusal categories |
| `/api/v1/checklists/dp/{issue_id}` | GET | Get DP issue details |
| `/api/v1/checklists/risk-assessment` | GET | Get risk assessment by project type |

### 4.3 Guide API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/guide/analyze` | POST | Analyze project and provide permit guidance |
| `/api/v1/guide/projects` | GET | List all projects |
| `/api/v1/guide/projects/{project_id}` | GET | Get project details |
| `/api/v1/guide/classification` | GET | Explain Part 9 vs Part 3 classification |

---

## 5. Missing Components

### 5.1 High Priority (Core Workflow Gaps)

| Component | Description | Effort |
|-----------|-------------|--------|
| **Permit Application Tracker** | Track permit status through stages | Medium |
| **Document Upload/Verification** | Upload and validate required documents | High |
| **Inspection Scheduling** | Track and schedule required inspections | Medium |
| **Fee Calculator Integration** | Accurate fee calculation from PDF schedule | Medium |
| **Permit Timeline Estimator** | Realistic timeline based on historical data | Low |

### 5.2 Medium Priority (Enhanced Features)

| Component | Description | Effort |
|-----------|-------------|--------|
| **Address Autocomplete** | Integration with Calgary parcel database | Low |
| **Zoning Map Visualization** | Display parcel on map with zone overlay | Medium |
| **DP Approval Checklist Generator** | Generate specific checklist based on zone/project | Medium |
| **SDAB Appeal Assistant** | Step-by-step appeal filing guide | Low |
| **Neighbor Notification Tracker** | Track circulation/notification requirements | Low |

### 5.3 Low Priority (Future Enhancements)

| Component | Description | Effort |
|-----------|-------------|--------|
| **Historical Permit Search** | Search similar approved/refused permits | Medium |
| **Construction Cost Estimator** | Integration with local cost data | High |
| **Professional Finder** | Connect to architects/engineers directory | Medium |
| **Multi-Permit Coordination** | Coordinate DP/BP/Trade permits | Medium |

---

## 6. Recommended Next Steps

### Phase 1: Complete Core Permit Workflow (2-3 weeks)

1. **Implement Permit Application Tracker**
   - Create `permits` database table with status tracking
   - Add API endpoints for permit creation/status updates
   - Create workflow state machine (Applied -> In Review -> Approved/Refused)

2. **Enhance Guide Mode Output**
   - Generate downloadable PDF checklists
   - Add more specific document requirements per zone/project type
   - Integrate DP refusal checklist warnings into guidance

3. **Connect Risk Assessment to Guide**
   - Automatically show relevant SDAB risks in project analysis
   - Add "Common Issues in Your Zone" section

### Phase 2: Document Management (2-3 weeks)

4. **Document Upload System**
   - File upload endpoints for permit documents
   - Basic validation (file type, size)
   - Document status tracking

5. **Drawing Review Integration**
   - Connect REVIEW mode to permit workflow
   - Store compliance check results with permit

### Phase 3: Advanced Features (3-4 weeks)

6. **Timeline and Fee Estimation**
   - Parse fee schedule PDF into structured data
   - Calculate accurate fees based on project parameters
   - Estimate timeline based on historical data

7. **Notification and Alerts**
   - Email notifications for permit status changes
   - Deadline reminders for document submission
   - Appeal deadline alerts

### Phase 4: Integration (2-3 weeks)

8. **External Data Integration**
   - Real-time parcel lookup from Calgary Open Data
   - Zone boundary visualization
   - Permit status from City portal (if API available)

---

## 7. Data Assets Summary

| Data File | Size | Records | Purpose |
|-----------|------|---------|---------|
| `development-permits.json` | 256 MB | 188,019 | Historical DP data |
| `sdab-decisions.json` | 762 KB | 1,433 | SDAB decision history |
| `dp_refusal_checklist.json` | 30 KB | 12 issues | DP refusal analysis |
| `sdab_issues_checklist.json` | 64 KB | 20 issues | SDAB issue analysis |
| `building-trade-permit-fee-schedule-2026.pdf` | 130 KB | - | Fee schedule |
| Parcel addresses | 249 MB | 414,605 | Address/zone lookup |

---

## 8. Schema Definitions Available

The following Pydantic schemas are defined for the permit workflow:

**Checklists (`schemas/checklists.py`):**
- `SDABIssueSummary`, `SDABIssueDetail`, `SDABChecklistResponse`
- `DPIssueSummary`, `DPIssueDetail`, `DPChecklistResponse`
- `RiskIssue`, `RiskAssessmentResponse`
- `GeneralGuidance`

**Projects (`schemas/projects.py`):**
- `GuideProjectInput`, `GuideResponse`
- `PermitRequirement`
- `ProjectCreate`, `ProjectResponse`

---

## Conclusion

The Calgary Building Code Expert System has a solid foundation for permit workflow support:

**Strengths:**
- Comprehensive SDAB and DP issue analysis with historical data
- Building classification (Part 9 vs Part 3) working
- Risk assessment by project type functional
- Clean API architecture with proper schemas

**Gaps to Address:**
- No permit application tracking/status management
- No document upload/verification system
- No inspection scheduling
- Fee calculation is estimated, not exact
- Timeline estimation not based on historical data

**Recommended Priority:** Focus first on permit tracking and document management to create a complete workflow from project analysis through permit application.
