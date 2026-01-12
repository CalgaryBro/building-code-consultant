# Calgary Building Code Expert System
## Comprehensive Development Plan

**Version:** 1.0
**Date:** January 8, 2026
**Scope:** Calgary, Alberta, Canada

---

## Table of Contents

1. [Vision](#vision)
2. [Operating Modes](#operating-modes)
3. [Data Requirements](#data-requirements)
4. [Acquired Data Inventory](#acquired-data-inventory)
5. [Data Extraction Methodology](#data-extraction-methodology)
6. [Database Schema](#database-schema)
7. [Rule Engine Design](#rule-engine-design)
8. [User Journeys](#user-journeys)
9. [Technology Stack](#technology-stack)
10. [DSSP Module: Development Site Servicing Plan Designer](#dssp-module-development-site-servicing-plan-designer)
11. [Quantity Survey Module: Construction Cost Estimation](#quantity-survey-module-construction-cost-estimation)
12. [Future Modules: Complete Permit Workflow Automation](#future-modules-complete-permit-workflow-automation)
13. [Development Phases](#development-phases)
14. [Critical First Steps](#critical-first-steps)
15. [AI Limitations & Safety Guardrails](#ai-limitations--safety-guardrails)
16. [Building Classification Clarification](#building-classification-clarification)
17. [Data Maintenance & Update Monitoring](#data-maintenance--update-monitoring)

---

## Vision

A comprehensive AI-powered building code expert system that:

1. **Knows everything** - All codes, standards, bylaws in a structured database
2. **Guides from inception** - Helps before a single line is drawn
3. **Reviews for approval** - Checks finished drawings for first-pass City approval

### The Reality of "First-Pass Approval"

City of Calgary reviewers check against:
- NBC(AE) 2023 (building code)
- NECB 2020 (energy)
- Land Use Bylaw 1P2007 (zoning)
- Calgary-specific amendments
- Referenced standards (CSA, ULC, ASTM - hundreds of them)
- Reviewer interpretation and experience

**Honest assessment**: 100% first-pass approval is extremely difficult, but we can dramatically reduce corrections by catching the common issues.

---

## Operating Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                    CALGARY CODE EXPERT                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   MODE 1        │   MODE 2        │   MODE 3                    │
│   EXPLORE       │   GUIDE         │   REVIEW                    │
│                 │                 │                             │
│   "What does    │   "I want to    │   "Check my                 │
│    the code     │    build X at   │    drawings"                │
│    say about?"  │    location Y"  │                             │
├─────────────────┼─────────────────┼─────────────────────────────┤
│   Code lookup   │   Pre-design    │   Drawing                   │
│   Q&A interface │   requirements  │   compliance                │
│   Search/browse │   Permit path   │   Full check                │
│                 │   Checklists    │   Report gen                │
└─────────────────┴─────────────────┴─────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE DATABASE                           │
├─────────────────────────────────────────────────────────────────┤
│  NBC(AE) 2023  │  NECB 2020  │  Bylaw 1P2007  │  STANDATA      │
│  Part 3 & 9    │  Energy     │  Zoning        │  Bulletins     │
├─────────────────────────────────────────────────────────────────┤
│  Calgary Amendments  │  Fee Schedules  │  Referenced Standards │
└─────────────────────────────────────────────────────────────────┘
```

### Mode 1: EXPLORE
- **Purpose**: Code lookup and Q&A interface
- **User Question**: "What does the code say about...?"
- **Features**:
  - Search/browse code sections
  - Natural language queries
  - Cross-reference navigation
  - Code article explanations

### Mode 2: GUIDE
- **Purpose**: Pre-design requirements and permit pathway
- **User Question**: "I want to build X at location Y"
- **Features**:
  - Project intake questionnaire
  - Building classification (Part 9 vs Part 3)
  - Zoning compliance check
  - Permit requirements identification
  - Document checklists generation
  - Cost and timeline estimation

### Mode 3: REVIEW
- **Purpose**: Drawing compliance checking
- **User Question**: "Check my drawings"
- **Features**:
  - AI-assisted data extraction
  - Human verification workflow
  - Compliance checking against all codes
  - Detailed report generation
  - Issue flagging with code references

#### Review UI Requirements (User Experience)

The review process must show real-time feedback to users:

```
┌─────────────────────────────────────────────────────────────────┐
│ DRAWING REVIEW IN PROGRESS                                      │
├─────────────────────────────────────────────────────────────────┤
│ Stage 1/5: Document Analysis           [██████████] COMPLETE    │
│ Stage 2/5: Dimension Extraction        [████████░░] 80%         │
│ Stage 3/5: Code Compliance Check       [░░░░░░░░░░] Pending     │
│ Stage 4/5: Zoning Verification         [░░░░░░░░░░] Pending     │
│ Stage 5/5: Report Generation           [░░░░░░░░░░] Pending     │
├─────────────────────────────────────────────────────────────────┤
│ Currently Checking: NBC 9.8.4 - Stair Dimensions                │
│                                                                 │
│ LIVE RESULTS:                                                   │
│ ✅ Stair width: 920mm (min 860mm required)          PASS        │
│ ✅ Headroom: 2100mm (min 1950mm required)           PASS        │
│ ⚠️ Riser height: 210mm (max 200mm allowed)          FAIL        │
│ ✅ Run depth: 280mm (min 255mm required)            PASS        │
└─────────────────────────────────────────────────────────────────┘
```

**Required UI Elements:**
1. **Progress Indicators**: Visual stage tracking with percentage complete
2. **Current Check Display**: Show which code section is being checked
3. **Pass/Fail Status**: Real-time results for each criterion as checked
4. **Color Coding**: Green (pass), Yellow (warning), Red (fail)
5. **Code References**: Link each check to specific NBC article
6. **Final Summary Report**: Downloadable PDF with all findings

---

## Data Requirements

### Tier 1: Must Have (Free/Public)

| Document | Source | Format | Priority |
|----------|--------|--------|----------|
| NBC(AE) 2023 | NRC | PDF | Critical |
| NECB 2020 | NRC | PDF | Critical |
| Land Use Bylaw 1P2007 | Calgary.ca | PDF/HTML | Critical |
| STANDATA Bulletins | Alberta.ca | PDF | High |
| Calgary DP/BP Checklists | Calgary.ca | PDF | High |
| Permit Fee Schedule | Calgary.ca | PDF | High |
| Part 9 Illustrated Guide | NRC | PDF | High |

### Tier 2: Important (Some Cost)

| Document | Source | Cost | Notes |
|----------|--------|------|-------|
| CSA Referenced Standards | CSA Group | $$$ | NBC references ~200 CSA standards |
| Construction Cost Data | RSMeans/local | $$ | For estimation |
| Historical permit data | City/FOIP | Time | For common issues |

### Tier 3: Enhancement

| Document | Source | Notes |
|----------|--------|-------|
| AHJ interpretations | City contacts | Informal knowledge |
| Common correction letters | Industry contacts | What fails review |
| Professional practice guides | APEGA/AAA | Best practices |

### Data Source URLs

```
NBC(AE) 2023:
https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada/codes-canada-publications

NECB 2020:
https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada/codes-canada-publications

Calgary Land Use Bylaw 1P2007:
https://www.calgary.ca/planning/land-use-bylaw.html

STANDATA Bulletins:
https://www.alberta.ca/standata-building-code

Calgary Permit Information:
https://www.calgary.ca/development/permits.html
```

---

## Acquired Data Inventory

**Status:** Downloaded January 8, 2026
**Total Size:** 348 MB
**Location:** `/data/` directory

### National Codes (Free from NRC)

| Document | File | Size | Source |
|----------|------|------|--------|
| NBC(AE) 2023 | `codes/NBC-AE-2023.pdf` | 23 MB | [NRC Publications](https://nrc-publications.canada.ca/eng/view/object/?id=0316d953-0d55-4311-af69-cad55efec499) |
| NFC(AE) 2023 | `codes/NFC-AE-2023.pdf` | 6.0 MB | [NRC Publications](https://nrc-publications.canada.ca/eng/view/object/?id=6c3e5cf6-8891-40e0-8b37-a78665c23f27) |
| NECB 2020 | `codes/NECB-2020.pdf` | 4.2 MB | [NRC Publications](https://nrc-publications.canada.ca/eng/view/object/?id=af36747e-3eee-4024-a1b4-73833555c7fa) |
| NPC 2020 | `codes/NPC-2020.pdf` | 4.8 MB | [NRC Publications](https://nrc-publications.canada.ca/eng/view/object/?id=6e7cabf5-d83e-4efd-9a1c-6515fc7cdc71) |

### Calgary Land Use Bylaw

| Document | File | Size | Source |
|----------|------|------|--------|
| Land Use Bylaw 1P2007 (Jan 2025) | `bylaws/land-use-bylaw-1p2007-amended-2025-01-01.pdf` | 12 MB | [Calgary.ca](https://www.calgary.ca/planning/land-use.html) |

### Alberta STANDATA Bulletins

| Category | Count | Location | Source |
|----------|-------|----------|--------|
| Building (23-BCB series) | 7 bulletins | `standata/*.pdf` | [Open Alberta](https://open.alberta.ca/publications/standata-bulletin-building-national-building-code-2023-alberta-edition) |
| Building Interpretations (23-BCI series) | 20 interpretations | `standata/*.pdf` | [Open Alberta](https://open.alberta.ca/publications/standata-interpretation-building-national-building-code-2023-alberta-edition) |
| Fire (23-FCB series) | 4 bulletins | `standata/fire/*.pdf` | [Open Alberta](https://open.alberta.ca/publications/standata-bulletin-fire-code-2023) |
| Plumbing (20-PCB series) | 10 bulletins | `standata/plumbing/*.pdf` | [Open Alberta](https://open.alberta.ca/publications/standata-bulletin-plumbing) |

### Calgary Permits & Guidelines

| Document | File | Size | Purpose |
|----------|------|------|---------|
| 2026 Fee Schedule | `permits/building-trade-permit-fee-schedule-2026.pdf` | 127 KB | Permit cost calculation |
| Accessibility Design Guide 2024 | `permits/accessibility-design-guide-2024.pdf` | 4.8 MB | Barrier-free requirements |
| Access Design Standards | `permits/access-design-standards.pdf` | 8.0 MB | Mobility/vision/cognitive |
| Design Guidelines (City Buildings) | `permits/design-guidelines-city-buildings.pdf` | 8.2 MB | Building design standards |
| DSSP Guidelines | `permits/dssp-design-guidelines.pdf` | 1.5 MB | Site servicing plans |
| Subdivision Servicing 2020 | `permits/subdivision-servicing-guidelines-2020.pdf` | 18 MB | Infrastructure requirements |

### Calgary Zoning/GIS Data

| Dataset | File(s) | Records | Source |
|---------|---------|---------|--------|
| Parcel Addresses | `zoning/parcel-addresses-*.json` (9 files) | **414,605** | [Open Calgary API](https://data.calgary.ca/resource/9zvu-p8uz.json) |
| Zone Designation Codes | `zoning/land-use-designation-codes.json` | 50+ zones | [Open Calgary](https://data.calgary.ca/resource/svbi-k49z.json) |

### Reference Standards

| Document | File | Size | Notes |
|----------|------|------|-------|
| 12-Storey EMTC Guide | `standards/12-storey-EMTC-guide.pdf` | 2.3 MB | Mass timber construction |
| NPC 2020 Comparison | `standards/NPC-2020-comparison.pdf` | 1.4 MB | Code changes reference |

### Still Required (Registration or Purchase)

| Document | Access Method | Cost | Priority |
|----------|--------------|------|----------|
| CSA/ASC B651:23 (Accessibility) | [Free registration at CSA CTA Portal](https://www.csagroup.org/csa-group-accessibility-standards-for-cta/) | Free | High |
| CSA C22.1:24 (Electrical Code) | [CSA Group Store](https://www.csagroup.org/store/product/CSA_C22.1:24/) | ~$300-500 | Medium (trade permits) |
| Other CSA Referenced Standards | CSA Group | Varies | Low (reference only) |

### Directory Structure

```
data/
├── codes/                              # 38 MB - National codes
│   ├── NBC-AE-2023.pdf
│   ├── NFC-AE-2023.pdf
│   ├── NECB-2020.pdf
│   └── NPC-2020.pdf
├── bylaws/                             # 12 MB - Calgary bylaws
│   └── land-use-bylaw-1p2007-amended-2025-01-01.pdf
├── standata/                           # 6.6 MB - Alberta STANDATA
│   ├── 23-BCB-*.pdf                    # Building bulletins
│   ├── 23-BCI-*.pdf                    # Building interpretations
│   ├── fire/
│   │   └── 23-FCB-*.pdf                # Fire bulletins
│   └── plumbing/
│       └── 20-PCB-*.pdf                # Plumbing bulletins
├── permits/                            # 41 MB - Calgary guides
│   ├── building-trade-permit-fee-schedule-2026.pdf
│   ├── accessibility-design-guide-2024.pdf
│   ├── access-design-standards.pdf
│   ├── design-guidelines-city-buildings.pdf
│   ├── dssp-design-guidelines.pdf
│   └── subdivision-servicing-guidelines-2020.pdf
├── standards/                          # 3.7 MB - Reference docs
│   ├── 12-storey-EMTC-guide.pdf
│   └── NPC-2020-comparison.pdf
└── zoning/                             # 249 MB - Calgary GIS data
    ├── land-use-designation-codes.json
    └── parcel-addresses-*.json         # 9 files, 414,605 records
```

### Data Sufficiency Assessment

| Mode | Data Required | Status |
|------|--------------|--------|
| **EXPLORE** | NBC(AE), NFC(AE), NECB, NPC, Bylaw, STANDATA | ✅ Complete |
| **GUIDE** | Zone codes, parcel data, fee schedule, checklists | ✅ Complete |
| **REVIEW** | NBC(AE) Part 9, dimensional requirements | ✅ Complete |

**Conclusion:** All core data for development and testing is acquired. CSA accessibility standard requires free registration. Electrical code needed only for electrical trade permits (separate stream).

---

## Data Extraction Methodology

### Why NOT Use AI's "Stored Knowledge"

**Critical Warning**: Populating the database from an LLM's training data would be dangerous:

| Risk | Impact |
|------|--------|
| Unverifiable sources | Cannot trace values back to official code |
| Potential hallucination | LLMs can invent plausible-sounding but wrong values |
| Version ambiguity | Cannot confirm which code edition is referenced |
| Calgary-specific gaps | Local amendments poorly represented in training |
| Life-safety liability | A wrong dimension could cause injury or death |

**Every numerical value must be traceable to an authoritative source document with page number.**

### The Extraction Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA EXTRACTION PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │  OFFICIAL    │    │   LLM-       │    │   HUMAN      │               │
│  │  SOURCE      │───▶│   ASSISTED   │───▶│   VERIFIED   │───▶ DATABASE │
│  │  PDFs        │    │   EXTRACTION │    │   DATA       │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│        │                    │                   │                        │
│        ▼                    ▼                   ▼                        │
│   NBC(AE) 2023        Structured JSON     Domain Expert                 │
│   NECB 2020           with confidence     reviews 100%                  │
│   Bylaw 1P2007        scores              of values                     │
│   STANDATA                                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Stage 1: Document Acquisition

| Document | Source | Copyright | Storage Allowed |
|----------|--------|-----------|-----------------|
| NBC(AE) 2023 | NRC/Queen's Printer | Crown Copyright | Yes, for internal use |
| NECB 2020 | NRC | Crown Copyright | Yes, for internal use |
| Land Use Bylaw 1P2007 | Calgary.ca | Public | Yes |
| STANDATA Bulletins | Alberta.ca | Public | Yes |
| CSA Standards | CSA Group | Licensed | Reference ONLY, no full text |
| ULC Standards | ULC | Licensed | Reference ONLY, no full text |

### Stage 2: LLM-Assisted Extraction

The LLM helps extract, but NEVER decides compliance:

```python
class CodeExtractor:
    """
    LLM-assisted extraction from official code PDFs.
    ALL outputs require human verification before production use.
    """

    EXTRACTION_PROMPT = """
    Extract this NBC article to structured JSON.

    CRITICAL RULES:
    - Extract EXACTLY what is written in the code
    - Do NOT interpret or paraphrase
    - If a value is unclear, set confidence to "LOW"
    - Include the exact page number
    - Do NOT infer values not explicitly stated

    OUTPUT FORMAT:
    {
        "article_number": "9.8.4.1",
        "title": "Stair Width",
        "full_text": "[exact code text]",
        "requirements": [
            {
                "element": "stair_width",
                "condition": "dwelling unit stairs",
                "min_value": 860,
                "max_value": null,
                "unit": "mm",
                "exact_quote": "shall have a width of not less than 860 mm",
                "confidence": "HIGH",
                "page_number": 423,
                "exceptions": []
            }
        ],
        "references_to": ["9.8.4.2", "9.8.7.1"],
        "extraction_warnings": []
    }
    """

    def extract_article(self, pdf_bytes: bytes, article_num: str) -> dict:
        result = self.llm.extract(pdf_bytes, self.EXTRACTION_PROMPT)

        # ALWAYS mark as unverified initially
        result["verified"] = False
        result["verified_by"] = None
        result["verified_date"] = None
        result["extraction_method"] = "llm_assisted"
        result["extraction_date"] = datetime.now().isoformat()

        return result
```

### Stage 3: Human Verification (MANDATORY)

```
┌─────────────────────────────────────────────────────────────────┐
│                 VERIFICATION INTERFACE                           │
├─────────────────────────────────────────────────────────────────┤
│  Article: 9.8.4.1 - Stair Width                                 │
│  Source: NBC(AE) 2023, Page 423                                 │
│                                                                  │
│  Extracted Value              Verification                      │
│  ─────────────────────        ─────────────────────             │
│                                                                  │
│  Element: stair_width         Original PDF: [VIEW]              │
│  Min: 860 mm                                                    │
│  Confidence: HIGH             ( ) Confirm correct               │
│                               ( ) Correct to: [____]            │
│                               ( ) Flag for review               │
│                                                                  │
│  Quote: "shall have a width   Notes: [________________]         │
│  of not less than 860 mm"                                       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Verifier: ________________  Designation: _________________     │
│  Date: ___________           [APPROVE] [REJECT] [FLAG]          │
└─────────────────────────────────────────────────────────────────┘
```

**Verification Rules:**
- ALL dimensional values must be human-verified before use
- Critical fields (stair width, fire ratings, egress) require architect/engineer verification
- Non-critical fields (titles, descriptions) can be batch-verified
- Any LOW confidence extraction must be manually verified against source PDF

### Stage 4: Database Storage with Audit Trail

```sql
-- Enhanced requirements table with extraction tracking
CREATE TABLE requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id),
    element VARCHAR(100) NOT NULL,
    condition JSONB,
    min_value DECIMAL,
    max_value DECIMAL,
    unit VARCHAR(20),
    exact_quote TEXT NOT NULL,

    -- EXTRACTION TRACKING
    extraction_method VARCHAR(50) NOT NULL,     -- 'llm_assisted', 'manual', 'import'
    extraction_confidence VARCHAR(20),          -- 'HIGH', 'MEDIUM', 'LOW'
    extraction_date TIMESTAMP NOT NULL,
    extraction_model VARCHAR(100),              -- 'qwen3-vl:8b', 'gpt-4', etc.

    -- SOURCE TRACEABILITY
    source_document VARCHAR(255) NOT NULL,      -- 'NBC(AE) 2023'
    source_page INTEGER NOT NULL,
    source_edition VARCHAR(50) NOT NULL,

    -- VERIFICATION (Required before production use)
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verifier_designation VARCHAR(100),          -- 'Architect', 'Engineer', 'Code Consultant'
    verified_date TIMESTAMP,
    verification_notes TEXT,

    -- Prevent unverified data in compliance checks
    CONSTRAINT verified_for_compliance CHECK (
        is_verified = TRUE OR
        extraction_confidence != 'LOW'
    )
);

-- View for ONLY verified requirements (used by rule engine)
CREATE VIEW verified_requirements AS
SELECT * FROM requirements WHERE is_verified = TRUE;
```

### Different Strategies by Mode

| Mode | Data Source | LLM Role | Verification |
|------|-------------|----------|--------------|
| **EXPLORE** | Full text + RAG | Synthesize answers with citations | Informational only |
| **GUIDE** | Verified structured data | None - direct database lookup | All data pre-verified |
| **REVIEW** | Verified structured data | Extract from drawings only | Human verifies extractions |

### Extraction Effort Estimate

| Document | Approx. Articles | Method | Expert Hours |
|----------|-----------------|--------|--------------|
| NBC(AE) Part 9 | ~500 | LLM + verify | 80-120 |
| NBC(AE) Part 3 | ~800 | LLM + verify | 120-160 |
| Land Use Bylaw zones | ~50 zones | Semi-auto | 40-60 |
| STANDATA bulletins | ~100 docs | Manual review | 40-60 |
| Calgary amendments | ~50 items | Manual | 20-30 |
| **TOTAL** | | | **300-430 hours** |

**This is significant effort, but there is no shortcut for life-safety data.**

### Extraction Pipeline Implementation Phases

```
PHASE 1: PILOT (Weeks 1-2)
├── Extract NBC Part 9, Sections 9.8-9.9 (Stairs & Exits) as pilot
├── Build verification interface
├── Recruit domain expert verifier
├── Measure extraction accuracy
└── Refine prompts based on results

PHASE 2: CORE EXTRACTION (Weeks 3-8)
├── NBC Part 9 complete (prioritized by frequency of use)
├── Land Use Bylaw zones (Calgary-specific)
├── STANDATA bulletins affecting Part 9
└── All values human-verified

PHASE 3: EXPANSION (Weeks 9-12)
├── NBC Part 3 (complex buildings)
├── NECB 2020 (energy code)
├── Referenced standards metadata
└── Complete verification cycle

PHASE 4: VALIDATION (Weeks 13-14)
├── Test against known scenarios
├── Cross-check with official summaries
├── User acceptance testing
└── Final sign-off by licensed professional
```

### Copyright Considerations

| Document Type | Can Store Full Text? | Can Display? | Notes |
|---------------|---------------------|--------------|-------|
| NBC(AE) | Yes (Crown Copyright) | Yes with attribution | Free to use, must cite |
| NECB | Yes (Crown Copyright) | Yes with attribution | Free to use, must cite |
| Land Use Bylaw | Yes (Public) | Yes | Municipal bylaw |
| STANDATA | Yes (Public) | Yes | Alberta Government |
| CSA Standards | **NO** | Reference only | Must purchase license |
| ULC/ASTM | **NO** | Reference only | Must purchase license |

For licensed standards, store only:
- Standard number (e.g., "CSA A440")
- Title
- Year/edition
- What it covers (summary)
- Link to purchase

---

## Database Schema

### Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     CODE REPOSITORY                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  codes                          articles                     │
│  ├── id                         ├── id                       │
│  ├── name (NBC_AE_2023)         ├── code_id (FK)             │
│  ├── version                    ├── number (9.10.9.1)        │
│  ├── effective_date             ├── title                    │
│  ├── jurisdiction               ├── full_text                │
│  └── status (current/legacy)    ├── parent_article_id        │
│                                 └── supersedes_id            │
│                                                              │
│  requirements                   conditions                   │
│  ├── id                         ├── id                       │
│  ├── article_id (FK)            ├── requirement_id (FK)      │
│  ├── type (dimensional/         ├── field (building_height)  │
│  │        material/procedural)  ├── operator (<=, ==, IN)    │
│  ├── element (stair_width)      ├── value (3)                │
│  ├── min_value / max_value      ├── unit (storeys)           │
│  ├── unit (mm)                  └── logic (AND/OR with next) │
│  └── exceptions[]               │                            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                     ZONING (BYLAW 1P2007)                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  zones                          zone_rules                   │
│  ├── id                         ├── id                       │
│  ├── code (R-C1, M-C1, etc)     ├── zone_id (FK)             │
│  ├── name                       ├── rule_type (setback/      │
│  ├── description                │              height/FAR)   │
│  └── category (residential/     ├── min_value / max_value    │
│                commercial/etc)  ├── unit                     │
│                                 └── conditions[]             │
│                                                              │
│  parcels                        (from City GIS data)         │
│  ├── id                                                      │
│  ├── address                                                 │
│  ├── legal_description                                       │
│  ├── zone_id (FK)                                            │
│  ├── area_sqm                                                │
│  └── geometry (PostGIS)                                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                     PROJECTS                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  projects                       extracted_data               │
│  ├── id                         ├── id                       │
│  ├── user_id                    ├── project_id (FK)          │
│  ├── address                    ├── field_name               │
│  ├── parcel_id (FK)             ├── value                    │
│  ├── classification (Part9/3)   ├── source (user/ai)         │
│  ├── occupancy_group            ├── confidence               │
│  ├── building_height            ├── verified (bool)          │
│  ├── building_area              ├── verified_by              │
│  └── status                     └── drawing_ref              │
│                                                              │
│  compliance_checks              documents                    │
│  ├── id                         ├── id                       │
│  ├── project_id (FK)            ├── project_id (FK)          │
│  ├── requirement_id (FK)        ├── type (floor_plan/elev)   │
│  ├── status (pass/fail/na)      ├── file_path                │
│  ├── actual_value               ├── extracted_data[]         │
│  ├── required_value             └── upload_date              │
│  └── notes                                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Detailed Table Definitions

#### codes
```sql
CREATE TABLE codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_name VARCHAR(50) NOT NULL,           -- e.g., "NBC_AE_2023"
    full_name VARCHAR(255) NOT NULL,          -- e.g., "National Building Code of Canada 2020 - Alberta Edition 2023"
    version VARCHAR(20) NOT NULL,             -- e.g., "2023"
    effective_date DATE NOT NULL,             -- e.g., "2024-05-01"
    jurisdiction VARCHAR(50) NOT NULL,        -- e.g., "Alberta"
    status VARCHAR(20) DEFAULT 'current',     -- current, legacy, draft
    source_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### articles
```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_id UUID REFERENCES codes(id),
    article_number VARCHAR(50) NOT NULL,      -- e.g., "9.10.9.1"
    title VARCHAR(500),
    full_text TEXT NOT NULL,
    parent_article_id UUID REFERENCES articles(id),
    hierarchy_level INT,                      -- 1=Division, 2=Section, 3=Subsection, etc.
    supersedes_id UUID REFERENCES articles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(code_id, article_number)
);

CREATE INDEX idx_articles_number ON articles(article_number);
CREATE INDEX idx_articles_code ON articles(code_id);
```

#### requirements
```sql
CREATE TABLE requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id),
    requirement_type VARCHAR(50) NOT NULL,    -- dimensional, material, procedural, performance
    element VARCHAR(100) NOT NULL,            -- e.g., "stair_width", "fire_rating", "ceiling_height"
    description TEXT,
    min_value DECIMAL,
    max_value DECIMAL,
    exact_value DECIMAL,
    unit VARCHAR(20),                         -- mm, m, minutes, storeys, m², etc.
    value_text VARCHAR(255),                  -- for non-numeric requirements
    is_mandatory BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_requirements_element ON requirements(element);
```

#### conditions
```sql
CREATE TABLE conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID REFERENCES requirements(id),
    condition_order INT NOT NULL,             -- order of evaluation
    field VARCHAR(100) NOT NULL,              -- e.g., "building_height", "occupancy_group"
    operator VARCHAR(20) NOT NULL,            -- =, !=, <, <=, >, >=, IN, NOT_IN, BETWEEN
    value_text VARCHAR(255),                  -- for string comparisons
    value_numeric DECIMAL,                    -- for numeric comparisons
    value_array TEXT[],                       -- for IN/NOT_IN operators
    logic_with_next VARCHAR(10),              -- AND, OR, null if last condition
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### zones
```sql
CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bylaw_id UUID REFERENCES codes(id),
    zone_code VARCHAR(20) NOT NULL,           -- e.g., "R-C1", "M-C1", "C-COR1"
    zone_name VARCHAR(255) NOT NULL,
    category VARCHAR(50),                      -- residential, commercial, industrial, mixed
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(bylaw_id, zone_code)
);
```

#### zone_rules
```sql
CREATE TABLE zone_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID REFERENCES zones(id),
    rule_type VARCHAR(50) NOT NULL,           -- setback_front, setback_side, height, FAR, parking, etc.
    description TEXT,
    min_value DECIMAL,
    max_value DECIMAL,
    unit VARCHAR(20),
    calculation_formula TEXT,                 -- e.g., "0.25 * lot_depth" for rear setback
    conditions JSONB,                         -- additional conditions as JSON
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### parcels
```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE parcels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address VARCHAR(255) NOT NULL,
    legal_description VARCHAR(255),
    zone_id UUID REFERENCES zones(id),
    area_sqm DECIMAL,
    frontage_m DECIMAL,
    depth_m DECIMAL,
    geometry GEOMETRY(POLYGON, 4326),
    city_parcel_id VARCHAR(50),               -- City's internal ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_parcels_geometry ON parcels USING GIST(geometry);
CREATE INDEX idx_parcels_address ON parcels(address);
```

#### projects
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,                             -- future: link to users table
    project_name VARCHAR(255),
    address VARCHAR(255) NOT NULL,
    parcel_id UUID REFERENCES parcels(id),

    -- Classification
    classification VARCHAR(20),               -- PART_9, PART_3
    occupancy_group VARCHAR(10),              -- A1, A2, B1, B2, C, D, E, F1, F2, F3
    construction_type VARCHAR(50),            -- combustible, noncombustible, heavy_timber

    -- Building parameters
    building_height_storeys INT,
    building_height_m DECIMAL,
    building_area_sqm DECIMAL,
    footprint_area_sqm DECIMAL,
    dwelling_units INT,

    -- Project type
    project_type VARCHAR(50),                 -- new_construction, addition, renovation, change_of_use

    -- Status
    status VARCHAR(50) DEFAULT 'draft',       -- draft, in_review, complete

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### compliance_checks
```sql
CREATE TABLE compliance_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    requirement_id UUID REFERENCES requirements(id),

    check_status VARCHAR(20) NOT NULL,        -- pass, fail, warning, not_applicable, pending
    actual_value DECIMAL,
    actual_value_text VARCHAR(255),
    required_value DECIMAL,
    required_value_text VARCHAR(255),

    notes TEXT,
    drawing_reference VARCHAR(100),           -- e.g., "A2.1" sheet reference
    location_description TEXT,                -- e.g., "Bedroom 2, north wall"

    checked_at TIMESTAMP DEFAULT NOW(),
    checked_by VARCHAR(100)                   -- user or 'system'
);

CREATE INDEX idx_compliance_project ON compliance_checks(project_id);
CREATE INDEX idx_compliance_status ON compliance_checks(check_status);
```

#### documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),

    document_type VARCHAR(50) NOT NULL,       -- floor_plan, elevation, section, site_plan, etc.
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),

    sheet_number VARCHAR(20),                 -- e.g., "A1.0"
    sheet_title VARCHAR(255),
    scale VARCHAR(20),                        -- e.g., "1:100"

    extraction_status VARCHAR(20),            -- pending, processing, complete, failed
    extraction_confidence DECIMAL,

    uploaded_at TIMESTAMP DEFAULT NOW()
);
```

#### extracted_data
```sql
CREATE TABLE extracted_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    project_id UUID REFERENCES projects(id),

    field_name VARCHAR(100) NOT NULL,         -- e.g., "stair_width", "room_area"
    field_value DECIMAL,
    field_value_text VARCHAR(255),
    unit VARCHAR(20),

    source VARCHAR(20) NOT NULL,              -- ai, user
    confidence DECIMAL,                       -- 0.0 to 1.0

    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,

    bounding_box JSONB,                       -- coordinates on document
    page_number INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_extracted_project ON extracted_data(project_id);
CREATE INDEX idx_extracted_field ON extracted_data(field_name);
```

---

## Rule Engine Design

### Core Principle

**Deterministic rules, not AI inference.** Every compliance decision must be traceable to a specific code article.

### Rule Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class ComplianceStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"  # needs more data

@dataclass
class ComplianceResult:
    status: ComplianceStatus
    article_ref: str
    message: str
    actual_value: Optional[float] = None
    required_value: Optional[float] = None
    location: Optional[str] = None
    suggested_fix: Optional[str] = None

class CodeRule(ABC):
    """Base class for all code rules."""

    def __init__(self, article_ref: str, description: str):
        self.article_ref = article_ref
        self.description = description

    @abstractmethod
    def applies_to(self, project: 'Project') -> bool:
        """Determine if this rule applies to the given project."""
        pass

    @abstractmethod
    def check(self, project: 'Project') -> ComplianceResult:
        """Check compliance and return result."""
        pass

    def get_required_data(self) -> List[str]:
        """Return list of data fields required to evaluate this rule."""
        return []
```

### Example Rules

```python
# Example 1: Fire separation between dwelling units (NBC 9.10.9.1)
class FireSeparationDwellingUnits(CodeRule):
    def __init__(self):
        super().__init__(
            article_ref="NBC_AE_2023_9.10.9.1",
            description="Fire separation between dwelling units"
        )

    def applies_to(self, project: Project) -> bool:
        return (
            project.classification == "PART_9" and
            project.occupancy_group == "C" and
            project.dwelling_unit_count > 1
        )

    def get_required_data(self) -> List[str]:
        return ["party_wall_fire_rating"]

    def check(self, project: Project) -> ComplianceResult:
        required_rating = 45  # minutes

        for wall in project.get_party_walls():
            if wall.fire_rating is None:
                return ComplianceResult(
                    status=ComplianceStatus.PENDING,
                    article_ref=self.article_ref,
                    message="Party wall fire rating not specified",
                    required_value=required_rating
                )

            if wall.fire_rating < required_rating:
                return ComplianceResult(
                    status=ComplianceStatus.FAIL,
                    article_ref=self.article_ref,
                    message=f"Party wall requires minimum {required_rating} minute fire rating",
                    actual_value=wall.fire_rating,
                    required_value=required_rating,
                    location=wall.location,
                    suggested_fix=f"Upgrade wall assembly to achieve {required_rating} min rating"
                )

        return ComplianceResult(
            status=ComplianceStatus.PASS,
            article_ref=self.article_ref,
            message="Party wall fire separation meets requirements"
        )


# Example 2: Minimum stair width (NBC 9.8.4.1)
class MinimumStairWidth(CodeRule):
    def __init__(self):
        super().__init__(
            article_ref="NBC_AE_2023_9.8.4.1",
            description="Minimum width of stairs"
        )

    def applies_to(self, project: Project) -> bool:
        return project.classification == "PART_9"

    def get_required_data(self) -> List[str]:
        return ["stair_width"]

    def check(self, project: Project) -> ComplianceResult:
        min_width = 860  # mm for residential

        for stair in project.get_stairs():
            if stair.width is None:
                return ComplianceResult(
                    status=ComplianceStatus.PENDING,
                    article_ref=self.article_ref,
                    message="Stair width not specified",
                    required_value=min_width
                )

            if stair.width < min_width:
                return ComplianceResult(
                    status=ComplianceStatus.FAIL,
                    article_ref=self.article_ref,
                    message=f"Stair width must be minimum {min_width}mm",
                    actual_value=stair.width,
                    required_value=min_width,
                    location=stair.location,
                    suggested_fix=f"Increase stair width to minimum {min_width}mm"
                )

        return ComplianceResult(
            status=ComplianceStatus.PASS,
            article_ref=self.article_ref,
            message="Stair widths meet minimum requirements"
        )


# Example 3: Egress window size (NBC 9.9.10.1)
class EgressWindowSize(CodeRule):
    def __init__(self):
        super().__init__(
            article_ref="NBC_AE_2023_9.9.10.1",
            description="Egress window minimum unobstructed opening"
        )

    def applies_to(self, project: Project) -> bool:
        return (
            project.classification == "PART_9" and
            project.occupancy_group == "C"
        )

    def get_required_data(self) -> List[str]:
        return ["bedroom_egress_window_area"]

    def check(self, project: Project) -> ComplianceResult:
        min_area = 0.35  # m²
        min_dimension = 380  # mm

        for bedroom in project.get_bedrooms():
            window = bedroom.egress_window

            if window is None:
                return ComplianceResult(
                    status=ComplianceStatus.FAIL,
                    article_ref=self.article_ref,
                    message="Bedroom requires egress window",
                    location=bedroom.name,
                    suggested_fix="Add egress window with min 0.35m² unobstructed opening"
                )

            if window.unobstructed_area < min_area:
                return ComplianceResult(
                    status=ComplianceStatus.FAIL,
                    article_ref=self.article_ref,
                    message=f"Egress window must have minimum {min_area}m² unobstructed opening",
                    actual_value=window.unobstructed_area,
                    required_value=min_area,
                    location=bedroom.name,
                    suggested_fix="Increase window size or change to casement style"
                )

            if window.min_dimension < min_dimension:
                return ComplianceResult(
                    status=ComplianceStatus.FAIL,
                    article_ref=self.article_ref,
                    message=f"Egress window minimum dimension must be {min_dimension}mm",
                    actual_value=window.min_dimension,
                    required_value=min_dimension,
                    location=bedroom.name
                )

        return ComplianceResult(
            status=ComplianceStatus.PASS,
            article_ref=self.article_ref,
            message="All bedroom egress windows meet requirements"
        )
```

### Rule Registry

```python
class RuleRegistry:
    """Registry of all code rules."""

    def __init__(self):
        self._rules: List[CodeRule] = []

    def register(self, rule: CodeRule):
        self._rules.append(rule)

    def get_applicable_rules(self, project: Project) -> List[CodeRule]:
        return [rule for rule in self._rules if rule.applies_to(project)]

    def run_all_checks(self, project: Project) -> List[ComplianceResult]:
        results = []
        for rule in self.get_applicable_rules(project):
            results.append(rule.check(project))
        return results


# Initialize registry with all rules
rule_registry = RuleRegistry()
rule_registry.register(FireSeparationDwellingUnits())
rule_registry.register(MinimumStairWidth())
rule_registry.register(EgressWindowSize())
# ... register all other rules
```

### Classification Engine

```python
def classify_building(params: dict) -> dict:
    """
    Classify building as Part 9 or Part 3.
    Returns classification details with code references.
    """
    height = params.get('storeys', 0)
    area = params.get('building_area_sqm', 0)
    occupancy = params.get('occupancy_group', '')

    # Part 9 limits (NBC 9.1.1.1)
    PART_9_MAX_HEIGHT = 3  # storeys
    PART_9_MAX_AREA = 600  # m²
    PART_9_ALLOWED_OCCUPANCIES = ['C', 'D', 'E', 'F2', 'F3']

    reasons = []

    # Check each criterion
    if height > PART_9_MAX_HEIGHT:
        reasons.append(f"Height ({height} storeys) exceeds Part 9 limit of {PART_9_MAX_HEIGHT}")

    if area > PART_9_MAX_AREA:
        reasons.append(f"Area ({area}m²) exceeds Part 9 limit of {PART_9_MAX_AREA}m²")

    if occupancy not in PART_9_ALLOWED_OCCUPANCIES:
        reasons.append(f"Occupancy {occupancy} not permitted under Part 9")

    if reasons:
        return {
            'classification': 'PART_3',
            'code_ref': 'NBC 3.1.1.1',
            'reasons': reasons,
            'professionals_required': ['Architect', 'Structural Engineer']
        }
    else:
        return {
            'classification': 'PART_9',
            'code_ref': 'NBC 9.1.1.1',
            'reasons': ['Building meets all Part 9 criteria'],
            'professionals_required': ['Designer (AABC or Architect)']
        }
```

---

## User Journeys

### Journey 1: EXPLORE Mode
**User Question: "What does the code say about X?"**

This mode allows users to search and browse the building code database conversationally.

```
┌─────────────────────────────────────────────────────────────┐
│  EXPLORE MODE - Code Lookup Interface                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ What are the stair width requirements for a house?  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  NBC(AE) 2023 - Section 9.8.4.1                            │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  MINIMUM STAIR WIDTH                                        │
│                                                             │
│  For residential occupancies (Group C):                     │
│  • Minimum clear width: 860 mm                             │
│  • Measured between handrails if both sides have them      │
│  • Measured from handrail to wall if one side              │
│                                                             │
│  Related Requirements:                                      │
│  ├── 9.8.2.1 - Headroom (min 1950mm)                       │
│  ├── 9.8.4.5 - Risers (125-200mm)                          │
│  ├── 9.8.4.6 - Treads (min 235mm run)                      │
│  └── 9.8.7.4 - Handrail height (865-965mm)                 │
│                                                             │
│  [View Full Article]  [Add to Project]  [Ask Follow-up]     │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ What about headroom on stairs?                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  NBC(AE) 2023 - Section 9.8.2.1                            │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  STAIR HEADROOM                                             │
│                                                             │
│  • Minimum headroom: 1950 mm                               │
│  • Measured vertically from nosing line to ceiling         │
│  • Applies to full length of stair flight                  │
│                                                             │
│  Note: This is a common failure point in renovations       │
│  where existing floor structures limit headroom.            │
│                                                             │
│  [View Full Article]  [Add to Project]                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**EXPLORE Mode Features:**
- Natural language search of code database
- Context-aware follow-up questions
- Cross-reference navigation between related articles
- Save requirements to active project
- Browse code by section hierarchy

---

### Journey 2: GUIDE Mode
**User Question: "I want to build X at location Y"**

This mode guides users from project inception through permit requirements.

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Enter Project Location                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Enter your project address:                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 456 Kensington Road NW, Calgary, AB                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                               [Look Up →]   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ✓ PARCEL FOUND                                            │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Address: 456 Kensington Road NW                      │ │
│  │  Legal: Plan 1234AB, Block 5, Lot 12                  │ │
│  │                                                       │ │
│  │  ZONING: M-C1                                         │ │
│  │  Multi-Residential – Contextual Low Profile           │ │
│  │                                                       │ │
│  │  Lot Dimensions:                                      │ │
│  │  • Width: 15.0 m                                      │ │
│  │  • Depth: 35.0 m                                      │ │
│  │  • Area: 525 m²                                       │ │
│  │                                                       │ │
│  │  Zoning Allows:                                       │ │
│  │  • Multi-family residential                           │ │
│  │  • Max height: 14 m / 4 storeys                      │ │
│  │  • Max FAR: 2.0                                       │ │
│  │  • Max density: 150 units/hectare                    │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│                                              [Continue →]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Describe Your Project                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What are you planning to build?                            │
│                                                             │
│  ○ Single-family home                                       │
│  ○ Duplex (side-by-side or up/down)                        │
│  ○ Triplex / Fourplex                                       │
│  ● 4-unit townhouse                          ← Selected     │
│  ○ Low-rise apartment (5+ units)                           │
│  ○ Addition to existing building                            │
│  ○ Secondary suite                                          │
│  ○ Commercial / retail                                      │
│  ○ Mixed-use (residential + commercial)                     │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Project Details:                                           │
│                                                             │
│  Number of storeys:        [3]     (above grade)           │
│  Number of units:          [4]                              │
│  Total building area:      [480]   m²                      │
│  Building footprint:       [160]   m²                      │
│                                                             │
│  Additional features:                                       │
│  ☑ Basement (full)                                         │
│  ☐ Secondary suites in units                               │
│  ☑ Attached garages                                        │
│  ☐ Rooftop deck                                            │
│                                                             │
│                                              [Continue →]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Project Classification                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                                                       │ │
│  │  YOUR PROJECT CLASSIFICATION                          │ │
│  │  ═══════════════════════════════════════════════════ │ │
│  │                                                       │ │
│  │  Building Code:      PART 9 (Acceptable Solutions)    │ │
│  │  ─────────────────────────────────────────────────── │ │
│  │  Reason: ≤3 storeys, ≤600m², Group C occupancy       │ │
│  │                                                       │ │
│  │  Occupancy Group:    C (Residential)                  │ │
│  │  Construction:       Combustible permitted            │ │
│  │  Fire Rating:        45-min between units (9.10.9)    │ │
│  │                                                       │ │
│  │  ─────────────────────────────────────────────────── │ │
│  │                                                       │ │
│  │  PERMITS REQUIRED:                                    │ │
│  │                                                       │ │
│  │  ✓ Development Permit (DP)     Timeline: 4-6 weeks   │ │
│  │  ✓ Building Permit (BP)        Timeline: 3-4 weeks   │ │
│  │  ✓ Electrical Permit                                  │ │
│  │  ✓ Plumbing Permit                                    │ │
│  │  ✓ Gas Permit                                         │ │
│  │  ✓ HVAC Permit                                        │ │
│  │                                                       │ │
│  │  ─────────────────────────────────────────────────── │ │
│  │                                                       │ │
│  │  PROFESSIONALS REQUIRED:                              │ │
│  │                                                       │ │
│  │  ✓ Architect OR AABC-registered Designer             │ │
│  │  ✓ Structural Engineer (multi-unit building)         │ │
│  │  ○ Geotechnical Engineer (site-dependent)            │ │
│  │                                                       │ │
│  │  ─────────────────────────────────────────────────── │ │
│  │                                                       │ │
│  │  ESTIMATED COSTS:                                     │ │
│  │                                                       │ │
│  │  Permit Fees:        ~$8,500 - $12,000               │ │
│  │  Construction:       ~$1,400,000 - $1,800,000        │ │
│  │  (Based on $2,900-$3,750/m² for townhouse)           │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│                                              [Continue →]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Requirements Dashboard                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Based on your project, here are ALL applicable             │
│  requirements from codes and bylaws:                        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ZONING - Bylaw 1P2007 (M-C1)               [✓ Compliant]  │
│  ─────────────────────────────────────────────────────────  │
│  │ Requirement          │ Allowed    │ Yours    │ Status │ │
│  ├──────────────────────┼────────────┼──────────┼────────┤ │
│  │ Height               │ max 14m    │ ~9.5m    │ ✓      │ │
│  │ FAR                  │ max 2.0    │ 0.91     │ ✓      │ │
│  │ Front setback        │ min 3.0m   │ TBD      │ ?      │ │
│  │ Rear setback         │ min 7.5m   │ TBD      │ ?      │ │
│  │ Side setback (N)     │ min 1.2m   │ TBD      │ ?      │ │
│  │ Side setback (S)     │ min 1.2m   │ TBD      │ ?      │ │
│  │ Parking              │ 4 stalls   │ 4        │ ✓      │ │
│  │ Landscaping          │ 30% min    │ TBD      │ ?      │ │
│  └──────────────────────┴────────────┴──────────┴────────┘ │
│                                                 [Expand ▼]  │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  FIRE SAFETY - NBC 9.10                        [12 items]  │
│  ─────────────────────────────────────────────────────────  │
│  ├── Fire separation between units: 1 hour     Required    │
│  ├── Fire separation to garage: 45 min         Required    │
│  ├── Smoke alarms: each floor + bedroom        Required    │
│  ├── CO alarms: near sleeping areas            Required    │
│  ├── Fire blocking in concealed spaces         Required    │
│  └── Exit signs: at each exit                  Required    │
│                                                 [Expand ▼]  │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  EGRESS - NBC 9.9                              [8 items]   │
│  ─────────────────────────────────────────────────────────  │
│  ├── Number of exits: 2 per unit               Required    │
│  ├── Exit separation: per 9.9.9                Required    │
│  ├── Stair width: min 860mm                    Required    │
│  ├── Stair headroom: min 1950mm                Required    │
│  ├── Egress windows: all bedrooms              Required    │
│  └── Travel distance: max per 9.9.6            Required    │
│                                                 [Expand ▼]  │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ENERGY - NBC 9.36 / NECB                      [6 items]   │
│  ─────────────────────────────────────────────────────────  │
│  ├── Climate Zone: 7A (Calgary)                            │
│  ├── Wall insulation: min RSI 4.67 (R-26.5)   Required    │
│  ├── Ceiling insulation: min RSI 8.67 (R-49)  Required    │
│  ├── Windows: max U-value 1.60                 Required    │
│  ├── Air barrier system                        Required    │
│  └── HRV/ERV ventilation                       Required    │
│                                                 [Expand ▼]  │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  [Generate Full Checklist PDF]    [Upload Drawings →]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Document Checklist                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DOCUMENTS REQUIRED FOR DEVELOPMENT PERMIT                  │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ☐ Completed DP Application Form                           │
│  ☐ Certificate of Title (current within 30 days)           │
│  ☐ Site Plan (1:200 or 1:500 scale)                        │
│     • Property lines and dimensions                         │
│     • Building footprint with setbacks                      │
│     • Driveway and parking layout                          │
│     • Landscaping plan                                      │
│  ☐ Floor Plans (all levels)                                │
│  ☐ Elevations (all four sides)                             │
│  ☐ Streetscape context                                     │
│  ☐ Shadow study (required if height >10m)                  │
│  ☐ Parking plan                                            │
│                                                             │
│  DOCUMENTS REQUIRED FOR BUILDING PERMIT                     │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ☐ Completed BP Application Form                           │
│  ☐ Approved DP (or concurrent application)                 │
│  ☐ Architectural Drawings (sealed by professional)         │
│     • Floor plans with dimensions                           │
│     • Building sections                                     │
│     • Construction details                                  │
│     • Door/window schedules                                 │
│  ☐ Structural Drawings (sealed by P.Eng)                   │
│     • Foundation plan                                       │
│     • Framing plans                                         │
│     • Structural details                                    │
│  ☐ Mechanical Drawings                                     │
│     • HVAC layout                                           │
│     • Plumbing layout                                       │
│  ☐ Electrical Drawings                                     │
│  ☐ Energy Compliance (NBC 9.36 or NECB)                    │
│  ☐ Truss Engineering (if applicable)                       │
│  ☐ Geotechnical Report (site-dependent)                    │
│  ☐ Lot Grading Plan                                        │
│                                                             │
│  [Download Checklist PDF]        [Upload Drawings →]        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Journey 3: REVIEW Mode
**User Question: "Check my drawings for code compliance"**

This mode analyzes uploaded drawings and checks them against all applicable codes.

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Upload Drawing Set                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Upload your drawings for compliance review:                │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                                                       │ │
│  │                                                       │ │
│  │           Drag & drop your PDF drawing set            │ │
│  │                  or click to browse                   │ │
│  │                                                       │ │
│  │          Supported: PDF (preferred), DWG              │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ✓ Uploaded: 456_Kensington_Townhouse_BP.pdf               │
│                                                             │
│  Detecting sheets...                                        │
│                                                             │
│  ✓ A0.1  - Cover Sheet / Index                             │
│  ✓ A1.0  - Site Plan                                       │
│  ✓ A2.0  - Main Floor Plan                                 │
│  ✓ A2.1  - Second Floor Plan                               │
│  ✓ A2.2  - Third Floor Plan                                │
│  ✓ A3.0  - Building Sections (2)                           │
│  ✓ A3.1  - Stair Sections & Details                        │
│  ✓ A4.0  - Elevations (North & South)                      │
│  ✓ A4.1  - Elevations (East & West)                        │
│  ✓ A5.0  - Wall Sections & Details                         │
│  ✓ A6.0  - Door & Window Schedules                         │
│    ... (8 more sheets detected)                             │
│                                                             │
│  Total: 19 sheets                                           │
│                                                             │
│                                      [Start Analysis →]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: AI Extraction (Qwen3-VL)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Analyzing drawings with AI vision model...                 │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Sheet A1.0 - Site Plan                         [Complete]  │
│  ████████████████████ 100%                                  │
│                                                             │
│  Extracted:                                                 │
│  • Lot width: 15.0m                            ✓ HIGH      │
│  • Lot depth: 35.0m                            ✓ HIGH      │
│  • Front setback: 3.2m                         ✓ HIGH      │
│  • Rear setback: 8.1m                          ✓ HIGH      │
│  • Side setback (N): 1.5m                      ✓ HIGH      │
│  • Side setback (S): 1.5m                      ✓ HIGH      │
│  • Building footprint: 12.0m x 11.5m           ✓ HIGH      │
│  • Parking spaces: 4                           ✓ HIGH      │
│  • Driveway width: 6.0m                        ✓ HIGH      │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Sheet A2.0 - Main Floor Plan                [Processing]   │
│  ████████████░░░░░░░░ 60%                                  │
│                                                             │
│  Extracting room dimensions...                              │
│  Extracting door widths...                                  │
│  Extracting stair width...                                  │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Overall Progress: Sheet 2 of 19                            │
│  ██░░░░░░░░░░░░░░░░░░ 10%                                  │
│                                                             │
│  Estimated time remaining: 3 minutes                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Human Verification                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️  VERIFICATION REQUIRED                                  │
│                                                             │
│  The following items need your confirmation before          │
│  compliance checking can proceed.                           │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  1 of 7: STAIR WIDTH                         [Life-Safety]  │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                                                       │ │
│  │  [Cropped drawing showing stair with dimension]       │ │
│  │                                                       │ │
│  │        ←──── 920 ────→                               │ │
│  │       ┌──────────────┐                               │ │
│  │       │   ═══════    │                               │ │
│  │       │   ═══════    │                               │ │
│  │       │   ═══════    │                               │ │
│  │       └──────────────┘                               │ │
│  │                                                       │ │
│  │  Sheet: A3.1    Location: Common stair, units 1-2     │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  AI Extracted: 920 mm                                       │
│  Confidence: MEDIUM (dimension partially obscured)          │
│                                                             │
│  ● Confirm value is 920 mm                                 │
│  ○ Correct to: [____] mm                                   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  2 of 7: FIRE SEPARATION RATING              [Life-Safety]  │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                                                       │ │
│  │  [Cropped drawing showing demising wall]              │ │
│  │                                                       │ │
│  │  AI could not find fire rating annotation             │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  AI Extracted: NOT FOUND                                    │
│  Reason: No fire rating symbol or note visible              │
│                                                             │
│  Please enter the fire rating for unit demising walls:      │
│  Fire rating: [60] minutes                                  │
│  Drawing reference: [A5.0, Detail 3]                        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Progress: ██░░░░░░░░ 2 of 7 items verified                │
│                                                             │
│                                              [Continue →]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Compliance Check                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Running compliance checks against:                         │
│                                                             │
│  • NBC(AE) 2023 Part 9                                      │
│  • Calgary Land Use Bylaw 1P2007 (Zone M-C1)               │
│  • NBC 9.36 Energy Requirements                             │
│  • STANDATA Bulletins (Alberta)                             │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ████████████████████ 100% Complete                        │
│                                                             │
│  Checking zoning compliance...              ✓ 8/8 passed   │
│  Checking fire separations...               ✓ 6/6 passed   │
│  Checking egress requirements...            ⚠ 7/8 passed   │
│  Checking stair dimensions...               ✓ 4/4 passed   │
│  Checking window requirements...            ✗ 3/4 passed   │
│  Checking accessibility...                  ✓ 2/2 passed   │
│  Checking energy compliance...              ✓ 5/5 passed   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  SUMMARY: 1 Fail, 1 Warning, 48 Pass                       │
│                                                             │
│                                      [View Full Report →]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Compliance Report                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROJECT: 456 Kensington Road NW - 4-Unit Townhouse        │
│  DATE: January 8, 2026                                      │
│  DRAWING SET: 456_Kensington_Townhouse_BP.pdf (19 sheets)  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                                                       │ │
│  │              COMPLIANCE SUMMARY                       │ │
│  │                                                       │ │
│  │    ✓ 48 PASS      ⚠ 1 WARNING      ✗ 1 FAIL         │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  ✗ FAIL: Bedroom 3 Egress Window (Unit 2)                  │
│  ───────────────────────────────────────────────────────   │
│                                                             │
│  Code Reference: NBC(AE) 2023 Section 9.9.10.1             │
│                                                             │
│  REQUIREMENT:                                               │
│  Bedrooms in residential occupancies shall have at least   │
│  one outside window with unobstructed opening of not       │
│  less than 0.35 m².                                        │
│                                                             │
│  FOUND ON DRAWINGS:                                         │
│  Sheet A2.1, Unit 2, Bedroom 3                              │
│  Window size: 600mm x 470mm = 0.28 m²                      │
│                                                             │
│  DEFICIENCY:                                                │
│  Unobstructed opening area is 0.28 m²                      │
│  Required minimum is 0.35 m²                               │
│  Shortfall: 0.07 m² (20% below minimum)                    │
│                                                             │
│  SUGGESTED CORRECTIONS:                                     │
│  • Increase window to minimum 750mm x 500mm (0.375 m²)     │
│  • OR change to casement window for larger clear opening   │
│  • OR reclassify room as non-bedroom (den/office)          │
│                                                             │
│  ───────────────────────────────────────────────────────   │
│                                                             │
│  ⚠ WARNING: Stair Headroom at Landing                      │
│  ───────────────────────────────────────────────────────   │
│                                                             │
│  Code Reference: NBC(AE) 2023 Section 9.8.2.1              │
│                                                             │
│  REQUIREMENT:                                               │
│  Minimum headroom of 1950mm measured vertically from       │
│  stair nosing line.                                        │
│                                                             │
│  FOUND ON DRAWINGS:                                         │
│  Sheet A3.1, Common Stair                                   │
│  Headroom at landing: 1960mm                               │
│                                                             │
│  STATUS:                                                    │
│  Technically compliant but marginal (10mm above minimum)   │
│                                                             │
│  RECOMMENDATION:                                            │
│  • Verify dimension during construction                     │
│  • Consider increasing to 2000mm+ for safety margin        │
│  • Note: Finishing materials may reduce clearance          │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  PASSED CHECKS (48 items)                      [Expand ▼]  │
│                                                             │
│  ───────────────────────────────────────────────────────   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [Download Full Report PDF]                         │   │
│  │                                                     │   │
│  │  [Share Report with Designer]                       │   │
│  │                                                     │   │
│  │  [Fix Issues & Re-check]                            │   │
│  │                                                     │   │
│  │  [Submit for Permit] (Coming Soon)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ───────────────────────────────────────────────────────   │
│                                                             │
│  DISCLAIMER: This report is generated by an automated      │
│  system and does not constitute official code compliance   │
│  approval. Final approval requires review by the City of   │
│  Calgary and licensed professionals. All life-safety       │
│  dimensions should be verified by a qualified designer.    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Quick Reference: System Actions by User Intent

| User Action | Mode | What System Does |
|-------------|------|------------------|
| "What does code say about X?" | EXPLORE | Search code database, return articles with references |
| "Show me stair requirements" | EXPLORE | Display NBC 9.8 requirements with values |
| Enter address | GUIDE | Geocode → Find parcel → Lookup zone → Show rules |
| Describe project type | GUIDE | Classify Part 9/3, determine occupancy group |
| Enter building parameters | GUIDE | Calculate FAR, check height, list permits needed |
| "What professionals do I need?" | GUIDE | Based on classification, list required professionals |
| Generate checklist | GUIDE | Build DP/BP document requirements list |
| Upload drawings (PDF) | REVIEW | Split sheets, classify each, queue for VLM |
| AI analyzes sheet | REVIEW | Qwen3-VL extracts dimensions, rooms, annotations |
| User verifies value | REVIEW | Confirmed value stored for compliance check |
| Run compliance check | REVIEW | Rule engine checks all requirements |
| View report | REVIEW | Show pass/fail with code refs, suggested fixes |
| Download report | REVIEW | Generate PDF with full details |

---

## Technology Stack

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND                                │
├─────────────────────────────────────────────────────────────┤
│  Next.js 14 (App Router)                                    │
│  ├── React Server Components                                │
│  ├── Tailwind CSS                                           │
│  ├── shadcn/ui components                                   │
│  └── PDF.js for drawing display                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND                                 │
├─────────────────────────────────────────────────────────────┤
│  Python FastAPI                                             │
│  ├── Pydantic for validation                                │
│  ├── Rule engine (custom)                                   │
│  ├── SQLAlchemy ORM                                         │
│  └── Celery for async tasks                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     AI LAYER                                │
├─────────────────────────────────────────────────────────────┤
│  Local Deployment (M4 Max):                                 │
│  ├── Qwen3-VL-8B (document understanding)                   │
│  ├── PaddleOCR (fast text extraction)                       │
│  └── Ollama for model serving                               │
│                                                             │
│  OR Cloud (higher volume):                                  │
│  ├── Claude API (conversation, reasoning)                   │
│  └── Qwen3-VL API (vision tasks)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATABASE                                │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL 16                                              │
│  ├── PostGIS extension (parcel geometries)                  │
│  ├── pg_trgm (text search)                                  │
│  └── Structured code data                                   │
│                                                             │
│  Redis                                                      │
│  ├── Session cache                                          │
│  └── Task queue (Celery)                                    │
│                                                             │
│  S3/MinIO                                                   │
│  └── Document storage (drawings, reports)                   │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Stack

#### Frontend
| Technology | Purpose | Version |
|------------|---------|---------|
| Next.js | React framework | 14.x |
| TypeScript | Type safety | 5.x |
| Tailwind CSS | Styling | 3.x |
| shadcn/ui | Component library | latest |
| PDF.js | PDF rendering | 4.x |
| React Query | Data fetching | 5.x |
| Zustand | State management | 4.x |

#### Backend
| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Primary language | 3.11+ |
| FastAPI | Web framework | 0.109+ |
| Pydantic | Validation | 2.x |
| SQLAlchemy | ORM | 2.x |
| Alembic | Migrations | 1.x |
| Celery | Task queue | 5.x |
| pytest | Testing | 8.x |

#### AI/ML
| Technology | Purpose | Notes |
|------------|---------|-------|
| Qwen3-VL-8B | Vision/document | Via Ollama |
| PaddleOCR | Text extraction | Lightweight |
| LangChain | LLM orchestration | Optional |
| Claude API | Conversation | Cloud option |

#### Database
| Technology | Purpose | Notes |
|------------|---------|-------|
| PostgreSQL | Primary database | 16.x |
| PostGIS | Spatial queries | For parcels |
| Redis | Caching/queues | 7.x |
| MinIO | Object storage | S3-compatible |

#### Infrastructure
| Technology | Purpose | Notes |
|------------|---------|-------|
| Docker | Containerization | Required |
| Docker Compose | Local orchestration | Development |
| Nginx | Reverse proxy | Production |

---

## Qwen3-VL Server Integration

### Overview

We will deploy a **local Qwen3-VL server** as part of our application stack. This server handles all vision-language tasks including document OCR, drawing analysis, and data extraction.

```
┌─────────────────────────────────────────────────────────────────┐
│                    VLM SERVICE ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │   FastAPI   │ ──── │  VLM Queue  │ ──── │  Qwen3-VL   │     │
│  │   Backend   │      │   (Redis)   │      │   Server    │     │
│  └─────────────┘      └─────────────┘      └─────────────┘     │
│         │                                        │              │
│         │              ┌─────────────┐          │              │
│         └───────────── │  PaddleOCR  │ ─────────┘              │
│                        │  (Fallback) │                         │
│                        └─────────────┘                         │
│                                                                 │
│  Processing Pipeline:                                          │
│  1. Document uploaded → stored in MinIO                        │
│  2. Task queued in Redis                                       │
│  3. VLM Server processes with appropriate prompt               │
│  4. Results validated and stored                               │
│  5. Human verification triggered if confidence < threshold     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Server Deployment Options

#### Option 1: Ollama (Recommended for Development)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen3-VL model
ollama pull qwen3-vl:8b

# Run server (default port 11434)
ollama serve
```

**Docker Compose Integration:**
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: calgary-code-vlm
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    # For Apple Silicon (M4 Max):
    # No GPU reservation needed - uses Metal automatically

  vlm-api:
    build: ./services/vlm
    container_name: calgary-code-vlm-api
    ports:
      - "8100:8100"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - MODEL_NAME=qwen3-vl:8b
    depends_on:
      - ollama

volumes:
  ollama_data:
```

#### Option 2: vLLM (Recommended for Production)

```bash
# Install vLLM with vision support
pip install vllm[vision]

# Run server
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-8B \
    --port 8100 \
    --max-model-len 32768 \
    --trust-remote-code
```

**Docker Compose for vLLM:**
```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: calgary-code-vllm
    ports:
      - "8100:8000"
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    environment:
      - HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}
    command: >
      --model Qwen/Qwen3-VL-8B
      --max-model-len 32768
      --trust-remote-code
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### Option 3: Local Python Server (Custom Control)

```python
# services/vlm/server.py

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import torch
import io

app = FastAPI(title="Calgary Code VLM Service")

# Load model on startup
model = None
processor = None

@app.on_event("startup")
async def load_model():
    global model, processor
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen3-VL-8B",
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    processor = AutoProcessor.from_pretrained("Qwen/Qwen3-VL-8B")

class ExtractionRequest(BaseModel):
    document_type: str  # "floor_plan", "elevation", "permit_form", etc.
    extraction_fields: list[str]

class ExtractionResult(BaseModel):
    fields: dict
    confidence_scores: dict
    raw_text: str
    bounding_boxes: dict

@app.post("/extract", response_model=ExtractionResult)
async def extract_from_document(
    file: UploadFile = File(...),
    request: ExtractionRequest = None
):
    # Load image
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))

    # Build prompt based on document type
    prompt = build_extraction_prompt(request.document_type, request.extraction_fields)

    # Process with model
    inputs = processor(
        text=prompt,
        images=[image],
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(**inputs, max_new_tokens=2048)
    response = processor.decode(outputs[0], skip_special_tokens=True)

    # Parse structured response
    result = parse_extraction_response(response, request.extraction_fields)

    return result
```

### Hardware Requirements

| Configuration | VRAM | Performance | Use Case |
|---------------|------|-------------|----------|
| M4 Max 128GB | Shared 128GB | ~10 tok/s | Development, low volume |
| RTX 4090 24GB | 24GB | ~25 tok/s | Production, medium volume |
| A100 40GB | 40GB | ~50 tok/s | Production, high volume |
| 2x RTX 4090 | 48GB | ~45 tok/s | Can run 32B model |

**For M4 Max (Your Setup):**

Since Ollama is already installed on your system, you just need to pull the vision model:

```bash
# Step 1: Check available vision models
ollama list

# Step 2: Pull the Qwen vision model (check exact name available)
ollama pull qwen2-vl:7b
# OR if qwen3-vl becomes available:
ollama pull qwen3-vl:8b

# Step 3: Test the model
ollama run qwen2-vl:7b "What do you see in this image?" --images /path/to/test.jpg

# Step 4: Verify Ollama server is running
curl http://localhost:11434/api/tags
```

**Optimal Environment Settings for Apple Silicon:**
```bash
# Add to ~/.zshrc or ~/.bashrc
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.7
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_HOST=0.0.0.0:11434  # Allow network access

# Reload shell
source ~/.zshrc
```

**API Endpoint for Our Application:**
```
Base URL: http://localhost:11434
Generate: POST /api/generate
Chat: POST /api/chat
Models: GET /api/tags
```

**Expected Performance on M4 Max 128GB:**
- Model load time: ~15-30 seconds (first run)
- Token generation: ~8-12 tokens/second
- Image processing: ~3-5 seconds per page
- Memory usage: ~18-24GB during inference
- Can process ~20 drawing sheets in ~2-3 minutes

---

## VLM Prompt Engineering

### Prompt Design Principles

1. **Be explicit about output format** - Request JSON or structured text
2. **Provide examples** - Few-shot prompting improves accuracy
3. **Specify what NOT to do** - Prevent hallucination
4. **Request confidence levels** - For human verification workflow
5. **Include units** - Always specify expected units (mm, m, m²)

### Document Type: Construction Drawing - Floor Plan

```python
FLOOR_PLAN_EXTRACTION_PROMPT = """
You are analyzing a construction floor plan drawing. Extract the following information accurately.

CRITICAL RULES:
- Only extract values that are explicitly shown or dimensioned on the drawing
- If a value is not visible or unclear, respond with "NOT_FOUND" for that field
- Never estimate or calculate values - only read what is drawn
- Include units exactly as shown (convert to mm if in feet/inches)
- Report confidence as HIGH (clearly readable), MEDIUM (partially visible), or LOW (unclear)

EXTRACT THESE FIELDS:
1. overall_building_width: The total width dimension of the building
2. overall_building_depth: The total depth dimension of the building
3. room_dimensions: For each labeled room, extract width x depth
4. door_widths: Width of each door shown
5. stair_width: Width of any stairs shown
6. corridor_widths: Width of any corridors/hallways
7. window_locations: Which rooms have windows and approximate sizes

RESPOND IN THIS EXACT JSON FORMAT:
{
  "drawing_info": {
    "sheet_number": "<sheet number if visible>",
    "scale": "<drawing scale if noted>",
    "title": "<drawing title if visible>"
  },
  "dimensions": {
    "overall_building_width": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"},
    "overall_building_depth": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"}
  },
  "rooms": [
    {
      "name": "<room name>",
      "width": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"},
      "depth": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"},
      "has_egress_window": true|false|"UNCLEAR"
    }
  ],
  "doors": [
    {
      "location": "<description>",
      "width": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"},
      "type": "interior|exterior|fire_rated"
    }
  ],
  "stairs": [
    {
      "location": "<description>",
      "width": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"},
      "num_risers": <number if countable>
    }
  ],
  "corridors": [
    {
      "location": "<description>",
      "width": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"}
    }
  ],
  "notes": ["<any relevant notes visible on drawing>"],
  "extraction_warnings": ["<any issues encountered during extraction>"]
}

If you cannot determine a value, use:
{"value": null, "unit": "mm", "confidence": "NOT_FOUND", "reason": "<why not found>"}

Analyze the floor plan now:
"""
```

### Document Type: Construction Drawing - Building Section

```python
SECTION_EXTRACTION_PROMPT = """
You are analyzing a building section drawing. Extract vertical dimensions and construction details.

CRITICAL RULES:
- Only extract values explicitly dimensioned on the drawing
- Pay attention to datum/reference points for height measurements
- If a value is not visible, respond with "NOT_FOUND"
- Include the reference point for each height measurement

EXTRACT THESE FIELDS:
1. floor_to_floor_heights: Height between floor levels
2. ceiling_heights: Floor to ceiling heights per level
3. stair_headroom: Minimum headroom clearance at stairs
4. window_head_heights: Height to top of windows from floor
5. window_sill_heights: Height to bottom of windows from floor
6. foundation_depth: Depth of foundation below grade
7. roof_slope: Roof pitch if shown

RESPOND IN THIS EXACT JSON FORMAT:
{
  "drawing_info": {
    "sheet_number": "<sheet number>",
    "scale": "<scale>",
    "section_mark": "<section identifier>"
  },
  "floor_heights": [
    {
      "level": "Main Floor",
      "elevation": {"value": <number>, "unit": "mm", "reference": "datum"},
      "floor_to_ceiling": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"},
      "floor_to_floor": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"}
    }
  ],
  "stairs": {
    "headroom_clearance": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"},
    "total_rise": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"},
    "riser_height": {"value": <number>, "unit": "mm", "confidence": "HIGH|MEDIUM|LOW"}
  },
  "construction": {
    "wall_assembly": "<description if visible>",
    "roof_assembly": "<description if visible>",
    "foundation_type": "<type if identifiable>"
  },
  "extraction_warnings": []
}
"""
```

### Document Type: Construction Drawing - Site Plan

```python
SITE_PLAN_EXTRACTION_PROMPT = """
You are analyzing a site plan drawing. Extract setbacks, lot dimensions, and building placement.

CRITICAL RULES:
- Setbacks are measured from property lines to building face
- Lot dimensions define the property boundary
- Pay attention to North arrow orientation
- Note any easements or right-of-ways shown

EXTRACT THESE FIELDS:
1. lot_dimensions: Width and depth of the lot
2. lot_area: Total lot area if noted
3. front_setback: Distance from front property line to building
4. rear_setback: Distance from rear property line to building
5. side_setbacks: Distance from side property lines to building (left and right)
6. building_footprint: Footprint dimensions of the building
7. driveway_width: Width of driveway at property line
8. parking_spaces: Number of parking spaces shown

RESPOND IN THIS EXACT JSON FORMAT:
{
  "drawing_info": {
    "sheet_number": "<sheet number>",
    "scale": "<scale>",
    "north_orientation": "<degrees from top of page>"
  },
  "lot": {
    "width": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"},
    "depth": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"},
    "area": {"value": <number>, "unit": "m²", "confidence": "HIGH|MEDIUM|LOW"},
    "legal_description": "<if visible>"
  },
  "setbacks": {
    "front": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"},
    "rear": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"},
    "left_side": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"},
    "right_side": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"}
  },
  "building": {
    "footprint_width": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"},
    "footprint_depth": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"},
    "footprint_area": {"value": <number>, "unit": "m²", "confidence": "HIGH|MEDIUM|LOW"}
  },
  "parking": {
    "spaces_count": <number>,
    "driveway_width": {"value": <number>, "unit": "m", "confidence": "HIGH|MEDIUM|LOW"}
  },
  "extraction_warnings": []
}
"""
```

### Document Type: Title Block Extraction

```python
TITLE_BLOCK_PROMPT = """
You are analyzing the title block of a construction drawing. Extract project metadata.

EXTRACT THESE FIELDS:
1. project_name: Name of the project
2. project_address: Site address
3. sheet_number: Sheet identifier (e.g., A1.0)
4. sheet_title: Description of what the sheet shows
5. scale: Drawing scale(s)
6. date: Drawing date
7. drawn_by: Who prepared the drawing
8. checked_by: Who reviewed the drawing
9. designer_company: Design firm name
10. revision_info: Any revision notes

RESPOND IN THIS EXACT JSON FORMAT:
{
  "project": {
    "name": "<project name>",
    "address": "<full address>",
    "permit_number": "<if visible>"
  },
  "sheet": {
    "number": "<sheet number>",
    "title": "<sheet title>",
    "scale": "<scale or 'AS NOTED'>",
    "date": "<date in YYYY-MM-DD format if possible>"
  },
  "personnel": {
    "drawn_by": "<initials or name>",
    "checked_by": "<initials or name>",
    "approved_by": "<initials or name>"
  },
  "company": {
    "name": "<company name>",
    "address": "<company address if shown>",
    "phone": "<phone if shown>"
  },
  "revisions": [
    {"number": "<rev#>", "date": "<date>", "description": "<change>"}
  ]
}
"""
```

### Document Type: Permit Application Form

```python
PERMIT_FORM_EXTRACTION_PROMPT = """
You are analyzing a building permit application form. Extract all filled-in information.

CRITICAL RULES:
- Only extract values that are actually written/typed in the form fields
- Do not infer or assume any values
- Mark checkbox fields as true/false based on whether they are checked
- Preserve exact text as written for names, addresses, descriptions

EXTRACT ALL VISIBLE FORM FIELDS INCLUDING:
1. Applicant information (name, address, phone, email)
2. Property information (address, legal description, zoning)
3. Project description
4. Building information (type, area, height, occupancy)
5. Construction value
6. Contractor information
7. Designer/Architect information

RESPOND IN THIS EXACT JSON FORMAT:
{
  "form_type": "<type of permit form>",
  "applicant": {
    "name": "<name>",
    "address": "<address>",
    "phone": "<phone>",
    "email": "<email>"
  },
  "property": {
    "address": "<property address>",
    "legal_description": "<legal desc>",
    "current_zoning": "<zoning>",
    "lot_area": "<area if specified>"
  },
  "project": {
    "description": "<project description>",
    "work_type": "new|addition|renovation|demolition",
    "estimated_value": "<dollar amount>"
  },
  "building": {
    "occupancy_type": "<occupancy>",
    "num_storeys": <number>,
    "building_area": "<area>",
    "num_units": <number>
  },
  "professionals": {
    "architect": {"name": "<name>", "license": "<license#>"},
    "engineer": {"name": "<name>", "license": "<license#>"},
    "contractor": {"name": "<name>", "license": "<license#>"}
  },
  "checkboxes": {
    "<checkbox_label>": true|false
  },
  "extraction_warnings": []
}
"""
```

### Document Type: Code Document / Standards

```python
CODE_DOCUMENT_PROMPT = """
You are analyzing a page from a building code or standard document. Extract the code requirements.

CRITICAL RULES:
- Preserve exact article/section numbering
- Capture the complete text of each requirement
- Note any exceptions or conditions
- Identify cross-references to other sections
- Mark table data separately from body text

EXTRACT:
1. Section/Article numbers with hierarchy
2. Requirement text verbatim
3. Any numerical values with units
4. Exceptions and conditions
5. References to other sections or standards
6. Table data if present

RESPOND IN THIS EXACT JSON FORMAT:
{
  "document_info": {
    "code_name": "<code name>",
    "section": "<section number>",
    "page": "<page number if visible>"
  },
  "articles": [
    {
      "number": "<article number, e.g., 9.8.4.1>",
      "title": "<article title if present>",
      "text": "<full requirement text>",
      "values": [
        {"description": "<what the value is for>", "value": <number>, "unit": "<unit>"}
      ],
      "conditions": ["<condition 1>", "<condition 2>"],
      "exceptions": ["<exception 1>"],
      "references": ["<9.10.1.2>", "<CSA A123>"]
    }
  ],
  "tables": [
    {
      "table_number": "<table id>",
      "title": "<table title>",
      "columns": ["<col1>", "<col2>"],
      "rows": [
        {"<col1>": "<value>", "<col2>": "<value>"}
      ]
    }
  ]
}
"""
```

### VLM Service Implementation

```python
# services/vlm/extraction_service.py

from enum import Enum
from typing import Optional
import httpx
from pydantic import BaseModel

class DocumentType(Enum):
    FLOOR_PLAN = "floor_plan"
    ELEVATION = "elevation"
    SECTION = "section"
    SITE_PLAN = "site_plan"
    TITLE_BLOCK = "title_block"
    PERMIT_FORM = "permit_form"
    CODE_DOCUMENT = "code_document"
    DETAIL = "detail"
    SCHEDULE = "schedule"

# Prompt registry
EXTRACTION_PROMPTS = {
    DocumentType.FLOOR_PLAN: FLOOR_PLAN_EXTRACTION_PROMPT,
    DocumentType.SECTION: SECTION_EXTRACTION_PROMPT,
    DocumentType.SITE_PLAN: SITE_PLAN_EXTRACTION_PROMPT,
    DocumentType.TITLE_BLOCK: TITLE_BLOCK_PROMPT,
    DocumentType.PERMIT_FORM: PERMIT_FORM_EXTRACTION_PROMPT,
    DocumentType.CODE_DOCUMENT: CODE_DOCUMENT_PROMPT,
}

class VLMService:
    """Service for interacting with the Qwen3-VL server."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "qwen3-vl:8b"
        self.client = httpx.AsyncClient(timeout=120.0)

    async def classify_document(self, image_bytes: bytes) -> DocumentType:
        """First pass: Identify what type of document this is."""

        classification_prompt = """
        Analyze this image and classify the document type.

        Respond with ONLY ONE of these exact values:
        - FLOOR_PLAN (if showing room layouts from above)
        - ELEVATION (if showing building face/facade)
        - SECTION (if showing vertical cut through building)
        - SITE_PLAN (if showing lot/property with building placement)
        - TITLE_BLOCK (if showing just the title block area)
        - PERMIT_FORM (if a form with fillable fields)
        - CODE_DOCUMENT (if text from a code/standard)
        - DETAIL (if showing construction detail)
        - SCHEDULE (if showing door/window/finish schedule)

        Respond with just the classification, nothing else.
        """

        response = await self._query_vlm(image_bytes, classification_prompt)

        # Parse response to DocumentType
        for doc_type in DocumentType:
            if doc_type.value.upper() in response.upper():
                return doc_type

        return DocumentType.FLOOR_PLAN  # Default fallback

    async def extract_data(
        self,
        image_bytes: bytes,
        document_type: DocumentType,
        additional_context: Optional[str] = None
    ) -> dict:
        """Extract structured data from document using appropriate prompt."""

        prompt = EXTRACTION_PROMPTS.get(document_type, FLOOR_PLAN_EXTRACTION_PROMPT)

        if additional_context:
            prompt = f"{prompt}\n\nADDITIONAL CONTEXT:\n{additional_context}"

        response = await self._query_vlm(image_bytes, prompt)

        # Parse JSON from response
        return self._parse_json_response(response)

    async def verify_specific_value(
        self,
        image_bytes: bytes,
        field_name: str,
        expected_location: str
    ) -> dict:
        """Focused extraction of a single value for verification."""

        prompt = f"""
        Look at this drawing and find the specific value for: {field_name}

        Expected location on drawing: {expected_location}

        RESPOND WITH ONLY:
        {{
          "field": "{field_name}",
          "value": <the value you find>,
          "unit": "<unit>",
          "confidence": "HIGH|MEDIUM|LOW",
          "location_description": "<where on the drawing you found it>"
        }}

        If you cannot find this specific value, respond:
        {{
          "field": "{field_name}",
          "value": null,
          "confidence": "NOT_FOUND",
          "reason": "<why you couldn't find it>"
        }}
        """

        response = await self._query_vlm(image_bytes, prompt)
        return self._parse_json_response(response)

    async def _query_vlm(self, image_bytes: bytes, prompt: str) -> str:
        """Send request to Ollama/vLLM server."""

        import base64
        image_b64 = base64.b64encode(image_bytes).decode()

        # Ollama API format
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for accuracy
                "num_predict": 4096
            }
        }

        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()

        return response.json()["response"]

    def _parse_json_response(self, response: str) -> dict:
        """Extract JSON from VLM response."""
        import json
        import re

        # Try to find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Return raw response if JSON parsing fails
        return {"raw_response": response, "parse_error": True}


# Usage example
async def process_drawing(file_path: str):
    """Example of processing a drawing through the VLM pipeline."""

    vlm = VLMService()

    with open(file_path, "rb") as f:
        image_bytes = f.read()

    # Step 1: Classify document type
    doc_type = await vlm.classify_document(image_bytes)
    print(f"Document classified as: {doc_type.value}")

    # Step 2: Extract data with appropriate prompt
    data = await vlm.extract_data(image_bytes, doc_type)
    print(f"Extracted data: {data}")

    # Step 3: Flag low-confidence items for human review
    items_for_review = []
    for field, info in data.get("dimensions", {}).items():
        if isinstance(info, dict) and info.get("confidence") in ["LOW", "MEDIUM"]:
            items_for_review.append({
                "field": field,
                "extracted_value": info.get("value"),
                "confidence": info.get("confidence")
            })

    return {
        "document_type": doc_type.value,
        "extracted_data": data,
        "requires_review": items_for_review
    }
```

### Confidence Scoring and Human Review Workflow

```python
# services/verification/confidence_handler.py

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class ConfidenceLevel(Enum):
    HIGH = "HIGH"           # >90% - Auto-accept
    MEDIUM = "MEDIUM"       # 70-90% - Flag for review
    LOW = "LOW"             # 50-70% - Require verification
    NOT_FOUND = "NOT_FOUND" # Value couldn't be extracted
    CRITICAL = "CRITICAL"   # Life-safety value - always verify

# Fields that ALWAYS require human verification regardless of confidence
CRITICAL_FIELDS = {
    "stair_width",
    "stair_headroom",
    "egress_window_area",
    "fire_separation_rating",
    "corridor_width",
    "exit_door_width",
    "guardrail_height",
    "handrail_height",
    "riser_height",
    "tread_depth"
}

@dataclass
class ExtractionResult:
    field_name: str
    value: Optional[float]
    unit: str
    confidence: ConfidenceLevel
    source_location: str  # Where on drawing
    requires_review: bool
    review_reason: Optional[str]

def assess_extraction(field_name: str, extracted: dict) -> ExtractionResult:
    """Assess an extracted value and determine if review needed."""

    confidence = ConfidenceLevel(extracted.get("confidence", "LOW"))

    # Critical fields always require review
    if field_name in CRITICAL_FIELDS:
        return ExtractionResult(
            field_name=field_name,
            value=extracted.get("value"),
            unit=extracted.get("unit", "mm"),
            confidence=ConfidenceLevel.CRITICAL,
            source_location=extracted.get("location", ""),
            requires_review=True,
            review_reason="Life-safety critical dimension - verification required"
        )

    # Determine review requirement based on confidence
    requires_review = confidence in [
        ConfidenceLevel.LOW,
        ConfidenceLevel.NOT_FOUND,
        ConfidenceLevel.MEDIUM
    ]

    review_reason = None
    if confidence == ConfidenceLevel.NOT_FOUND:
        review_reason = "Value could not be extracted from drawing"
    elif confidence == ConfidenceLevel.LOW:
        review_reason = "Low confidence extraction - please verify"
    elif confidence == ConfidenceLevel.MEDIUM:
        review_reason = "Medium confidence - recommended to verify"

    return ExtractionResult(
        field_name=field_name,
        value=extracted.get("value"),
        unit=extracted.get("unit", "mm"),
        confidence=confidence,
        source_location=extracted.get("location", ""),
        requires_review=requires_review,
        review_reason=review_reason
    )
```

---

## DSSP Module: Development Site Servicing Plan Designer

### Overview

The DSSP (Development Site Servicing Plan) Module is a comprehensive engineering design tool that automates the calculation, design, and documentation of site servicing requirements for development projects in Calgary, Alberta. This module integrates with the Guide and Review modes to provide complete site servicing design capabilities.

**Purpose**: Enable users to design compliant Development Site Servicing Plans by:
1. Automating stormwater, sanitary, and water service calculations
2. Generating required DSSP drawings and documentation
3. Ensuring compliance with City of Calgary standards
4. Producing submission-ready packages

### Applicable Standards and Codes

#### Primary Calgary Standards
| Standard | Version | Purpose |
|----------|---------|---------|
| **DSSP Design Guidelines** | 2018 | Submission requirements, drafting standards |
| **Stormwater Management & Design Manual** | 2011 | Stormwater calculations, retention sizing |
| **Standard Specifications for Sewer Construction** | 2025 | Sanitary sewer design, pipe specs |
| **Standard Specifications for Waterworks Construction** | 2025 | Water service design, pipe specs |
| **Subdivision Servicing Guidelines** | 2020 | Infrastructure requirements |
| **Land Use Bylaw 1P2007** | Current | Zoning, lot coverage, grading |

#### Alberta Provincial Standards
| Standard | Version | Purpose |
|----------|---------|---------|
| **Alberta Stormwater Management Guidelines** | 1999/2013 | Provincial drainage requirements |
| **Standards for Municipal Waterworks, Wastewater** | 2013 | Part 4: Wastewater systems |
| **Alberta Private Sewage Systems Standard of Practice** | 2021 | Rural/private systems |

#### Reference Standards
| Standard | Purpose |
|----------|---------|
| **AWWA C-Series** | Pipe and fitting standards |
| **CSA B64** | Backflow prevention |
| **ASTM Standards** | Material specifications |

### Module Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DSSP MODULE                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐           │
│  │  INPUT MODULE   │   │ CALCULATION     │   │  OUTPUT MODULE  │           │
│  │                 │──▶│    ENGINE       │──▶│                 │           │
│  │ • Site data     │   │                 │   │ • DSSP Drawings │           │
│  │ • Zoning        │   │ • Stormwater    │   │ • Calculations  │           │
│  │ • Survey        │   │ • Sanitary      │   │ • Reports       │           │
│  │ • Soil data     │   │ • Water         │   │ • Checklists    │           │
│  └─────────────────┘   │ • Grading       │   └─────────────────┘           │
│                        └─────────────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    STANDARDS DATABASE                                │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  Calgary IDF Curves │ Pipe Sizing Tables │ Material Specs │ Fees    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Input Requirements

#### 1. Site Information (Required)
| Input | Description | Source | Units |
|-------|-------------|--------|-------|
| `site_address` | Civic address | User input | string |
| `legal_description` | Plan, Block, Lot | User input | string |
| `site_area` | Total lot area | Survey/input | m² |
| `lot_width` | Lot frontage | Survey | m |
| `lot_depth` | Lot depth | Survey | m |
| `zoning_district` | Land use designation | Auto from address | string |
| `development_type` | Residential/Commercial/Mixed | User input | enum |

#### 2. Proposed Development (Required)
| Input | Description | Units |
|-------|-------------|-------|
| `building_footprint` | Ground floor area | m² |
| `total_floor_area` | All floors combined | m² |
| `building_height` | Height above grade | m |
| `num_storeys` | Number of floors | integer |
| `num_dwelling_units` | For residential | integer |
| `num_occupants` | Design population | integer |
| `parking_stalls` | Number of stalls | integer |
| `landscaped_area` | Soft landscape | m² |
| `impervious_area` | Hard surfaces | m² |

#### 3. Existing Infrastructure (Required)
| Input | Description | Source |
|-------|-------------|--------|
| `storm_sewer_location` | Connection point | City records |
| `storm_sewer_size` | Existing pipe diameter | mm |
| `storm_sewer_invert` | Invert elevation | m |
| `sanitary_sewer_location` | Connection point | City records |
| `sanitary_sewer_size` | Existing pipe diameter | mm |
| `sanitary_sewer_invert` | Invert elevation | m |
| `water_main_location` | Connection point | City records |
| `water_main_size` | Existing pipe diameter | mm |
| `water_pressure` | Available pressure | kPa |

#### 4. Site Conditions (Required)
| Input | Description | Units |
|-------|-------------|-------|
| `existing_grade_high` | Highest point | m (geodetic) |
| `existing_grade_low` | Lowest point | m (geodetic) |
| `soil_type` | Predominant soil | enum |
| `groundwater_level` | Depth to water table | m below grade |
| `percolation_rate` | Soil permeability | mm/hr |
| `geotechnical_report` | Report reference | boolean |

#### 5. Stormwater Options (User Selection)
| Input | Description | Options |
|-------|-------------|---------|
| `sw_strategy` | Management approach | conventional / LID / hybrid |
| `outlet_type` | Discharge method | storm_sewer / overland / infiltration |
| `storage_type` | Detention type | surface / underground / green_roof |
| `quality_device` | Water quality BMP | oil_grit / bioswale / none |

---

### Calculation Engine

#### A. Stormwater Calculations

##### A.1 Rational Method (Sites ≤ 5 ha)
```
Q = C × i × A / 360

Where:
  Q = Peak runoff (m³/s)
  C = Runoff coefficient (dimensionless)
  i = Rainfall intensity (mm/hr)
  A = Drainage area (ha)
```

**Calgary Runoff Coefficients (C)**
| Surface Type | C Value |
|--------------|---------|
| Roofs | 0.90 |
| Asphalt/Concrete | 0.85 |
| Gravel surfaces | 0.50 |
| Lawns (flat, <2%) | 0.17 |
| Lawns (sloped, 2-7%) | 0.22 |
| Landscaped areas | 0.20 |
| Natural areas | 0.15 |

**Composite Runoff Coefficient**
```
C_composite = Σ(C_i × A_i) / A_total
```

##### A.2 Calgary IDF Curves (Intensity-Duration-Frequency)
Based on Calgary International Airport rainfall data:

```
For Calgary (Climate Zone 7A):

i = a / (t + b)^c

Where for return periods:
  2-year:  a = 820,  b = 7.0,  c = 0.81
  5-year:  a = 1040, b = 7.2,  c = 0.82
  10-year: a = 1180, b = 7.3,  c = 0.82
  25-year: a = 1380, b = 7.5,  c = 0.83
  100-year: a = 1680, b = 7.8, c = 0.84

  t = time of concentration (minutes)
  i = intensity (mm/hr)
```

##### A.3 Time of Concentration
```
Tc = Ti + Tt

Where:
  Ti = Inlet time (minimum 10 minutes for urban Calgary)
  Tt = Travel time in pipe/channel

Tt = L / (60 × V)
  L = flow length (m)
  V = velocity (m/s)
```

##### A.4 Retention/Detention Pond Sizing

**Volume for Water Quality (Calgary Requirement)**
```
V_quality = 25 mm × A_total × C_composite / 1000

Where:
  V_quality = Permanent pool volume (m³)
  A_total = Total drainage area (m²)
  C_composite = Overall runoff coefficient
```

**Volume for Flood Control**
```
V_flood = (Q_in - Q_out) × Δt × 60

Where:
  V_flood = Storage volume required (m³)
  Q_in = Inflow rate (m³/s)
  Q_out = Allowable release rate (m³/s)
  Δt = Storm duration (minutes)
```

**Pre-Development Release Rate (Calgary)**
```
Q_release = 1.5 L/s/ha (typical greenfield)
         = 2.0 L/s/ha (urban infill)
```

##### A.5 Inlet Control Device (ICD) Sizing
```
Q = C_d × A × √(2 × g × h)

Where:
  Q = Flow through orifice (m³/s)
  C_d = Discharge coefficient (0.61 for sharp-edged)
  A = Orifice area (m²)
  g = 9.81 m/s²
  h = Head above centerline (m)
```

##### A.6 Storm Pipe Sizing (Manning's Equation)
```
Q = (1/n) × A × R^(2/3) × S^(1/2)

Where:
  Q = Flow capacity (m³/s)
  n = Manning's roughness (0.013 for PVC/HDPE)
  A = Cross-sectional area (m²)
  R = Hydraulic radius = A/P (m)
  P = Wetted perimeter (m)
  S = Slope (m/m)

Minimum pipe sizes:
  Private: 150 mm
  Public: 300 mm
Minimum velocity: 0.6 m/s (self-cleaning)
Maximum velocity: 4.5 m/s
```

---

#### B. Sanitary Sewer Calculations

##### B.1 Population and Flow Estimation

**Population Density by Zoning (Calgary)**
| Zone | Density (persons/unit) | Units/ha |
|------|----------------------|----------|
| R-C1 | 2.8 | 12-18 |
| R-C2 | 2.8 | 25-35 |
| M-CG | 2.5 | 40-80 |
| M-H1 | 2.2 | 100-200 |
| Commercial | - | By fixture count |

**Unit Flows**
```
Residential: 350 L/person/day (average)
Commercial: 30 L/m² GFA/day
Industrial: Project-specific
```

##### B.2 Design Flow Calculations

**Average Daily Flow (ADF)**
```
ADF = P × q_avg / 86,400

Where:
  ADF = Average daily flow (L/s)
  P = Population (persons)
  q_avg = Per capita flow (L/person/day)
```

**Peak Dry Weather Flow (PDWF)**
```
PDWF = ADF × PF

Peaking Factor (Harmon Formula):
  PF = 1 + 14 / (4 + √P)

Where:
  P = Population in thousands
  PF typically ranges 2.5 to 4.0
```

**Peak Wet Weather Flow (PWWF)**
```
PWWF = PDWF + I/I

Infiltration/Inflow (new development):
  I/I = 0.15 L/s/ha (Calgary standard)

For areas pre-1990:
  I/I = 0.3 to 0.5 L/s/ha (includes foundation drains)
```

##### B.3 Sanitary Pipe Sizing (Manning's Equation)
```
Same formula as storm, with:
  n = 0.013 (all pipe types)

Design Criteria:
  Minimum size: 200 mm
  Maximum depth for d/D: 0.80 (80% full)
  Minimum velocity: 0.6 m/s
  Maximum velocity: 3.0 m/s
  Minimum cover: 2.5 m (or insulated)
  Maximum service depth: 6.0 m
```

##### B.4 Manhole Spacing
| Pipe Diameter | Maximum Spacing |
|---------------|-----------------|
| 200-375 mm | 120 m |
| 450-900 mm | 150 m |
| > 900 mm | 180 m |

---

#### C. Water Service Calculations

##### C.1 Domestic Demand
```
Residential:
  Peak hour = 1.5 L/s per dwelling unit
  Daily = 350 L/person/day

Commercial:
  By fixture unit count (CSA B64)
```

##### C.2 Fire Flow Requirements (Calgary Fire Dept)
| Building Type | Minimum Fire Flow | Duration |
|---------------|------------------|----------|
| Single family residential | 60 L/s | 1 hour |
| Multi-family (≤6 units) | 90 L/s | 1 hour |
| Multi-family (>6 units) | 120 L/s | 2 hours |
| Commercial (sprinklered) | 150 L/s | 2 hours |
| Commercial (unsprinklered) | 200 L/s | 2 hours |

##### C.3 Service Line Sizing
| Dwelling Units | Minimum Service Size |
|----------------|---------------------|
| 1 | 19 mm (3/4") |
| 2-4 | 25 mm (1") |
| 5-10 | 38 mm (1.5") |
| >10 | Engineering required |

##### C.4 Pressure Requirements
```
Minimum static: 275 kPa (40 psi)
Minimum residual: 140 kPa (20 psi) at peak flow
Maximum static: 550 kPa (80 psi)
```

---

#### D. Grading Calculations

##### D.1 Minimum Grades
| Surface | Minimum Slope |
|---------|---------------|
| Pavement (to drain) | 1.0% |
| Landscaped areas | 2.0% |
| Swales | 1.0% |
| Away from buildings | 2% for 1.5m, then 1% |

##### D.2 Lot Drainage
```
Split Drainage:
  40-60% front : 60-40% rear (preferred)

Trap Low:
  Maximum depth: 0.3 m
  Minimum area: 25 m²
  Inlet capacity per IDF curves
```

##### D.3 Building Grades
```
Foundation drain elevation > property line drainage swale
Garage floor ≥ 150 mm above property line
Main floor ≥ 450 mm above property line (Calgary)
```

---

### Output Deliverables

#### Required DSSP Drawing Package

##### Sheet 1: Site Servicing Plan (1:200 or 1:500)
**Contents:**
- Property boundaries with dimensions
- Building footprint with setbacks
- All underground utilities:
  - Storm sewer (green)
  - Sanitary sewer (brown/orange)
  - Water service (blue)
  - Gas (yellow) - noted only
  - Power/telecom - noted only
- Pipe sizes, materials, slopes
- Manholes, cleanouts, valves
- Connection points to City mains
- Easements and right-of-ways
- North arrow, scale, legend

##### Sheet 2: Grading Plan (1:200 or 1:500)
**Contents:**
- Existing contours (dashed)
- Proposed contours (solid)
- Spot elevations at key points:
  - Building corners
  - Property corners
  - Grade breaks
  - Drainage structures
- Drainage arrows
- Retaining walls (if any)
- Trap low locations
- Overland flow routes
- Cross-sections references

##### Sheet 3: Stormwater Management Plan (1:200 or 1:500)
**Contents:**
- Catchment areas delineated
- Area and C-value for each catchment
- Storage facilities (ponds, tanks)
- Outlet structures
- Water quality devices
- Overland escape routes
- Emergency overflow paths
- Stormwater calculations summary table

##### Sheet 4: Details (NTS)
**Contents:**
- Typical trench details
- Manhole details
- Service connection details
- ICD detail (if applicable)
- Oil-grit separator detail (if applicable)
- Backwater valve detail
- Standard City details referenced

##### Sheet 5: Architectural Floor Plan (From Architect)
**Contents:**
- Water meter room location
- Fire department connection
- Fire suppression layout (if sprinklered)
- Backflow preventer location

##### Circulation Block (Required on Sheet 1)
```
┌──────────────────────────────────────────────────────┐
│ DRAWING CIRCULATION                                  │
├──────────────────────────────────────────────────────┤
│ REV │ DESCRIPTION  │ FOR DP │ FOR APPROVAL │ ARCHIVE│
├─────┼──────────────┼────────┼──────────────┼────────┤
│  0  │ Initial      │   □    │      □       │   □    │
│  1  │              │   □    │      □       │   □    │
│  2  │              │   □    │      □       │   □    │
└──────────────────────────────────────────────────────┘
```

#### Supporting Documents

##### Stormwater Management Report (Required for certain sites)
**Trigger Conditions:**
- No storm sewer connection available
- Zero discharge sites
- Sites with retention ponds
- Flagged by Water Resources

**Contents:**
1. Site description and location
2. Pre-development conditions
3. Post-development conditions
4. Hydrology calculations
5. Hydraulic modeling results
6. Storage sizing calculations
7. Water quality measures
8. Maintenance plan

##### Sanitary Servicing Study (For larger developments)
**Trigger Conditions:**
- Developments > 100 units
- Capacity concerns identified
- New trunk sewer connections

**Contents:**
1. Population projections
2. Flow calculations
3. Downstream capacity analysis
4. Phasing plan

##### Calculation Package
**Contents:**
- Storm catchment areas and C-values
- IDF curve calculations
- Retention volume calculations
- ICD/outlet sizing
- Pipe sizing worksheets
- Sanitary flow calculations
- Water demand calculations

---

### DSSP Module Database Tables

```sql
-- DSSP Project Table
CREATE TABLE dssp_projects (
    id UUID PRIMARY KEY,
    permit_application_id UUID REFERENCES permit_applications(id),
    project_name VARCHAR(255) NOT NULL,
    site_address VARCHAR(255) NOT NULL,
    legal_description VARCHAR(100),
    site_area_m2 DECIMAL(10,2),
    zoning_district VARCHAR(20),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Site Inputs Table
CREATE TABLE dssp_site_inputs (
    id UUID PRIMARY KEY,
    dssp_project_id UUID REFERENCES dssp_projects(id),
    lot_width_m DECIMAL(8,2),
    lot_depth_m DECIMAL(8,2),
    impervious_area_m2 DECIMAL(10,2),
    pervious_area_m2 DECIMAL(10,2),
    building_footprint_m2 DECIMAL(10,2),
    num_dwelling_units INTEGER,
    design_population INTEGER,
    existing_grade_high_m DECIMAL(8,3),
    existing_grade_low_m DECIMAL(8,3),
    soil_type VARCHAR(50),
    groundwater_depth_m DECIMAL(6,2),
    storm_sewer_size_mm INTEGER,
    storm_sewer_invert_m DECIMAL(8,3),
    sanitary_sewer_size_mm INTEGER,
    sanitary_sewer_invert_m DECIMAL(8,3),
    water_main_size_mm INTEGER,
    water_pressure_kpa DECIMAL(6,1),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Stormwater Calculations Table
CREATE TABLE dssp_stormwater_calcs (
    id UUID PRIMARY KEY,
    dssp_project_id UUID REFERENCES dssp_projects(id),
    catchment_id VARCHAR(10),
    catchment_area_m2 DECIMAL(10,2),
    runoff_coefficient DECIMAL(4,3),
    time_concentration_min DECIMAL(6,2),
    intensity_2yr_mm_hr DECIMAL(6,2),
    intensity_5yr_mm_hr DECIMAL(6,2),
    intensity_100yr_mm_hr DECIMAL(6,2),
    peak_flow_2yr_m3s DECIMAL(8,4),
    peak_flow_100yr_m3s DECIMAL(8,4),
    retention_volume_m3 DECIMAL(8,2),
    release_rate_ls DECIMAL(8,3),
    outlet_type VARCHAR(50),
    icd_diameter_mm INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sanitary Calculations Table
CREATE TABLE dssp_sanitary_calcs (
    id UUID PRIMARY KEY,
    dssp_project_id UUID REFERENCES dssp_projects(id),
    population INTEGER,
    avg_daily_flow_ls DECIMAL(8,4),
    peaking_factor DECIMAL(4,2),
    peak_dry_weather_flow_ls DECIMAL(8,4),
    infiltration_ls DECIMAL(8,4),
    peak_wet_weather_flow_ls DECIMAL(8,4),
    pipe_size_mm INTEGER,
    pipe_slope_pct DECIMAL(6,4),
    velocity_ms DECIMAL(6,3),
    depth_ratio DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Water Calculations Table
CREATE TABLE dssp_water_calcs (
    id UUID PRIMARY KEY,
    dssp_project_id UUID REFERENCES dssp_projects(id),
    domestic_demand_ls DECIMAL(8,4),
    fire_flow_ls DECIMAL(8,2),
    total_demand_ls DECIMAL(8,4),
    service_size_mm INTEGER,
    meter_size_mm INTEGER,
    backflow_required BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- DSSP Drawings Table
CREATE TABLE dssp_drawings (
    id UUID PRIMARY KEY,
    dssp_project_id UUID REFERENCES dssp_projects(id),
    sheet_number INTEGER,
    sheet_type VARCHAR(50),  -- 'site_servicing', 'grading', 'stormwater', 'details', 'floor_plan'
    drawing_file_path VARCHAR(500),
    drawing_format VARCHAR(20),  -- 'pdf', 'dwg', 'dxf'
    revision INTEGER DEFAULT 0,
    status VARCHAR(50),  -- 'draft', 'for_dp', 'for_approval', 'approved'
    created_at TIMESTAMP DEFAULT NOW()
);

-- IDF Curves Table (Calgary)
CREATE TABLE idf_curves (
    id UUID PRIMARY KEY,
    location VARCHAR(100) DEFAULT 'Calgary',
    return_period_years INTEGER,
    duration_minutes INTEGER,
    intensity_mm_hr DECIMAL(8,2),
    source VARCHAR(255),
    effective_date DATE
);
```

---

### DSSP Module API Endpoints

```
POST   /api/v1/dssp/projects                    Create new DSSP project
GET    /api/v1/dssp/projects/{id}               Get project details
PUT    /api/v1/dssp/projects/{id}               Update project

POST   /api/v1/dssp/{id}/site-inputs            Save site inputs
GET    /api/v1/dssp/{id}/site-inputs            Get site inputs

POST   /api/v1/dssp/{id}/calculate/stormwater   Run stormwater calculations
POST   /api/v1/dssp/{id}/calculate/sanitary     Run sanitary calculations
POST   /api/v1/dssp/{id}/calculate/water        Run water service calculations
POST   /api/v1/dssp/{id}/calculate/all          Run all calculations

GET    /api/v1/dssp/{id}/results                Get all calculation results
GET    /api/v1/dssp/{id}/results/stormwater     Get stormwater results
GET    /api/v1/dssp/{id}/results/sanitary       Get sanitary results

POST   /api/v1/dssp/{id}/generate/drawings      Generate DSSP drawings
GET    /api/v1/dssp/{id}/drawings               List drawings
GET    /api/v1/dssp/{id}/drawings/{sheet}       Download specific drawing

POST   /api/v1/dssp/{id}/generate/report        Generate calculation report
GET    /api/v1/dssp/{id}/report                 Download report

POST   /api/v1/dssp/{id}/submit                 Submit for review
GET    /api/v1/dssp/{id}/checklist              Get submission checklist

GET    /api/v1/dssp/idf-curves                  Get Calgary IDF data
GET    /api/v1/dssp/pipe-tables                 Get pipe sizing tables
GET    /api/v1/dssp/runoff-coefficients         Get C-value tables
```

---

### DSSP Module UI Components

#### 1. Project Setup Wizard
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DSSP DESIGNER - Step 1 of 5: Site Information                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Site Address: [123 Example Street NW                              ] [🔍]   │
│                                                                              │
│  Legal Description: Plan [1234567] Block [12] Lot [34]                      │
│                                                                              │
│  Site Area:        [1,250    ] m²     (auto-calculated from parcel data)   │
│  Lot Width:        [12.5     ] m                                            │
│  Lot Depth:        [100      ] m                                            │
│                                                                              │
│  Zoning District:  [R-C2    ▼]  (auto-detected: Residential - Contextual)  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        SITE LOCATION MAP                               │ │
│  │                     [Interactive Map View]                             │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│                                              [Back]  [Save & Continue →]    │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2. Calculation Dashboard
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DSSP DESIGNER - Calculation Results                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │  STORMWATER         │  │  SANITARY           │  │  WATER SERVICE      │  │
│  │  ✓ Calculated       │  │  ✓ Calculated       │  │  ✓ Calculated       │  │
│  ├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤  │
│  │ Total Area: 1,250m² │  │ Population: 8       │  │ Demand: 1.2 L/s     │  │
│  │ Composite C: 0.65   │  │ PDWF: 0.45 L/s      │  │ Fire Flow: 60 L/s   │  │
│  │ Q100: 0.082 m³/s    │  │ PWWF: 0.63 L/s      │  │ Service: 25mm       │  │
│  │ Storage: 31.3 m³    │  │ Pipe: 200mm         │  │ Meter: 19mm         │  │
│  │ Release: 1.88 L/s   │  │ Slope: 0.50%        │  │                     │  │
│  │ ICD: 75mm orifice   │  │ Velocity: 0.72 m/s  │  │ Backflow: Required  │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  CATCHMENT DIAGRAM                                                      ││
│  │  [Visual representation of drainage areas with flow arrows]             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  [Recalculate]  [View Details]  [Export Calculations]  [Generate Drawings]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3. Drawing Generator
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DSSP DESIGNER - Drawing Generation                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Select Drawings to Generate:                                               │
│                                                                              │
│  ☑ Sheet 1: Site Servicing Plan (1:200)                      [Preview]     │
│  ☑ Sheet 2: Grading Plan (1:200)                             [Preview]     │
│  ☑ Sheet 3: Stormwater Management Plan (1:200)               [Preview]     │
│  ☑ Sheet 4: Details                                          [Preview]     │
│  ☐ Sheet 5: Floor Plan (upload from architect)               [Upload]      │
│                                                                              │
│  Drawing Options:                                                           │
│  Paper Size: [600mm × 900mm ▼]    Scale: [1:200 ▼]                         │
│  Format: ○ PDF  ○ DWG  ○ Both                                              │
│                                                                              │
│  Title Block Information:                                                   │
│  Project Name: [Smith Residence                                    ]        │
│  Engineer: [ABC Engineering Ltd.                                   ]        │
│  Date: [2026-01-10]                                                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  DRAWING PREVIEW                                                        ││
│  │  [Sheet 1: Site Servicing Plan]                                        ││
│  │                                                                         ││
│  │  ┌─────────┐                                                            ││
│  │  │ BLDG    │──── STORM ────▶ TO MH                                     ││
│  │  │         │──── SANITARY ─▶ TO MH                                     ││
│  │  │         │──── WATER ────▶ FROM MAIN                                 ││
│  │  └─────────┘                                                            ││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│                               [Generate All Drawings]  [Download Package]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Implementation Phases for DSSP Module

#### Phase D1: Core Calculations (4 weeks)
- [ ] Implement stormwater calculation engine
- [ ] Implement sanitary calculation engine
- [ ] Implement water service calculation engine
- [ ] Load Calgary IDF curves into database
- [ ] Create calculation API endpoints
- [ ] Unit tests for all formulas

#### Phase D2: Input Interface (3 weeks)
- [ ] Build project setup wizard
- [ ] Integrate with address/parcel lookup
- [ ] Connect to existing infrastructure data
- [ ] Save/load project functionality
- [ ] Input validation rules

#### Phase D3: Drawing Generation (5 weeks)
- [ ] Design CAD template system
- [ ] Implement site servicing plan generator
- [ ] Implement grading plan generator
- [ ] Implement stormwater plan generator
- [ ] Implement detail sheet generator
- [ ] PDF and DWG export

#### Phase D4: Reports & Submission (2 weeks)
- [ ] Calculation report generator
- [ ] Stormwater management report template
- [ ] DSSP checklist integration
- [ ] Submission package bundler
- [ ] Fee calculation integration

---

### References

#### City of Calgary
- [DSSP Design Guidelines (2018)](https://www.calgary.ca/content/dam/www/pda/pd/documents/urban-development/publications/dssp-design-guidelines.pdf)
- [Stormwater Management & Design Manual (2011)](https://www.calgary.ca/content/dam/www/pda/pd/documents/urban-development/bulletins/2011-stormwater-management-and-design.pdf)
- [Water Development Resources](https://www.calgary.ca/development/home-building/water-development-process.html)
- [Water Guidelines & Specifications](https://www.calgary.ca/development/home-building/water-development-specifications.html)

#### Alberta Provincial
- [Stormwater Management Guidelines (1999)](https://open.alberta.ca/publications/0773251499)
- [Standards for Municipal Wastewater Systems (2013)](https://open.alberta.ca/dataset/f57fec02-7de8-4985-b948-dcf5e2664aee)

---

## Quantity Survey Module: Construction Cost Estimation

### Overview

The Quantity Survey (QS) module provides construction cost estimation capabilities for Calgary projects. This module directly integrates with the permit fee calculator since Calgary permit fees are based on **construction value** ($10.14 per $1,000 for building permits, $9.79 per $1,000 for trade permits).

### Purpose & Integration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    QUANTITY SURVEY MODULE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐    ┌──────────────┐    ┌───────────────────┐        │
│   │   Project    │───▶│   Quantity   │───▶│  Construction     │        │
│   │   Details    │    │   Take-off   │    │  Cost Estimate    │        │
│   └──────────────┘    └──────────────┘    └─────────┬─────────┘        │
│                                                      │                   │
│                                                      ▼                   │
│   ┌──────────────────────────────────────────────────────────┐         │
│   │                    OUTPUT PRODUCTS                        │         │
│   ├──────────────┬──────────────┬────────────┬───────────────┤         │
│   │ Construction │ Permit Fee   │ Bill of    │ Cost          │         │
│   │ Value        │ Calculation  │ Quantities │ Breakdown     │         │
│   └──────────────┴──────────────┴────────────┴───────────────┘         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Calgary Construction Cost Data (2025-2026)

#### Residential Construction Costs ($/sq.ft)

| Category | Standard | Mid-Range | Premium | Luxury |
|----------|----------|-----------|---------|--------|
| Single Family | $200-250 | $250-300 | $300-400 | $400-600+ |
| Townhouse | $180-220 | $220-280 | $280-350 | $350-500 |
| Multi-Family Low Rise | $200-240 | $240-300 | $300-380 | $380-500 |
| Multi-Family High Rise | $250-300 | $300-380 | $380-480 | $480-700+ |
| Secondary Suite | $150-200 | $200-250 | $250-350 | - |
| Backyard Suite (ADU) | $250-300 | $300-400 | $400-500 | - |

#### Commercial Construction Costs ($/sq.ft)

| Category | Budget | Standard | Premium |
|----------|--------|----------|---------|
| Office - Core & Shell | $180-220 | $220-285 | $285-430 |
| Office - Fit-out | $80-120 | $120-150 | $150-250 |
| Retail - Strip Mall | $140-170 | $170-205 | $205-280 |
| Retail - Shopping Centre | $240-280 | $280-325 | $325-450 |
| Hotel - 3 Star | $235-250 | $250-265 | $265-320 |
| Hotel - 5 Star | $310-400 | $400-485 | $485-700 |
| Restaurant | $200-280 | $280-350 | $350-500 |

#### Industrial Construction Costs ($/sq.ft)

| Category | Light | Standard | Heavy |
|----------|-------|----------|-------|
| Warehouse | $90-130 | $110-170 | $140-220 |
| Manufacturing | $120-180 | $150-220 | $200-350 |
| Cold Storage | $180-250 | $220-300 | $280-400 |

#### Institutional Construction Costs ($/sq.ft)

| Category | Budget | Standard | Premium |
|----------|--------|----------|---------|
| Elementary School | $260-300 | $300-360 | $360-450 |
| High School | $280-340 | $340-400 | $400-500 |
| University/College | $345-420 | $420-525 | $525-700 |
| General Hospital | $700-800 | $800-950 | $950-1200+ |
| Medical Office | $280-350 | $350-420 | $420-550 |
| Community Centre | $250-320 | $320-400 | $400-500 |

### Input Requirements

#### 1. Project Information
- Project name and address
- Building type (residential, commercial, industrial, institutional)
- Building use classification
- New construction vs renovation

#### 2. Building Dimensions
- Gross floor area (sq.ft or m²)
- Number of storeys
- Building footprint
- Basement area (if applicable)
- Garage/parking area

#### 3. Construction Quality Level
- **Budget**: Basic materials, standard fixtures, minimal finishes
- **Standard**: Good quality materials, mid-range fixtures
- **Mid-Range**: Above-average materials, upgraded finishes
- **Premium**: High-quality materials, premium fixtures
- **Luxury**: Top-tier materials, custom finishes, high-end systems

#### 4. System Specifications
- Foundation type (slab, crawl space, full basement)
- Structural system (wood frame, steel, concrete)
- Exterior cladding (vinyl, stucco, brick, stone)
- Roofing type (asphalt, metal, flat membrane)
- Window quality level
- HVAC system type
- Electrical service size
- Plumbing fixture count

#### 5. Site Conditions
- Site access (easy, moderate, difficult)
- Soil conditions (if known)
- Demolition requirements
- Site grading requirements

### Calculation Methodology

#### Method 1: Square Foot Method (Quick Estimate - Class D)

```python
# Basic Square Foot Calculation
base_cost_psf = get_base_cost(building_type, quality_level)
location_factor = get_calgary_location_factor()  # ~1.0 for Calgary
complexity_factor = get_complexity_factor(num_storeys, shape)
condition_factor = get_site_condition_factor(access, soil)

estimated_cost = (
    gross_area *
    base_cost_psf *
    location_factor *
    complexity_factor *
    condition_factor
)

# Add soft costs (10-15%)
soft_costs = estimated_cost * 0.12  # Design, permits, contingency
total_project_cost = estimated_cost + soft_costs
```

#### Method 2: Assembly Cost Method (Detailed Estimate - Class C)

```python
# Assembly-Based Calculation
assemblies = {
    "foundation": foundation_cost_per_sf * footprint_area,
    "superstructure": structure_cost_per_sf * gross_area,
    "exterior_enclosure": envelope_cost_per_sf * envelope_area,
    "roofing": roof_cost_per_sf * roof_area,
    "interior_construction": interior_cost_per_sf * gross_area,
    "mechanical": mechanical_cost_per_sf * gross_area,
    "electrical": electrical_cost_per_sf * gross_area,
    "site_work": site_cost_per_sf * site_area,
}

subtotal = sum(assemblies.values())

# Markups
general_conditions = subtotal * 0.08  # 8%
overhead_profit = (subtotal + general_conditions) * 0.10  # 10%
contingency = (subtotal + general_conditions + overhead_profit) * 0.05  # 5%

total_construction_cost = subtotal + general_conditions + overhead_profit + contingency
```

#### Method 3: Unit Cost Method (Detailed BOQ - Class B)

This method requires detailed quantity take-offs for each CSI division.

### CSI MasterFormat Divisions

The module organizes costs by CSI MasterFormat divisions:

| Division | Description | Typical % of Total |
|----------|-------------|-------------------|
| 01 | General Requirements | 6-8% |
| 02 | Existing Conditions | 1-3% |
| 03 | Concrete | 8-15% |
| 04 | Masonry | 3-8% |
| 05 | Metals | 5-12% |
| 06 | Wood, Plastics, Composites | 8-15% |
| 07 | Thermal & Moisture Protection | 5-10% |
| 08 | Openings | 5-10% |
| 09 | Finishes | 10-18% |
| 10 | Specialties | 1-3% |
| 11 | Equipment | 0-5% |
| 12 | Furnishings | 0-3% |
| 21 | Fire Suppression | 1-3% |
| 22 | Plumbing | 5-10% |
| 23 | HVAC | 8-15% |
| 26 | Electrical | 8-15% |
| 31 | Earthwork | 2-5% |
| 32 | Exterior Improvements | 2-5% |
| 33 | Utilities | 2-5% |

### Output Deliverables

#### 1. Construction Cost Estimate Report
- Executive summary
- Methodology description
- Detailed cost breakdown by division
- Assumptions and exclusions
- Confidence level (Class A-E)

#### 2. Permit Fee Calculation
```
Building Permit Fee:
- Processing Fee: $112
- Base Fee: $10.14 × (Construction Value ÷ $1,000)
- Safety Codes Council Fee: 4% of Base Fee

Trade Permits (if separate):
- Processing Fee: $112
- Base Fee: $9.79 × (Construction Value ÷ $1,000)
- Safety Codes Council Fee: 4% of Base Fee
```

#### 3. Bill of Quantities (BOQ)
- Itemized list of materials and labor
- Quantities for each work item
- Unit prices and extended costs
- Suitable for tendering

#### 4. Cost Breakdown Visualization
- Pie chart by division
- Bar chart comparing to benchmarks
- Cost per square foot analysis

### Required Drawings for Quantity Survey

For accurate quantity take-offs, the following drawings are typically required:

#### Architectural Drawings
- Site plan with building footprint
- Floor plans (all levels)
- Building sections
- Exterior elevations
- Roof plan
- Door and window schedules
- Finish schedules

#### Structural Drawings
- Foundation plan
- Framing plans (floor, roof)
- Structural details
- Steel/concrete schedules

#### Mechanical Drawings
- HVAC plans and details
- Plumbing riser diagrams
- Equipment schedules

#### Electrical Drawings
- Power plans
- Lighting plans
- Panel schedules
- Electrical specifications

### Database Schema

```sql
-- Project cost estimation table
CREATE TABLE qs_projects (
    id UUID PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    building_type VARCHAR(50) NOT NULL,
    quality_level VARCHAR(20) NOT NULL,
    gross_area_sf NUMERIC(12,2) NOT NULL,
    num_storeys INTEGER,
    basement_area_sf NUMERIC(12,2),
    estimation_class CHAR(1) DEFAULT 'D',  -- A, B, C, D, E
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cost estimates by division
CREATE TABLE qs_division_costs (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES qs_projects(id),
    division_code VARCHAR(10) NOT NULL,
    division_name VARCHAR(255) NOT NULL,
    estimated_cost NUMERIC(14,2) NOT NULL,
    unit_cost_psf NUMERIC(10,2),
    notes TEXT
);

-- Line item details for BOQ
CREATE TABLE qs_line_items (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES qs_projects(id),
    division_code VARCHAR(10),
    item_code VARCHAR(50),
    description TEXT NOT NULL,
    quantity NUMERIC(14,4),
    unit VARCHAR(20),
    unit_cost NUMERIC(12,4),
    extended_cost NUMERIC(14,2),
    source VARCHAR(100)  -- RSMeans, local quote, etc.
);

-- Cost database (reference costs)
CREATE TABLE qs_cost_data (
    id UUID PRIMARY KEY,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),
    unit VARCHAR(20),
    material_cost NUMERIC(12,4),
    labor_cost NUMERIC(12,4),
    equipment_cost NUMERIC(12,4),
    total_unit_cost NUMERIC(12,4),
    location VARCHAR(50) DEFAULT 'Calgary',
    effective_date DATE,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assembly costs (for assembly method)
CREATE TABLE qs_assemblies (
    id UUID PRIMARY KEY,
    assembly_code VARCHAR(50) UNIQUE NOT NULL,
    assembly_name VARCHAR(255) NOT NULL,
    building_type VARCHAR(50),
    quality_level VARCHAR(20),
    unit VARCHAR(20),  -- SF, LF, EA, etc.
    cost_per_unit NUMERIC(12,4) NOT NULL,
    includes_labor BOOLEAN DEFAULT TRUE,
    includes_material BOOLEAN DEFAULT TRUE,
    effective_date DATE,
    source VARCHAR(100)
);

-- Historical cost indices
CREATE TABLE qs_cost_indices (
    id UUID PRIMARY KEY,
    period DATE NOT NULL,
    location VARCHAR(50) DEFAULT 'Calgary',
    index_value NUMERIC(8,2) NOT NULL,
    base_year INTEGER DEFAULT 2020,
    source VARCHAR(100)
);
```

### API Endpoints

```
# Quick Estimate
POST /api/v1/qs/quick-estimate
  Input: building_type, gross_area, quality_level, num_storeys
  Output: estimated_cost, cost_per_sf, permit_fees

# Detailed Estimate
POST /api/v1/qs/detailed-estimate
  Input: project details, system specifications
  Output: division breakdown, total cost, BOQ

# Get Cost Data
GET /api/v1/qs/cost-data?category=&building_type=
GET /api/v1/qs/assemblies?building_type=&quality=

# Generate Reports
POST /api/v1/qs/projects/{id}/report
  Output: PDF cost estimate report

# Permit Fee Calculator Integration
POST /api/v1/qs/permit-fee-calculation
  Input: construction_value
  Output: permit_fees breakdown
```

### UI Components

#### Quick Estimate Form
- Building type selector
- Quality level slider
- Area input
- Instant cost estimate display
- Permit fee preview

#### Detailed Estimate Wizard
- Step 1: Project information
- Step 2: Building dimensions
- Step 3: System specifications
- Step 4: Review and adjust
- Step 5: Generate reports

#### Cost Breakdown Dashboard
- Division-by-division cost display
- Interactive pie chart
- Comparison to benchmarks
- Export options (PDF, Excel)

### Data Sources

#### Primary Sources
- [RSMeans Data](https://www.rsmeans.com) - Industry standard cost database
- [Altus Group Canadian Cost Guide](https://www.altusgroup.com/featured-insights/canadian-cost-guide/) - Annual Canadian construction costs
- City of Calgary fee schedules
- Local contractor pricing

#### Updates Required
- Quarterly cost index updates
- Annual base cost review
- Material price volatility adjustments

### Reference Links

#### Industry Standards
- [CIQS - Canadian Institute of Quantity Surveyors](https://ciqs.org)
- [RICS - Royal Institution of Chartered Surveyors](https://www.rics.org)

#### Calgary Resources
- [Calgary Building Permit Fee Calculator](https://www.calgary.ca/development/permits/fee-calculators.html)
- [Calgary Construction Association](https://cgyca.com)

#### Cost Data
- [RSMeans Online](https://www.rsmeansonline.com)
- [Statistics Canada Building Construction Price Index](https://www150.statcan.gc.ca/n1/daily-quotidien/250204/dq250204b-eng.htm)

---

## Future Modules: Complete Permit Workflow Automation

This section outlines all planned modules organized by their position in the Calgary permit workflow. Each module represents an opportunity to automate calculations, generate documentation, or provide compliance analysis.

### Complete Permit Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     CALGARY PERMIT WORKFLOW AUTOMATION ROADMAP                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐           │
│  │  PRE-APPLICATION   │   │  DEVELOPMENT       │   │  BUILDING          │           │
│  │  STAGE             │──▶│  PERMIT (DP)       │──▶│  PERMIT (BP)       │           │
│  ├────────────────────┤   ├────────────────────┤   ├────────────────────┤           │
│  │ • Site Feasibility │   │ • Zoning Analysis  │   │ • Quantity Survey  │           │
│  │ • Zoning Check     │   │ • DSSP Calculator  │   │ • Fire Safety Calc │           │
│  │ • Setback Calc     │   │ • Parking Calc     │   │ • NECB Energy Calc │           │
│  │ • FAR Calculator   │   │ • Landscaping Calc │   │ • Accessibility    │           │
│  │ • Lot Coverage     │   │ • Shadow Analysis  │   │ • Plumbing Fixtures│           │
│  │                    │   │ • Traffic Impact   │   │ • HVAC Load Calc   │           │
│  └────────────────────┘   └────────────────────┘   │ • Drawing Review AI│           │
│                                                     └────────────────────┘           │
│                                                              │                       │
│                                                              ▼                       │
│                            ┌────────────────────┐   ┌────────────────────┐           │
│                            │  INSPECTION &      │   │  OCCUPANCY         │           │
│                            │  CONSTRUCTION      │◀──│  CERTIFICATE       │           │
│                            ├────────────────────┤   ├────────────────────┤           │
│                            │ • Inspection Sched │   │ • Final Compliance │           │
│                            │ • Deficiency Track │   │ • As-Built Verify  │           │
│                            │ • Progress Reports │   │ • Occupancy Check  │           │
│                            └────────────────────┘   └────────────────────┘           │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Module Status Legend

| Status | Meaning |
|--------|---------|
| ✅ COMPLETE | Module implemented and functional |
| 🔄 IN PROGRESS | Currently being developed |
| 📋 PLANNED | Documented and ready for development |
| 💡 PROPOSED | Concept stage, needs detailed planning |

---

### STAGE 1: Pre-Application Modules

These modules help users assess feasibility BEFORE formal application.

#### 1.1 Zoning Analysis Calculator ✅ PARTIAL

**Purpose**: Automated zoning compliance check for any Calgary address

**Current Status**: Basic zone lookup implemented

**Full Scope**:
```
┌─────────────────────────────────────────────────────────────────────┐
│                    ZONING ANALYSIS CALCULATOR                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INPUT:                          OUTPUT:                             │
│  ├── Address or Legal            ├── Zone District                   │
│  ├── Proposed Building Type      ├── Permitted Uses List             │
│  ├── Proposed Floor Area         ├── Height Limit                    │
│  ├── Proposed Height             ├── FAR Calculation                 │
│  └── Proposed Units              ├── Setback Requirements            │
│                                   ├── Parking Requirements            │
│                                   ├── Landscaping %                   │
│                                   ├── Density Limits                  │
│                                   └── Relaxation Options              │
│                                                                      │
│  CALCULATIONS:                                                        │
│  • FAR = Gross Floor Area ÷ Lot Area                                 │
│  • Lot Coverage = Building Footprint ÷ Lot Area × 100               │
│  • Setbacks: Front, Rear, Side (each side), Corner                   │
│  • Parking: Residential (1-2/unit), Commercial (by GFA)             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Database Requirements**:
- Zone rules table with all 68 Calgary zones
- Setback rules by zone and lot type
- Parking requirements by use type
- FAR and height limits

**API Endpoints**:
```
POST /api/v1/zoning/analyze
GET  /api/v1/zoning/zones/{zone_code}/rules
GET  /api/v1/zoning/address/{address}/compliance
POST /api/v1/zoning/setback-calculator
POST /api/v1/zoning/far-calculator
POST /api/v1/zoning/parking-calculator
```

**UI Components**:
- Address lookup with map integration
- Zoning rule display panel
- Compliance checklist with pass/fail indicators
- 3D setback visualization (future)

---

#### 1.2 Setback Calculator 📋 PLANNED

**Purpose**: Calculate required building setbacks for any lot configuration

**Calculations**:
| Setback Type | Calculation Method |
|--------------|-------------------|
| Front | Zone minimum + street type adjustment |
| Rear | Zone minimum - lot depth adjustment |
| Side (interior) | Zone minimum, often 1.2m for residential |
| Side (flanking) | Zone minimum for corner lots, often 3.0m |
| Building separation | Based on fire rating requirements |

**Special Cases**:
- Corner lots (two front setbacks)
- Through lots (two rear setbacks)
- Irregular lots (angular measurement)
- Easement adjustments

**Output**:
- Building envelope diagram (SVG)
- Maximum building footprint
- Buildable area calculation

---

#### 1.3 FAR & Lot Coverage Calculator 📋 PLANNED

**Purpose**: Calculate Floor Area Ratio and lot coverage limits

**Formulas**:
```
FAR = Total Gross Floor Area ÷ Lot Area
    where GFA includes:
    - All above-grade floor area
    - Covered parking (50% in some zones)
    - Excludes: basements, mechanical rooms, balconies

Lot Coverage = Building Footprint ÷ Lot Area × 100%
    where Footprint includes:
    - Main building outline
    - Attached garage
    - Covered patios (depends on zone)
    - Excludes: uncovered decks, eaves
```

**Zone-Specific Rules**:
| Zone Category | Max FAR | Max Coverage |
|---------------|---------|--------------|
| R-C1 (Residential) | 0.45-0.65 | 45% |
| R-C2 (Duplex) | 0.50-0.75 | 45% |
| M-C1 (Multi-Res Low) | 2.0 | 60% |
| M-C2 (Multi-Res Med) | 4.0 | 70% |
| C-COR1 (Commercial) | 5.0 | 100% |

---

### STAGE 2: Development Permit (DP) Modules

These modules support DP application preparation.

#### 2.1 DSSP Calculator ✅ COMPLETE

**Status**: Fully implemented

**Location**: `/dssp` route, `/api/v1/dssp/*` endpoints

**Features**:
- Stormwater calculations (Rational Method, Manning's)
- Sanitary sewer sizing (Harmon peaking factor)
- Water service sizing (Hazen-Williams)
- Calgary IDF curves integrated
- Drawing generator (SVG)

---

#### 2.2 Parking Requirement Calculator 📋 PLANNED

**Purpose**: Calculate parking stalls required by land use

**Calculation Rules** (Bylaw 1P2007):

| Use Type | Parking Requirement |
|----------|-------------------|
| Single Detached | 1 stall minimum |
| Duplex/Semi | 1 stall per unit |
| Townhouse | 1.5 stalls per unit |
| Multi-Res (studio/1BR) | 1 stall per unit |
| Multi-Res (2BR+) | 1.25-1.5 stalls per unit |
| Office | 2.5 stalls per 100m² |
| Retail | 4.0 stalls per 100m² |
| Restaurant | 8.0 stalls per 100m² |
| Industrial | 1.0 stall per 100m² |

**Additional Calculations**:
- Accessible parking (1 per 25 regular stalls, min 1)
- Bicycle parking (varies by use)
- Loading spaces (by GFA for commercial)
- Visitor parking (10-15% of resident parking)

**Output**:
- Total stalls required
- Stall dimension requirements (2.5m × 5.5m min)
- Aisle width requirements (6.0m for 90° parking)
- Accessible stall requirements
- Parking layout diagram (optional)

---

#### 2.3 Landscaping Requirement Calculator 📋 PLANNED

**Purpose**: Calculate required landscaping area and features

**Requirements by Zone**:
| Zone Type | Min Landscaping | Front Yard | Rear Yard |
|-----------|----------------|------------|-----------|
| Residential | 30-40% | Required | Varies |
| Commercial | 15-25% | Required | Buffer |
| Industrial | 10-15% | Required | Buffer |

**Features Required**:
- Tree planting (1 per 7.5m of frontage)
- Deciduous vs conifer mix
- Permeable surface calculation
- Storm water detention integration

**Output**:
- Required landscaping area (m²)
- Tree count required
- Plant schedule template
- Landscaping plan diagram (SVG)

---

#### 2.4 Shadow Analysis Tool 💡 PROPOSED

**Purpose**: Generate shadow studies for buildings >10m height

**Requirements**:
- Calgary requires shadow studies for tall buildings
- Analysis at March 21 and September 21 (equinoxes)
- Hours: 10:00, 12:00, 14:00, 16:00

**Technical Approach**:
- 3D building model from footprint + height
- Sun position calculation (Calgary: 51.0°N)
- Shadow projection algorithm
- Impact on adjacent properties

**Output**:
- Shadow diagrams at required times
- Impact assessment on neighbors
- Compliance statement

---

### STAGE 3: Building Permit (BP) Modules

These modules support BP application preparation.

#### 3.1 Quantity Survey Calculator ✅ COMPLETE

**Status**: Fully implemented

**Location**: `/quantity-survey` route, `/api/v1/quantity-survey/*` endpoints

**Features**:
- Parametric cost estimation (Class D)
- Bill of Quantities generation
- CSI division breakdown
- Calgary permit fee calculation
- Construction cost database (2024-2026)

---

#### 3.2 Fire Safety Calculator 📋 PLANNED (HIGH PRIORITY)

**Purpose**: Calculate fire safety requirements per NBC Part 9 (Div B, Section 9.9-9.10)

**Calculations**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FIRE SAFETY CALCULATOR                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. OCCUPANT LOAD CALCULATION (NBC Table 3.1.17.1)                  │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  Occupant Load = Floor Area ÷ Area per Person                       │
│                                                                      │
│  ┌────────────────────────────────┬─────────────────────────────┐   │
│  │ Use Type                       │ m² per Person               │   │
│  ├────────────────────────────────┼─────────────────────────────┤   │
│  │ Assembly (standing)            │ 0.4                         │   │
│  │ Assembly (seated, fixed)       │ 0.75                        │   │
│  │ Assembly (seated, loose)       │ 0.95                        │   │
│  │ Mercantile (street floor)      │ 2.8                         │   │
│  │ Mercantile (other floors)      │ 5.6                         │   │
│  │ Office                         │ 9.3                         │   │
│  │ Industrial                     │ 4.6                         │   │
│  │ Residential (sleeping)         │ 4.6                         │   │
│  │ Residential (non-sleeping)     │ 9.3                         │   │
│  └────────────────────────────────┴─────────────────────────────┘   │
│                                                                      │
│  2. EXIT WIDTH CALCULATION (NBC 3.4.3.2)                            │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  Exit Width = Occupant Load × mm per Person                         │
│                                                                      │
│  • No sprinklers: 6.1 mm/person (stairs), 8.0 mm/person (level)    │
│  • With sprinklers: 5.1 mm/person (stairs), 6.4 mm/person (level)  │
│  • Minimum exit width: 760mm (Part 9), 1100mm (Part 3)             │
│                                                                      │
│  3. NUMBER OF EXITS (NBC 9.9.2)                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  • Floor area ≤ 200m² + max 60 occupants: 1 exit permitted         │
│  • Floor area > 200m² or > 60 occupants: 2 exits required          │
│  • > 300 occupants: 3 exits required                                │
│  • > 600 occupants: 4 exits required                                │
│                                                                      │
│  4. TRAVEL DISTANCE (NBC 9.9.6)                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  Maximum Travel Distance to Exit:                                    │
│  • No sprinklers: 25m (dead-end), 40m (through)                     │
│  • With sprinklers: 32m (dead-end), 55m (through)                   │
│                                                                      │
│  5. FIRE SEPARATION REQUIREMENTS (NBC 9.10)                         │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  ┌────────────────────────────────┬─────────────────────────────┐   │
│  │ Separation Location            │ Fire Rating Required        │   │
│  ├────────────────────────────────┼─────────────────────────────┤   │
│  │ Suite-to-suite (multi-unit)    │ 1 hour                      │   │
│  │ Suite-to-corridor              │ 45 min                      │   │
│  │ Suite-to-storage               │ 45 min                      │   │
│  │ Suite-to-garage (attached)     │ 45 min                      │   │
│  │ Floor assembly (multi-storey)  │ 45 min - 1 hour            │   │
│  │ Exit stair enclosure           │ 45 min                      │   │
│  │ Service room                   │ 1 hour                      │   │
│  └────────────────────────────────┴─────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Output**:
- Occupant load calculation table
- Required exit widths
- Number of exits required
- Travel distance analysis
- Fire separation requirements
- Egress diagram (SVG)

**API Endpoints**:
```
POST /api/v1/fire-safety/occupant-load
POST /api/v1/fire-safety/exit-requirements
POST /api/v1/fire-safety/travel-distance
POST /api/v1/fire-safety/fire-separations
POST /api/v1/fire-safety/full-analysis
```

---

#### 3.3 NECB Energy Compliance Calculator 📋 PLANNED (HIGH PRIORITY)

**Purpose**: Verify compliance with National Energy Code for Buildings

**Compliance Paths**:
1. **Prescriptive Path** - Meet all prescriptive requirements
2. **Trade-off Path** - Trade between envelope components
3. **Performance Path** - Energy modeling (requires software)

**Prescriptive Requirements** (Climate Zone 7A - Calgary):

```
┌─────────────────────────────────────────────────────────────────────┐
│              NECB 2020 PRESCRIPTIVE REQUIREMENTS                     │
│                    Climate Zone 7A (Calgary)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  BUILDING ENVELOPE                                                   │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  ┌────────────────────────────┬──────────────────┬───────────────┐  │
│  │ Component                  │ Max U-value      │ Min R-value   │  │
│  │                            │ (W/m²·K)         │ (RSI)         │  │
│  ├────────────────────────────┼──────────────────┼───────────────┤  │
│  │ Roof/Ceiling               │ 0.121            │ 8.27 (R-47)   │  │
│  │ Above-Grade Wall           │ 0.210            │ 4.76 (R-27)   │  │
│  │ Below-Grade Wall           │ 0.284            │ 3.52 (R-20)   │  │
│  │ Floor over unheated space  │ 0.183            │ 5.46 (R-31)   │  │
│  │ Slab-on-Grade Edge         │ 1.020            │ 0.98 (R-5.6)  │  │
│  └────────────────────────────┴──────────────────┴───────────────┘  │
│                                                                      │
│  WINDOWS & DOORS                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  • Maximum FDWR: 40% (Fenestration + Door to Wall Ratio)            │
│  • Window U-value: max 1.60 W/m²·K                                  │
│  • Door U-value: max 2.80 W/m²·K (opaque), 1.60 (glazed)           │
│  • SHGC: varies by orientation and projection factor                │
│                                                                      │
│  AIR BARRIER                                                         │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  • Required on all buildings                                         │
│  • Continuous across all joints                                      │
│  • Max air leakage: 0.05 L/s/m² at 75 Pa (components)              │
│  • Whole building: 0.25 L/s/m² at 5 Pa (Part 9)                    │
│                                                                      │
│  HVAC SYSTEMS                                                        │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  • Heating: min AFUE 95% (furnace), COP 3.3 (heat pump)            │
│  • Cooling: min SEER 15 (split), EER 12 (package)                  │
│  • Ventilation: HRV/ERV with min 70% heat recovery                 │
│  • Duct insulation: R-6 in unconditioned space                      │
│                                                                      │
│  LIGHTING                                                            │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  • Interior LPD (W/m²): Office 8.5, Retail 12.0, Warehouse 5.0     │
│  • Daylight controls required in perimeter zones                    │
│  • Occupancy sensors in select spaces                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Calculations**:
- Overall envelope U-value
- FDWR calculation
- Trade-off compliance check
- Energy cost estimate

**Output**:
- Compliance checklist
- Component specifications required
- Trade-off analysis (if applicable)
- Energy compliance report (PDF)

---

#### 3.4 Accessibility Compliance Checker 📋 PLANNED

**Purpose**: Verify barrier-free design requirements (NBC 3.8, AODA/ADA concepts)

**Key Requirements**:

| Feature | Requirement |
|---------|-------------|
| Accessible Route | 920mm min clear width |
| Door Width | 810mm min clear opening |
| Ramp Slope | Max 1:12 (8.3%) |
| Landing Size | 1500mm × 1500mm min |
| Grab Bars | 750-900mm height |
| Accessible WC | 1500mm × 1500mm turning |
| Counter Height | 865mm max (accessible) |
| Signage | Tactile, Braille, visual contrast |

**Spaces Requiring Accessibility**:
- Building entrance (at least 1)
- Washrooms (at least 1 per floor)
- Corridors and doors on accessible route
- Elevators (if >1 storey and public)
- Parking (% of stalls)

**Output**:
- Accessibility compliance checklist
- Accessible route diagram
- Required features list
- Non-compliance flagging

---

#### 3.5 Plumbing Fixture Calculator 📋 PLANNED

**Purpose**: Calculate required plumbing fixtures per NPC 2020 and NBC

**Fixture Requirements** (per occupant load):

```
┌─────────────────────────────────────────────────────────────────────┐
│               PLUMBING FIXTURE REQUIREMENTS                          │
│                    NPC 2020 / NBC Referenced                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ASSEMBLY OCCUPANCIES (A-2)                                          │
│  ─────────────────────────────────────────────────────────────────  │
│  │ Fixture       │ Male           │ Female         │               │
│  ├───────────────┼────────────────┼────────────────┤               │
│  │ WC            │ 1:75           │ 1:40           │               │
│  │ Urinals       │ 1:50           │ -              │               │
│  │ Lavatories    │ 1:100          │ 1:100          │               │
│                                                                      │
│  MERCANTILE (E)                                                      │
│  ─────────────────────────────────────────────────────────────────  │
│  │ WC            │ 1:500          │ 1:375          │               │
│  │ Urinals       │ 1:750          │ -              │               │
│  │ Lavatories    │ 1:750          │ 1:750          │               │
│                                                                      │
│  OFFICE (D)                                                          │
│  ─────────────────────────────────────────────────────────────────  │
│  │ WC            │ 1:25           │ 1:15           │               │
│  │ Urinals       │ 1:50           │ -              │               │
│  │ Lavatories    │ 1:40           │ 1:40           │               │
│                                                                      │
│  RESIDENTIAL                                                         │
│  ─────────────────────────────────────────────────────────────────  │
│  • Dwelling unit: 1 WC, 1 lavatory, 1 tub/shower, 1 kitchen sink   │
│  • Additional WC recommended for 3+ bedroom                         │
│                                                                      │
│  DRINKING FOUNTAINS                                                  │
│  ─────────────────────────────────────────────────────────────────  │
│  • 1 per floor (generally)                                          │
│  • Accessible fountain required (hi-lo or dual)                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Output**:
- Fixture count by type
- Male/female distribution
- Accessible fixture requirements
- Fixture schedule for drawings

---

#### 3.6 HVAC Load Calculator 📋 PLANNED

**Purpose**: Calculate heating and cooling loads for Calgary climate

**Calculations**:

```
HEATING LOAD (Calgary Design Conditions)
──────────────────────────────────────────
Outdoor Design Temp: -31°C (January 2.5%)
Indoor Design Temp: 21°C
Delta T: 52°C

Heat Loss = (U-value × Area × ΔT) + Infiltration + Ventilation

COOLING LOAD (Calgary Design Conditions)
──────────────────────────────────────────
Outdoor Design Temp: 29°C (July 2.5%)
Outdoor Design WB: 15°C
Indoor Design Temp: 24°C

Cooling Load = Envelope + Solar + Internal + Ventilation + Infiltration
```

**Output**:
- Heating load (BTU/hr or kW)
- Cooling load (tons or kW)
- Equipment sizing recommendations
- Ventilation requirements (ASHRAE 62.1)

---

#### 3.7 AI Drawing Review Module 💡 PROPOSED (HIGH VALUE)

**Purpose**: Analyze uploaded drawings for code compliance issues

**Approach**: Rather than generating drawings, use AI to REVIEW drawings

**Capabilities**:
1. **Dimension Extraction** - Read dimensions from floor plans
2. **Element Detection** - Identify doors, windows, stairs, exits
3. **Code Compliance Check** - Compare to requirements
4. **Issue Flagging** - Highlight non-compliance areas

**Technical Implementation**:
```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI DRAWING REVIEW PIPELINE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  UPLOAD              PROCESS              ANALYZE           REPORT  │
│  ──────             ───────              ───────           ──────  │
│                                                                      │
│  ┌─────┐         ┌─────────────┐      ┌──────────┐     ┌────────┐  │
│  │ PDF │────────▶│ PDF to Image│─────▶│  VLM AI  │────▶│Compliance│ │
│  │ DWG │         │ (per page)  │      │ Analysis │     │ Report  │  │
│  │ DXF │         └─────────────┘      └──────────┘     └────────┘  │
│  └─────┘                │                   │               │       │
│                         │                   │               │       │
│                         ▼                   ▼               ▼       │
│              ┌───────────────────────────────────────────────────┐  │
│              │ CHECKS PERFORMED:                                  │  │
│              │ • Stair dimensions (width, rise, run)             │  │
│              │ • Door dimensions and swings                       │  │
│              │ • Window sizes (egress requirements)               │  │
│              │ • Exit locations and travel distances             │  │
│              │ • Corridor widths                                  │  │
│              │ • Room labels and areas                           │  │
│              │ • Fire separation indications                     │  │
│              └───────────────────────────────────────────────────┘  │
│                                                                      │
│  OUTPUT:                                                             │
│  • Annotated drawings with issue markers                            │
│  • Compliance checklist with pass/fail                              │
│  • Required corrections list                                         │
│  • Code references for each issue                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Human Verification Required**:
- All AI-extracted values need human confirmation
- Life-safety dimensions require explicit verification checkbox
- Disclaimer: AI assistance only, not approval

---

### STAGE 4: Construction & Inspection Modules

#### 4.1 Inspection Scheduler 💡 PROPOSED

**Purpose**: Track and schedule required inspections

**Inspection Stages**:
1. Footing/Foundation (before pour)
2. Plumbing rough-in
3. Electrical rough-in
4. HVAC rough-in
5. Framing
6. Insulation/Vapor barrier
7. Drywall (fire-rated assemblies)
8. Final inspection

**Features**:
- Calendar integration
- City inspector booking
- Checklist for each stage
- Photo documentation upload
- Deficiency tracking

---

#### 4.2 Deficiency Tracker 💡 PROPOSED

**Purpose**: Track and resolve inspection deficiencies

**Features**:
- Deficiency logging with photos
- Priority classification
- Correction tracking
- Re-inspection scheduling
- Resolution documentation

---

### Module Development Priority Matrix

| Module | Business Value | Technical Complexity | Dependencies | Priority |
|--------|---------------|---------------------|--------------|----------|
| Fire Safety Calculator | High | Medium | NBC data | P1 |
| NECB Energy Calculator | High | High | NECB data | P1 |
| Zoning Analysis (full) | High | Medium | Zone data | P1 |
| Parking Calculator | Medium | Low | Zone data | P2 |
| Accessibility Checker | Medium | Medium | NBC data | P2 |
| Plumbing Fixtures | Medium | Low | NPC data | P2 |
| HVAC Load Calculator | Medium | Medium | Climate data | P2 |
| AI Drawing Review | Very High | Very High | VLM, training | P3 |
| Shadow Analysis | Low | High | 3D engine | P3 |
| Landscaping Calculator | Low | Low | Zone data | P3 |
| Inspection Scheduler | Medium | Medium | None | P4 |
| Deficiency Tracker | Medium | Low | None | P4 |

### Suggested Implementation Roadmap

```
PHASE 1: Q1 2026
├── Fire Safety Calculator (complete)
├── NECB Energy Calculator (prescriptive)
└── Zoning Analysis (full implementation)

PHASE 2: Q2 2026
├── Parking Calculator
├── Accessibility Checker
├── Plumbing Fixture Calculator
└── HVAC Load Calculator (basic)

PHASE 3: Q3 2026
├── AI Drawing Review (pilot)
├── Landscaping Calculator
└── Shadow Analysis (basic)

PHASE 4: Q4 2026
├── AI Drawing Review (full)
├── Inspection Scheduler
└── Deficiency Tracker
```

---

### Required Standards, Codes, and Documents by Module

This section details all codes, standards, and reference documents required for each future module.

#### Zoning Analysis & Setback Calculator

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| Land Use Bylaw 1P2007 | Current (consolidated) | calgary.ca | Zone definitions, setbacks, FAR, height |
| Calgary zoning districts map | Current | data.calgary.ca | Zone boundaries shapefile |
| Permitted Use Tables | Per bylaw | calgary.ca | Use-by-zone matrix |
| Development Permit Guidelines | Current | calgary.ca | Interpretation guidance |
| Calgary Street Type Classification | Current | calgary.ca | Setback adjustments |

**Key Bylaw Sections**:
- Part 4: General Rules (setbacks, height measurement)
- Part 5: Parking and Loading
- Part 6: Landscaping
- Part 7-11: Zone-specific rules

---

#### Parking Requirement Calculator

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| Land Use Bylaw 1P2007 Part 5 | Current | calgary.ca | Parking requirements by use |
| Parking Stall Standards (Schedule 1) | Current | calgary.ca | Stall dimensions |
| Accessible Parking Guidelines | Current | calgary.ca | Accessible stall requirements |
| Bicycle Parking Bylaw 6M2021 | 2021 | calgary.ca | Bike parking requirements |
| Calgary Transit TOD Guidelines | Current | calgary.ca | Parking reductions near transit |

**Calculation Tables Required**:
- Table 5.2.1.1: Minimum motor vehicle parking stalls
- Table 5.2.1.2: Parking for specific uses
- Table 5.3.1.1: Bicycle parking requirements
- Schedule 1: Parking stall dimensions

---

#### Fire Safety Calculator

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| NBC(AE) 2023 Division B | 2023 | NRC/Alberta | Fire safety requirements |
| NBC Part 3.1 | General | NRC | Occupancy classification |
| NBC Part 3.2 | Building fire safety | NRC | Fire separations |
| NBC Part 3.3 | Safety within floor areas | NRC | Travel distance, exits |
| NBC Part 3.4 | Exits | NRC | Exit requirements |
| NBC Part 9.9 | Means of egress (Part 9) | NRC | Residential exits |
| NBC Part 9.10 | Fire protection (Part 9) | NRC | Residential fire safety |
| CAN/ULC-S101 | Standard for fire tests | ULC | Fire rating tests |
| STANDATA 99-BC-001 | Exit requirements | Alberta | Alberta interpretations |

**Key Tables Required**:
- Table 3.1.17.1: Occupant load (m² per person)
- Table 3.2.2.24-83: Fire separation ratings
- Table 3.4.3.2.A/B: Exit width per person
- Table 9.9.1.1: Number of exits (Part 9)
- Table 9.10.3.1-A: Fire separation requirements

**Formulas**:
```
Occupant Load = Floor Area (m²) ÷ Area per Person (from Table 3.1.17.1)
Exit Width = Occupant Load × mm per Person (from Table 3.4.3.2)
Number of Exits = Based on occupant load and floor area thresholds
Travel Distance = Measured along path of travel (max per 3.4.2.4)
```

---

#### NECB Energy Compliance Calculator

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| NECB 2020 | 2020 | NRC | Energy code requirements |
| NBC(AE) 2023 Section 9.36 | 2023 | NRC | Part 9 energy efficiency |
| ASHRAE 90.1-2019 | 2019 | ASHRAE | Referenced standard |
| ASHRAE Fundamentals | 2021 | ASHRAE | Climate data, calculations |
| CSA F280 | Current | CSA | Heating/cooling loads |
| NRCan Climate Data | Current | NRCan | Heating/cooling degree days |

**Key Tables Required**:
- Table 3.1.1.6-A: Climate zone definitions
- Table 3.2.1.1: Prescriptive R-values/U-values by zone
- Table 3.2.2.2: Fenestration requirements
- Table 3.2.2.3: Air barrier requirements
- Table 4.3.1.2: Equipment efficiency

**Calgary Climate Data** (Zone 7A):
```
Heating Degree Days (18°C base): 4,940
Cooling Degree Days (10°C base): 164
January Design Temp (2.5%): -31°C
July Design Temp (2.5%): 29°C
```

**Formulas**:
```
FDWR = (Fenestration Area + Door Area) ÷ Gross Wall Area × 100
Overall Wall U-value = Σ(U × A) ÷ Σ(A)
Trade-off Compliance = Proposed ≤ Reference (NECB 3.3)
```

---

#### Accessibility Compliance Checker

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| NBC(AE) 2023 Section 3.8 | 2023 | NRC | Barrier-free requirements |
| NBC Part 9.5.2 | 2023 | NRC | Residential accessibility |
| CSA B651 | Current | CSA | Accessible design standard |
| Alberta Building Code amendments | Current | Alberta | Provincial variations |
| STANDATA 07-BCV-010 | Current | Alberta | Accessibility interpretations |
| City of Calgary Access Design Standards | Current | calgary.ca | Local requirements |

**Key Requirements**:
- Accessible route: 920mm min clear width
- Door opening: 810mm min clear
- Ramp slope: 1:12 max (8.33%)
- Landings: 1500mm × 1500mm min
- Grab bars: 750-900mm height
- Accessible washroom: 1700mm × 1700mm (NBC) or 1500mm × 1500mm turning

**Spaces Requiring Barrier-Free Access**:
- At least 1 entrance per building
- At least 1 accessible route per floor
- At least 1 accessible washroom per floor (public buildings)
- Elevators if more than 1 storey (with exceptions)

---

#### Plumbing Fixture Calculator

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| NPC 2020 (National Plumbing Code) | 2020 | NRC | Plumbing requirements |
| NBC(AE) 2023 Table 3.7.2.2.A | 2023 | NRC | Fixture requirements |
| NBC(AE) 2023 Table 3.7.2.2.B | 2023 | NRC | Water closets for assembly |
| CSA B64.10 | Current | CSA | Backflow prevention |
| STANDATA 01-BCV-018 | Current | Alberta | Fixture interpretations |

**Key Tables Required**:
- NPC Table 2.4.10.3: Fixture unit values
- NBC Table 3.7.2.2.A: Required plumbing fixtures
- NBC Table 3.7.2.2.B: Additional WCs for assembly

**Formulas**:
```
Number of Fixtures = Occupant Load ÷ Persons per Fixture (from table)
Male/Female Split = 50/50 unless specific use data available
Accessible Fixtures = At least 1 per required set
```

---

#### HVAC Load Calculator

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| ASHRAE Fundamentals | 2021 | ASHRAE | Load calculation methods |
| CSA F280-12 | 2012 | CSA | Residential load calculation |
| HRAI Residential Load Calculation | Current | HRAI | Canadian methodology |
| Environment Canada Climate Data | Current | ECCC | Design temperatures |
| NECB 2020 Part 5 | 2020 | NRC | Equipment efficiency |
| NBC 9.33 | 2023 | NRC | Residential HVAC requirements |

**Calgary Design Conditions**:
```
Heating:
- Outdoor Design Temp: -31°C (January 2.5%)
- Indoor Design Temp: 21°C
- Delta T: 52°C

Cooling:
- Outdoor Design Temp: 29°C (July 2.5%)
- Outdoor Design WB: 15°C
- Indoor Design Temp: 24°C
- Indoor RH: 50%

Climate Data:
- HDD (18°C): 4,940
- CDD (18°C): 164
- Latitude: 51.0°N
```

**Formulas**:
```
Heating Load (BTU/hr):
Q_total = Q_envelope + Q_infiltration + Q_ventilation
Q_envelope = Σ(U × A × ΔT)
Q_infiltration = 0.018 × ACH × Volume × ΔT

Cooling Load (BTU/hr):
Q_total = Q_envelope + Q_solar + Q_internal + Q_ventilation + Q_infiltration
Q_solar = A_glass × SHGC × Solar Intensity × CLF
Q_internal = Q_people + Q_lights + Q_equipment
```

---

#### Landscaping Calculator

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| Land Use Bylaw 1P2007 Part 6 | Current | calgary.ca | Landscaping requirements |
| Calgary Parks Standards | Current | calgary.ca | Tree species, planting |
| Low Impact Development Guidelines | Current | calgary.ca | Stormwater integration |
| Calgary Complete Streets Policy | Current | calgary.ca | Boulevard requirements |

**Requirements by Zone**:
| Zone Type | Min Landscaping | Trees per Frontage |
|-----------|----------------|-------------------|
| Residential | 30-40% of lot | 1 per 7.5m |
| Commercial | 15-25% of lot | 1 per 7.5m |
| Industrial | 10-15% of lot | 1 per 10m |
| Multi-Res | 20-30% of lot | 1 per 6m |

---

#### Shadow Analysis Tool

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| Land Use Bylaw 1P2007 | Current | calgary.ca | When shadow study required |
| Calgary Urban Design Guidelines | Current | calgary.ca | Shadow analysis methodology |
| Sun position algorithm (NOAA) | Current | NOAA | Solar angle calculations |

**Requirements**:
- Required for buildings >10m in residential areas
- Analysis dates: March 21, September 21 (equinoxes)
- Analysis times: 10:00, 12:00, 14:00, 16:00

**Calgary Solar Data**:
```
Latitude: 51.0447°N
Longitude: 114.0719°W

March 21 (Spring Equinox):
- Solar noon altitude: ~39°
- Sunrise: 07:26, Sunset: 19:36

June 21 (Summer Solstice):
- Solar noon altitude: ~62°
- Sunrise: 05:18, Sunset: 21:49

September 21 (Fall Equinox):
- Solar noon altitude: ~39°
- Sunrise: 07:17, Sunset: 19:27

December 21 (Winter Solstice):
- Solar noon altitude: ~15°
- Sunrise: 08:30, Sunset: 16:33
```

---

#### AI Drawing Review Module

| Document | Version | Source | Purpose |
|----------|---------|--------|---------|
| All NBC sections | 2023 | NRC | Compliance checking |
| Calgary permit checklists | Current | calgary.ca | Required items |
| Drawing standards (CSA A23.1) | Current | CSA | Drawing conventions |
| CAD/PDF specifications | Various | Industry | File format handling |

**Checks to Perform**:

| Check Category | Specific Checks | Code Reference |
|----------------|-----------------|----------------|
| Stairs | Width, rise, run, headroom | NBC 9.8 |
| Doors | Width, swing, clearances | NBC 9.5, 3.8 |
| Windows | Egress dimensions, safety glazing | NBC 9.7, 9.6 |
| Exits | Number, width, travel distance | NBC 9.9, 3.4 |
| Corridors | Width, dead-ends | NBC 9.9, 3.3 |
| Rooms | Ceiling height, area | NBC 9.5 |
| Fire | Separation ratings, fire-stops | NBC 9.10, 3.2 |

---

### Data Acquisition Priority

| Priority | Module | Documents Needed | Estimated Effort |
|----------|--------|------------------|-----------------|
| P1 | Fire Safety | NBC 3.1-3.4, 9.9-9.10, Tables | 2 weeks |
| P1 | NECB Energy | NECB 2020, NBC 9.36, Climate data | 3 weeks |
| P1 | Zoning (full) | Bylaw 1P2007 complete digitization | 2 weeks |
| P2 | Parking | Bylaw Part 5, Tables | 1 week |
| P2 | Accessibility | NBC 3.8, 9.5.2, CSA B651 | 2 weeks |
| P2 | Plumbing | NPC 2020, NBC Tables | 1 week |
| P2 | HVAC | ASHRAE, CSA F280, Climate | 2 weeks |
| P3 | Landscaping | Bylaw Part 6, Parks standards | 1 week |
| P3 | Shadow | Solar algorithms, guidelines | 1 week |
| P3 | AI Review | All codes (already digitized) | N/A |

---

### Document Download/Purchase Requirements

#### Free/Public Documents
- NBC(AE) 2023: Available from NRC (pdf download)
- NECB 2020: Available from NRC (pdf download)
- NPC 2020: Available from NRC (pdf download)
- Land Use Bylaw 1P2007: calgary.ca (pdf)
- STANDATA bulletins: alberta.ca (pdf)
- Climate data: Environment Canada, NRCan

#### Paid Documents (May Require Purchase)
| Document | Approximate Cost | Source |
|----------|-----------------|--------|
| CSA B651 (Accessibility) | ~$200 | CSA Group |
| CSA F280 (HVAC Loads) | ~$150 | CSA Group |
| ASHRAE Fundamentals | ~$300 | ASHRAE |
| ASHRAE 90.1 | ~$150 | ASHRAE |

#### Alternative: Standards Referenced in Codes
Many CSA standards are referenced in NBC and can be accessed through code-referenced versions (often included in NBC commentary or available through provincial adoptions).

---

## Development Phases

### Phase 1: Foundation (MVP)

**Goal**: Working prototype for Part 9 residential in Calgary

**Duration**: 8-12 weeks

| Component | Deliverable | Priority |
|-----------|-------------|----------|
| Database | NBC Part 9 key sections digitized | P0 |
| Database | R-C1, R-C2 zones from Bylaw 1P2007 | P0 |
| Backend | Project classification engine | P0 |
| Backend | Basic rule engine framework | P0 |
| Frontend | Project intake questionnaire | P0 |
| Frontend | Requirements display dashboard | P0 |
| Frontend | PDF checklist export | P1 |

**Scope Limits**:
- Part 9 residential only
- 2-3 residential zones only
- No drawing analysis
- No AI integration
- Calgary only

### Phase 2: AI Integration

**Goal**: Add drawing analysis capabilities

**Duration**: 6-8 weeks

| Component | Deliverable | Priority |
|-----------|-------------|----------|
| AI | Qwen3-VL integration for extraction | P0 |
| Frontend | Human verification interface | P0 |
| Frontend | Drawing viewer with annotation | P0 |
| Backend | Compliance report generator | P0 |
| PDF | Report export | P1 |
| Database | Complete Part 9 coverage | P1 |

### Phase 3: Full Coverage

**Goal**: Comprehensive Calgary coverage

**Duration**: 8-10 weeks

| Component | Deliverable | Priority |
|-----------|-------------|----------|
| Database | All Calgary zones | P0 |
| Database | NECB 2020 integration | P0 |
| Backend | Part 3 building support | P1 |
| Backend | Energy compliance checker | P1 |
| Frontend | Multi-user projects | P2 |
| Frontend | Professional collaboration | P2 |

### Phase 4: Scale

**Goal**: Beyond Calgary, advanced features

**Duration**: Ongoing

| Component | Deliverable | Priority |
|-----------|-------------|----------|
| Database | Edmonton support | P1 |
| Backend | BIM/IFC file support | P1 |
| API | Third-party integrations | P2 |
| Analytics | Common issues dashboard | P2 |
| Mobile | Responsive/PWA | P2 |

---

## Critical First Steps

### Immediate Actions (Week 1-2)

1. **Set up project structure**
   - Initialize Git repository
   - Set up monorepo (frontend + backend)
   - Configure Docker environment
   - Set up CI/CD pipeline

2. **Database foundation**
   - Design and create schema
   - Set up PostgreSQL with PostGIS
   - Create migration system

3. **Acquire source documents**
   - Download NBC(AE) 2023 PDF
   - Download Calgary Bylaw 1P2007
   - Download STANDATA bulletins
   - Get Calgary permit checklists

### Week 3-4

4. **Begin code digitization**
   - Start with Part 9 Division B Section 9.8 (Stairs)
   - Extract requirements into database format
   - Build validation tests

5. **Build classification engine**
   - Part 9 vs Part 3 logic
   - Occupancy group determination
   - Permit type identification

### Week 5-6

6. **Build rule engine framework**
   - Base rule class structure
   - Rule registry
   - First 10 rules implemented
   - Compliance result format

7. **Start frontend**
   - Project intake form
   - Classification result display
   - Basic requirements view

---

## Key Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code lookup accuracy | 100% | Verified against source documents |
| Classification accuracy | >99% | User confirmation rate |
| User verification completion | >95% | Checkbox attestation rate |
| Processing time | <5 min/project | End-to-end analysis |
| First-pass approval improvement | >50% reduction in corrections | User feedback tracking |

---

## AI Limitations & Safety Guardrails

### What AI Cannot Do (Hard Blocks)

These actions are explicitly prohibited for AI in this system:

| Action | Allowed? | Alternative Approach |
|--------|----------|---------------------|
| Calculate fire ratings | NO | Lookup table from NBC |
| Determine occupancy type | NO | User selects from list |
| Invent code requirements | NO | Only cite existing rules |
| Estimate costs | NO | Formula from bylaw fee schedule |
| Interpret ambiguous cases | NO | Escalate to human expert |
| Approve compliance | NEVER | Licensed professional required |
| Modify extracted values | NO | User must verify and correct |
| Skip verification steps | NO | All life-safety values require human confirmation |

### VLM Accuracy Limitations

**Critical Warning**: Based on current VLM benchmarks (as of 2025):

| Task | Accuracy | Reliability |
|------|----------|-------------|
| Drawing type detection | 85-95% | Good |
| Title block extraction | 85-90% | Good |
| Room labels | 70-85% | Moderate |
| Clean dimension reading | 75-85% | Moderate |
| **Precise dimensions with tolerances** | **50-70%** | **UNRELIABLE** |
| Scale interpretation | 40-60% | UNRELIABLE |
| Fire rating annotations | 50-65% | UNRELIABLE |

**The Math Problem**: For a 50-sheet drawing set with 100 data points per sheet:
- At 85% accuracy: **750 potential errors**
- At 95% accuracy: **250 potential errors**

For life-safety code compliance, this is unacceptable without human verification.

### Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI hallucination of dimensions | Critical | Mandatory human verification checkbox |
| Misclassification of building | High | Explicit user confirmation required |
| Outdated code references | High | Version-controlled database with effective dates |
| User reliance without verification | High | Attestation checkboxes, disclaimers |
| Professional liability claims | Critical | System is advisory only, not approval |

### Disclaimers Required in UI

Every compliance report must include:

> **DISCLAIMER**: This report is generated by an automated system and does not constitute official code compliance approval. Final approval requires review by the City of Calgary and licensed professionals. All life-safety dimensions must be verified by a qualified designer. The system may contain errors and should not be relied upon as the sole source of code compliance information.

---

## Citation Standards & Formal Reports

### Core Principle: Everything Must Be Cited

**Every recommendation, requirement, and compliance check in the system must be traceable to an authoritative source.** This enables users to:
1. Verify the accuracy of information
2. Defend their applications against unfair decisions
3. Understand the legal basis for requirements
4. Appeal decisions with proper precedent references

### Citation Format Standards

#### Code Citations
```
Format: [Code Short Name] [Edition] [Article/Section Number]

Examples:
- NBC(AE) 2023 Section 9.8.2.1.(1)
- Land Use Bylaw 1P2007 Section 333(1)(a)
- STANDATA 24-BCB-005 Section 3.2
- NECB 2020 Article 8.4.2.2
```

#### SDAB Decision Citations
```
Format: SDAB-[Year]-[Number] ([Outcome])

Examples:
- SDAB-2024-0123 (Allowed)
- SDAB-2023-0456 (Denied)
- SDAB-2024-0789 (Allowed in Part)
```

#### Development Permit Citations
```
Format: DP[Year]-[Number] ([Status])

Examples:
- DP2024-0001 (Approved)
- DP2023-5678 (Refused - Setback deficiency)
```

### Formal Report Structure

Each operating mode generates a formal report with full citations:

#### EXPLORE Mode Report
```markdown
# Code Exploration Report
**Generated**: [Date/Time]
**Query**: [User's original question]

## Summary Answer
[Synthesized answer to the query]

## Applicable Code Sections

### Primary References
| Code | Section | Title | Relevance |
|------|---------|-------|-----------|
| NBC(AE) 2023 | 9.8.2.1 | Stair Width | Directly addresses query |
| NBC(AE) 2023 | 9.8.4.1 | Riser Dimensions | Related requirement |

### Full Text of Cited Sections
#### NBC(AE) 2023 Section 9.8.2.1 - Stair Width
> "Except as provided in Sentence (2) and Article 9.8.4.7., required exit
> stairs and public stairs serving buildings of residential occupancy
> shall have a width of not less than 900 mm."

[Additional sections...]

### Related STANDATA Interpretations
- STANDATA 23-BCB-012: Clarification on stair width measurement

### Cross-References
- See also: Section 9.8.4.7 (Spiral Stairs), Section 9.9.3.2 (Exit Width)

## Disclaimer
[Standard disclaimer text]
```

#### GUIDE Mode Report
```markdown
# Pre-Design Requirements Report
**Project**: [Project Name]
**Address**: [Address]
**Zone**: [Zone Code]
**Generated**: [Date/Time]

## Project Classification
- **Building Classification**: Part 9 Residential
  - *Citation*: NBC(AE) 2023 Section 1.3.3.2
- **Occupancy Group**: C (Residential)
  - *Citation*: NBC(AE) 2023 Table 3.1.2.1

## Zoning Requirements
| Requirement | Value | Source |
|-------------|-------|--------|
| Max Height | 10m | LUB 1P2007 s.333(2)(a) |
| Front Setback | 6.0m | LUB 1P2007 s.333(3)(a) |
| Side Setback | 1.2m | LUB 1P2007 s.333(3)(b) |

## Building Code Requirements
[Detailed requirements with citations...]

## Potential Issues & Precedents
Based on SDAB decisions and permit history for this zone:

| Issue | Risk Level | Precedent |
|-------|------------|-----------|
| Secondary Suite | Medium | SDAB-2023-0234 (Allowed with conditions) |
| Setback Relaxation | High | SDAB-2024-0156 (Denied - no hardship shown) |

## Permit Checklist
[Checklist with code references for each item...]
```

#### REVIEW Mode Report
```markdown
# Compliance Review Report
**Project**: [Project Name]
**Drawing Set**: [List of drawings reviewed]
**Review Date**: [Date/Time]

## Executive Summary
- **Total Checks**: 87
- **Pass**: 72 (83%)
- **Fail**: 8 (9%)
- **Requires Verification**: 7 (8%)

## Detailed Findings

### PASS - Stair Width
| Item | Required | Actual | Status | Citation |
|------|----------|--------|--------|----------|
| Main Stair Width | ≥860mm | 900mm | PASS | NBC(AE) 2023 s.9.8.2.1.(2) |
| Headroom | ≥1950mm | 2100mm | PASS | NBC(AE) 2023 s.9.8.2.2.(3) |

### FAIL - Guard Height
| Item | Required | Actual | Status | Citation |
|------|----------|--------|--------|----------|
| Deck Guard | ≥1070mm | 900mm | FAIL | NBC(AE) 2023 s.9.8.8.3.(1) |

**Deficiency Details**:
- Location: Rear deck (Drawing A3.2)
- Required: Guard height ≥1070mm for surfaces >1800mm above grade
- Actual: 900mm shown on drawing
- Code Reference: NBC(AE) 2023 Section 9.8.8.3.(1)
- Correction Required: Increase guard height to minimum 1070mm

**Similar Cases**:
- DP2023-4521: Refused for same deficiency, later corrected
- SDAB-2023-0891: Appeal denied for guard height variance

### REQUIRES VERIFICATION
[Items that need human verification with extraction confidence...]

## Appendix: All Code References Used
[Complete list of every code section cited in this report]

## Certification
This report was generated automatically. All findings require verification
by a qualified professional before submission to the Authority Having
Jurisdiction.
```

### Issue Checklist with Precedent Citations

The system maintains an issues checklist derived from:
1. **SDAB Decisions** - Historical appeal outcomes with citable decision numbers
2. **Refused Permits** - Common deficiency reasons with permit references
3. **STANDATA Bulletins** - Official interpretations with bulletin numbers

Each checklist item includes:
```json
{
  "issue_id": "CHK-001",
  "description": "Secondary suite parking requirements",
  "risk_level": "HIGH",
  "code_references": [
    "LUB 1P2007 s.340.1(2)(b)",
    "NBC(AE) 2023 s.9.35.2.1"
  ],
  "sdab_precedents": [
    {
      "decision": "SDAB-2024-0123",
      "outcome": "Allowed",
      "key_factor": "Tandem parking accepted"
    },
    {
      "decision": "SDAB-2023-0456",
      "outcome": "Denied",
      "key_factor": "No visitor parking provided"
    }
  ],
  "prevention_tips": [
    "Provide minimum 1 parking stall per suite",
    "Consider tandem parking if space limited",
    "Document hardship if seeking relaxation"
  ]
}
```

### Database Schema for Citations

```sql
-- Citation tracking for all system outputs
CREATE TABLE citations (
    id UUID PRIMARY KEY,
    citation_type VARCHAR(50) NOT NULL,  -- 'code', 'sdab', 'permit', 'standata'
    reference_code VARCHAR(100) NOT NULL, -- e.g., 'NBC(AE) 2023 s.9.8.2.1'
    full_reference TEXT NOT NULL,
    source_document VARCHAR(255),
    effective_date DATE,
    expiry_date DATE,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Link citations to compliance checks
CREATE TABLE check_citations (
    check_id UUID REFERENCES compliance_checks(id),
    citation_id UUID REFERENCES citations(id),
    citation_context TEXT, -- How this citation applies
    PRIMARY KEY (check_id, citation_id)
);

-- SDAB decision details for precedent lookup
CREATE TABLE sdab_decisions (
    id UUID PRIMARY KEY,
    decision_number VARCHAR(50) UNIQUE NOT NULL,
    decision_date DATE,
    property_address TEXT,
    zone VARCHAR(20),
    issue_type VARCHAR(100),
    outcome VARCHAR(50), -- 'ALLOWED', 'DENIED', 'ALLOWED_IN_PART'
    key_reasoning TEXT,
    conditions TEXT[],
    full_text TEXT,
    searchable_text TSVECTOR
);
```

### API Endpoints for Citations

```
GET /api/citations/search?query=stair+width
GET /api/citations/code/{code_id}/article/{article_number}
GET /api/sdab/decisions?zone=R-C1&issue=setback
GET /api/sdab/decision/{decision_number}
GET /api/reports/{project_id}/explore
GET /api/reports/{project_id}/guide
GET /api/reports/{project_id}/review
POST /api/reports/{project_id}/generate?format=pdf
```

---

## Building Classification Clarification

### Part 9 vs Part 3 Determination

**Part 9 applies when ALL of these are true:**

| Criterion | Limit | How Measured |
|-----------|-------|--------------|
| Building height | ≤3 storeys | Above grade, not including basement |
| Building area | ≤600 m² | **Floor plate/footprint**, not total gross area |
| Occupancy | C, D, E, F2, F3 only | Major occupancy classification |

**Important**: The 600 m² limit refers to the **building footprint** (largest floor plate), NOT total floor area across all storeys. A 3-storey building with 200 m² per floor (600 m² total) qualifies for Part 9, but a building with 650 m² footprint does not.

### Part 3 Requirements

When Part 3 applies, additional professionals are required:
- Registered Architect (mandatory)
- Structural Engineer (mandatory)
- Mechanical Engineer (for complex HVAC)
- Fire Protection Engineer (for complex fire systems)
- Electrical Engineer (for large services)

The system should detect Part 3 classification and:
1. Display different requirements
2. List required professionals
3. Note that Part 3 compliance is more complex
4. Recommend engaging design professionals before proceeding

---

## Data Maintenance & Update Monitoring

### Why This Matters

Building codes, zoning bylaws, and STANDATA bulletins are **living documents** that update regularly. A compliance system using outdated data could give incorrect guidance, leading to permit rejections or safety issues.

### Update Frequencies

| Document Type | Update Cycle | Monitoring Method |
|--------------|--------------|-------------------|
| **National Codes (NBC, NFC, NPC, NECB)** | ~5 years | Check NRC website quarterly |
| **Alberta Edition Adoption** | 1-2 years after national | Check Alberta.ca for adoption notices |
| **STANDATA Bulletins** | Ongoing (new bulletins monthly) | Subscribe to Alberta MA email alerts |
| **Calgary Land Use Bylaw** | Multiple amendments/year | Check Calgary.ca monthly |
| **Calgary Zoning Map** | Continuous (as rezonings approved) | Open Calgary API weekly |
| **Fee Schedules** | Annually (January) | Check Calgary.ca in December |
| **Referenced Standards (CSA, ULC)** | Varies by standard | Track NBC reference updates |

### Automated Update Checker

```python
# update_checker.py
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import hashlib

@dataclass
class DataSource:
    name: str
    url: str
    check_frequency_days: int
    last_checked: Optional[datetime] = None
    last_hash: Optional[str] = None
    current_version: Optional[str] = None

DATA_SOURCES = [
    DataSource(
        name="STANDATA Bulletins Index",
        url="https://open.alberta.ca/publications/standata-bulletin-building-national-building-code-2023-alberta-edition",
        check_frequency_days=7
    ),
    DataSource(
        name="Calgary Land Use Bylaw",
        url="https://www.calgary.ca/planning/land-use.html",
        check_frequency_days=30
    ),
    DataSource(
        name="Calgary Zoning Data",
        url="https://data.calgary.ca/resource/svbi-k49z.json",
        check_frequency_days=7
    ),
    DataSource(
        name="Alberta Building Codes Page",
        url="https://www.alberta.ca/building-codes-and-standards",
        check_frequency_days=30
    ),
    DataSource(
        name="NRC Codes Canada",
        url="https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada/codes-canada-publications",
        check_frequency_days=90
    ),
]

class UpdateChecker:
    def __init__(self, db_connection):
        self.db = db_connection

    def check_for_updates(self) -> list[dict]:
        """Check all data sources for updates."""
        updates_found = []

        for source in DATA_SOURCES:
            if self._should_check(source):
                try:
                    current_hash = self._get_page_hash(source.url)

                    if source.last_hash and current_hash != source.last_hash:
                        updates_found.append({
                            "source": source.name,
                            "url": source.url,
                            "detected_at": datetime.now(),
                            "action_required": "Review for new content"
                        })

                    # Update tracking
                    source.last_hash = current_hash
                    source.last_checked = datetime.now()
                    self._save_source_state(source)

                except Exception as e:
                    print(f"Error checking {source.name}: {e}")

        return updates_found

    def _should_check(self, source: DataSource) -> bool:
        if source.last_checked is None:
            return True
        return datetime.now() - source.last_checked > timedelta(days=source.check_frequency_days)

    def _get_page_hash(self, url: str) -> str:
        response = requests.get(url, timeout=30)
        return hashlib.md5(response.content).hexdigest()

    def _save_source_state(self, source: DataSource):
        # Save to database for persistence
        pass

def notify_admin(updates: list[dict]):
    """Send notification about detected updates."""
    if updates:
        # Email, Slack, or dashboard notification
        for update in updates:
            print(f"⚠️ UPDATE DETECTED: {update['source']}")
            print(f"   URL: {update['url']}")
            print(f"   Action: {update['action_required']}")
```

### Database Version Tracking

```sql
-- Track document versions and effective dates
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type VARCHAR(50) NOT NULL,  -- 'NBC', 'STANDATA', 'BYLAW', etc.
    document_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE,                     -- When superseded
    source_url TEXT,
    file_hash VARCHAR(64),                -- SHA-256 of downloaded file
    downloaded_at TIMESTAMP DEFAULT NOW(),
    is_current BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- Track when we last checked each source
CREATE TABLE update_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(100) NOT NULL,
    source_url TEXT NOT NULL,
    checked_at TIMESTAMP DEFAULT NOW(),
    page_hash VARCHAR(64),
    update_detected BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- Alert when using potentially outdated data
CREATE VIEW outdated_documents AS
SELECT
    document_type,
    document_name,
    version,
    effective_date,
    CURRENT_DATE - effective_date AS days_since_effective
FROM document_versions
WHERE is_current = TRUE
AND (
    -- NBC editions older than 5 years
    (document_type = 'NBC' AND CURRENT_DATE - effective_date > 1825)
    OR
    -- STANDATA older than 2 years may be superseded
    (document_type = 'STANDATA' AND CURRENT_DATE - effective_date > 730)
    OR
    -- Bylaw amendments older than 6 months
    (document_type = 'BYLAW' AND CURRENT_DATE - effective_date > 180)
);
```

### Subscription Alerts

**Sign up for official notifications:**

| Source | Subscription URL | What You Get |
|--------|-----------------|--------------|
| Alberta Municipal Affairs | [alberta.ca/building-standata](https://www.alberta.ca/building-standata) | Email when new STANDATA issued |
| Safety Codes Council | [safetycodes.ab.ca](https://www.safetycodes.ab.ca) | Code change notifications |
| Calgary Planning | [calgary.ca/planning](https://www.calgary.ca/planning) | Bylaw amendment notices |
| NRC Codes Canada | [nrc.canada.ca](https://nrc.canada.ca) | New code edition announcements |

### Update Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA UPDATE WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. DETECTION                                                            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                │
│  │ Automated   │     │ Email       │     │ Manual      │                │
│  │ Checker     │ OR  │ Alert       │ OR  │ Review      │                │
│  │ (weekly)    │     │ Received    │     │ (quarterly) │                │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                │
│         └──────────────────┬┴───────────────────┘                        │
│                            ▼                                             │
│  2. ASSESSMENT                                                           │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ • What changed? (new articles, amended values, deletions)   │        │
│  │ • Impact scope? (Part 9, Part 3, specific zones)           │        │
│  │ • Effective date? (immediate or future)                     │        │
│  │ • Supersedes what? (mark old version as expired)            │        │
│  └──────────────────────────────┬──────────────────────────────┘        │
│                                 ▼                                        │
│  3. EXTRACTION                                                           │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ • Download new document                                     │        │
│  │ • Run LLM extraction on changed sections                    │        │
│  │ • Compare with previous version                             │        │
│  │ • Flag all changes for human verification                   │        │
│  └──────────────────────────────┬──────────────────────────────┘        │
│                                 ▼                                        │
│  4. VERIFICATION                                                         │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ • Domain expert reviews all extracted changes               │        │
│  │ • Verify numerical values against source                    │        │
│  │ • Confirm effective dates                                   │        │
│  │ • Approve for production                                    │        │
│  └──────────────────────────────┬──────────────────────────────┘        │
│                                 ▼                                        │
│  5. DEPLOYMENT                                                           │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ • Update database with new requirements                     │        │
│  │ • Set effective_date for time-based queries                 │        │
│  │ • Mark old version as superseded                            │        │
│  │ • Log change in audit trail                                 │        │
│  │ • Notify users of significant changes                       │        │
│  └─────────────────────────────────────────────────────────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Scheduled Tasks (Cron Jobs)

```bash
# /etc/cron.d/code-expert-updates

# Check STANDATA and Calgary sources weekly (Sunday 2 AM)
0 2 * * 0 /app/scripts/check_updates.py --sources standata,calgary

# Check Alberta codes monthly (1st of month, 3 AM)
0 3 1 * * /app/scripts/check_updates.py --sources alberta

# Check NRC/national codes quarterly (1st of Jan, Apr, Jul, Oct)
0 4 1 1,4,7,10 * /app/scripts/check_updates.py --sources nrc

# Download fresh Calgary zoning data weekly (Monday 1 AM)
0 1 * * 1 /app/scripts/refresh_zoning.py

# Generate data freshness report monthly
0 6 1 * * /app/scripts/freshness_report.py --email admin@example.com
```

### User-Facing Freshness Indicators

The UI should show data currency:

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 DATA CURRENCY STATUS                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  NBC(AE) 2023        ✅ Current    Effective: May 1, 2024       │
│  Land Use Bylaw      ✅ Current    Amended: Jan 1, 2025         │
│  STANDATA Bulletins  ✅ Current    Last checked: 2 days ago     │
│  Calgary Zoning Map  ✅ Current    Last updated: 5 days ago     │
│  Fee Schedule        ✅ Current    2026 Edition                 │
│                                                                  │
│  ⚠️ Next code cycle: NBC 2025 expected adoption ~2027           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Critical: Effective Date Handling

When codes change, there's often a transition period:

```python
def get_applicable_requirement(element: str, project_date: date) -> Requirement:
    """
    Return the requirement that was in effect on the project date.

    Example: NBC(AE) 2019 was in effect until April 30, 2024.
             NBC(AE) 2023 came into effect May 1, 2024.

    A project permitted in March 2024 uses the 2019 code.
    A project permitted in June 2024 uses the 2023 code.
    """
    return db.query(Requirement).filter(
        Requirement.element == element,
        Requirement.effective_date <= project_date,
        or_(
            Requirement.expiry_date.is_(None),
            Requirement.expiry_date > project_date
        )
    ).order_by(Requirement.effective_date.desc()).first()
```

---

## Appendix A: Key Code Requirements Reference

### Fire Separations (Part 9)

| Condition | Required Rating | Code Reference |
|-----------|-----------------|----------------|
| Between dwelling units | 45 minutes | 9.10.9 |
| Between suites in care occupancy | 60 minutes | 9.10.9 |
| Furnace room (residential) | 45 minutes | 9.10.10 |
| Exit stair enclosure | 45 minutes | 9.9.4 |
| Storage garage to dwelling | 45 minutes | 9.10.9 |

### Egress Requirements

| Element | Minimum Dimension | Code Reference |
|---------|-------------------|----------------|
| Stair width (residential) | 860 mm | 9.8.4.1 |
| Door width (dwelling unit) | 810 mm | 9.5.5.1 |
| Corridor width | 1100 mm | 9.9.3.1 |
| Handrail height | 865-965 mm | 9.8.7.4 |
| Riser height | 125-200 mm | 9.8.4.5 |

### Energy Efficiency

| Building Type | Code Section | Minimum Standard |
|---------------|--------------|------------------|
| Part 9 residential | Section 9.36 | Tier 1 minimum |
| Part 3 buildings | NECB 2020 | Tier 1 minimum |
| Climate Zone 7A/7B | 9.36.2 | RSI 4.67 walls |

---

## Appendix B: Calgary Residential Zones Quick Reference

### R-C1 (Residential - Contextual One Dwelling)

| Rule | Value |
|------|-------|
| Max height | 10m |
| Max FAR | 0.45 |
| Front setback | 3.0m (contextual) |
| Side setback | 1.2m |
| Rear setback | 25% of lot depth or 7.5m |
| Parking | 1 stall minimum |

### R-C2 (Residential - Contextual One/Two Dwelling)

| Rule | Value |
|------|-------|
| Max height | 10m |
| Max FAR | 0.50 |
| Front setback | 3.0m (contextual) |
| Side setback | 1.2m |
| Rear setback | 25% of lot depth or 7.5m |
| Parking | 1 stall per unit |

---

---

## Appendix C: Calgary Zoning Data Acquisition

### Data Sources

| Source | URL | Data Type | Format |
|--------|-----|-----------|--------|
| Open Calgary Portal | https://data.calgary.ca | Parcels, Zones, Assessments | GeoJSON, Shapefile, CSV |
| Land Use Bylaw Map | https://www.calgary.ca/maps/land-use-bylaw.html | Interactive zone lookup | Web API |
| Property Assessments | https://data.calgary.ca/Government/Current-Year-Property-Assessments-Parcel-/4bsw-nn7w | Parcel details | CSV, GeoJSON |

### All Calgary Zone Categories

#### Residential Districts

| Zone Code | Name | Typical Use |
|-----------|------|-------------|
| R-C1 | Residential – Contextual One Dwelling | Single-family, established areas |
| R-C1N | Residential – Contextual One Dwelling Narrow | Narrow lot single-family |
| R-C1L | Residential – Contextual One Dwelling Large | Large lot single-family |
| R-C1s | Residential – Contextual One Dwelling Small | Small lot single-family |
| R-C2 | Residential – Contextual One / Two Dwelling | Single or duplex |
| R-CG | Residential – Contextual Grade-Oriented | Rowhouse, townhouse |
| R-G | Residential – Grade-Oriented | Medium density grade-oriented |
| R-GM | Residential – Grade-Oriented Medium Profile | Medium density, taller |
| M-C1 | Multi-Residential – Contextual Low Profile | Low-rise apartments, established |
| M-C2 | Multi-Residential – Contextual Medium Profile | Mid-rise apartments, established |
| M-CG | Multi-Residential – Contextual Grade-Oriented | Grade-oriented multi-res |
| M-G | Multi-Residential – Grade-Oriented | Townhouse, rowhouse |
| M-1 | Multi-Residential – Low Profile | Low-rise apartments |
| M-2 | Multi-Residential – Medium Profile | Mid-rise apartments |
| M-H1 | Multi-Residential – High Density Low Profile | High density, low rise |
| M-H2 | Multi-Residential – High Density Medium Profile | High density, mid rise |
| M-H3 | Multi-Residential – High Density High Profile | High density, high rise |
| M-X1 | Multi-Residential – Mixed Use Low Profile | Residential + commercial |
| M-X2 | Multi-Residential – Mixed Use Medium Profile | Residential + commercial |

#### Commercial Districts

| Zone Code | Name | Typical Use |
|-----------|------|-------------|
| C-N1 | Commercial – Neighbourhood 1 | Small neighbourhood commercial |
| C-N2 | Commercial – Neighbourhood 2 | Larger neighbourhood commercial |
| C-C1 | Commercial – Community 1 | Community-scale retail |
| C-C2 | Commercial – Community 2 | Larger community retail |
| C-COR1 | Commercial – Corridor 1 | Low intensity corridor |
| C-COR2 | Commercial – Corridor 2 | Medium intensity corridor |
| C-COR3 | Commercial – Corridor 3 | High intensity corridor |
| C-R1 | Commercial – Regional 1 | Regional shopping |
| C-R2 | Commercial – Regional 2 | Large regional retail |
| C-R3 | Commercial – Regional 3 | Major regional retail |
| C-O | Commercial – Office | Office buildings |

#### Industrial Districts

| Zone Code | Name | Typical Use |
|-----------|------|-------------|
| I-G | Industrial – General | General industrial |
| I-B | Industrial – Business | Business/light industrial |
| I-C | Industrial – Commercial | Commercial industrial |
| I-E | Industrial – Edge | Industrial edge/transition |
| I-H | Industrial – Heavy | Heavy industrial |
| I-R | Industrial – Redevelopment | Industrial redevelopment |

#### Mixed Use Districts

| Zone Code | Name | Typical Use |
|-----------|------|-------------|
| MU-1 | Mixed Use – General | General mixed use |
| MU-2 | Mixed Use – Active Frontage | Street-oriented mixed use |
| CC-X | City Centre Mixed Use | Downtown mixed use |
| CC-COR | City Centre – Corridor | Downtown corridor |
| CC-EPR | City Centre – East Precinct | East downtown |
| CC-ET | City Centre – East Town | East Victoria Park |
| CC-MH | City Centre – Medium/High Density | Downtown residential |
| CC-MHX | City Centre – Medium/High Density Mixed | Downtown mixed |
| CC-ERR | City Centre – East Residential | East residential |

#### Special Purpose Districts

| Zone Code | Name | Typical Use |
|-----------|------|-------------|
| S-CS | Special Purpose – Community Service | Schools, community facilities |
| S-CI | Special Purpose – Civic | Civic buildings |
| S-CRI | Special Purpose – City and Regional Infrastructure | Major infrastructure |
| S-R | Special Purpose – Recreation | Parks, recreation |
| S-SPR | Special Purpose – Sports | Sports facilities |
| S-FUD | Special Purpose – Future Urban Development | Future development areas |
| S-UN | Special Purpose – Urban Nature | Natural areas |
| S-URP | Special Purpose – Urban Reserve | Land banking |
| DC | Direct Control | Custom rules by Council |

### Calgary Neighbourhood Examples by Zone

| Neighbourhood | Common Zones | Character |
|---------------|--------------|-----------|
| Mount Royal | R-C1L, DC | Large lot single-family, heritage |
| Brentwood | R-C1, R-C2 | Post-war single-family |
| Kensington | M-C1, M-C2, C-N1 | Mixed residential/commercial |
| Mission | M-H2, M-H3, C-COR2 | High-density, urban |
| Inglewood | M-CG, C-N2, DC | Heritage, mixed use |
| Bridgeland | R-CG, M-C1, C-N1 | Transitioning, mixed |
| Downtown | CC-X, CC-COR, CC-MHX | High-rise, commercial |
| Beltline | M-H3, C-COR3, CC-MH | High-density residential |
| Marda Loop | R-C2, C-N2, M-CG | Neighbourhood commercial |
| Sunnyside | R-C2, M-C1, C-N1 | Mixed, near downtown |
| University District | MU-1, MU-2, S-CS | New mixed-use development |
| Mahogany | R-C1, R-C2, R-CG | New suburban |
| Cranston | R-C1, R-C2 | Suburban single-family |

### Data Import Strategy

```python
# Example: Loading Calgary parcel data from Open Calgary

import geopandas as gpd
import requests

# Option 1: Download GeoJSON directly
PARCELS_URL = "https://data.calgary.ca/resource/4bsw-nn7w.geojson"

def load_calgary_parcels():
    """Load parcel data from Open Calgary API."""
    # Note: May need pagination for full dataset
    response = requests.get(PARCELS_URL, params={"$limit": 50000})
    parcels = gpd.read_file(response.text)
    return parcels

# Option 2: Download from ArcGIS REST API
ZONING_LAYER_URL = "https://data.calgary.ca/api/geospatial/..."

def load_zoning_districts():
    """Load zoning district polygons."""
    # Implementation depends on exact API endpoint
    pass

# Import into PostgreSQL/PostGIS
def import_to_postgis(parcels_gdf, connection_string):
    """Import GeoDataFrame to PostGIS."""
    parcels_gdf.to_postgis(
        name='parcels',
        con=connection_string,
        if_exists='replace',
        index=True,
        dtype={'geometry': 'GEOMETRY'}
    )
```

### Address Lookup Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  User enters: "123 Example Street NW"                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Geocode address → Get coordinates (lat/lng)             │
│     - Use Calgary geocoding API or Google/Mapbox            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Spatial query → Find parcel containing point            │
│     SELECT * FROM parcels                                   │
│     WHERE ST_Contains(geometry, ST_Point(lng, lat))         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Get zone from parcel → Look up zone rules               │
│     SELECT z.*, zr.* FROM zones z                           │
│     JOIN zone_rules zr ON z.id = zr.zone_id                 │
│     WHERE z.zone_code = parcel.zone_code                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Return to user:                                         │
│     - Zone: R-C1                                            │
│     - Max height: 10m                                       │
│     - Max FAR: 0.45                                         │
│     - Setbacks: Front 3m, Side 1.2m, Rear 7.5m             │
│     - Parking: 1 stall minimum                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Refresh Strategy

| Data Type | Update Frequency | Method |
|-----------|------------------|--------|
| Parcel boundaries | Quarterly | Full refresh from Open Calgary |
| Zone assignments | As changed | Monitor bylaw amendments |
| Zone rules | As changed | Manual update from Bylaw 1P2007 |
| Property assessments | Annual | Full refresh after July 1 |

### Key API Endpoints

```
# Open Calgary Socrata API
Base URL: https://data.calgary.ca/resource/

# Property Assessments (includes parcel info)
GET /4bsw-nn7w.json?$where=address like '%123 EXAMPLE%'

# With SoQL query
GET /4bsw-nn7w.json?$query=SELECT * WHERE roll_number='123456789'

# GeoJSON format for mapping
GET /4bsw-nn7w.geojson?$limit=1000
```

---

## Implementation Progress Log

### Session: January 9, 2026 (Continued - Evening)

**Status: Phase 1 Foundation - NBC Code Extraction EXPANDED**

#### Completed Tasks

| Task | Status | Notes |
|------|--------|-------|
| Project structure setup | ✅ Complete | Backend (FastAPI) + Frontend (React/Vite) |
| Database schema design | ✅ Complete | SQLAlchemy models for codes, zones, projects |
| PostgreSQL + pgvector setup | ✅ Complete | Docker container running on port 5432 |
| Backend unit tests | ✅ Complete | 220+ tests passing |
| Calgary zones import | ✅ Complete | 68 zone designations imported |
| Calgary parcels import | ✅ Complete | 414,605 parcel addresses imported |
| Zone polygon data | ✅ Complete | 10,249 land use district polygons with HEIGHT/FAR |
| Property-zone mapping | ✅ Complete | 577,803 address-to-zone mappings |
| Parcel-zone linking | ✅ Complete | 390,844 parcels linked to zones |
| SDAB decisions | ✅ Complete | 1,433 appeal records downloaded |
| Development permits | ✅ Complete | 188,019 permit records downloaded |
| Virtual environment setup | ✅ Complete | .venv created with all dependencies |
| **NBC Section 9.5 extraction** | ✅ Complete | Accessibility (8 articles, 16 reqs) |
| **NBC Section 9.6 extraction** | ✅ Complete | Glass (4 articles, 16 reqs) |
| **NBC Section 9.7 extraction** | ✅ Complete | Windows/Doors/Skylights (10 articles, 31 reqs) |
| **NBC Section 9.8 extraction** | ✅ Complete | Stairs, Ramps, Handrails and Guards (30 articles, 75 reqs) |
| **NBC Section 9.9 extraction** | ✅ Complete | Means of Egress (22 articles, 47 reqs) |
| **NBC Section 9.10 extraction** | ✅ Complete | Fire Protection (22 articles, 24 reqs) |
| **NBC Section 9.11 extraction** | ✅ Complete | Sound Transmission (4 articles, 13 reqs) |
| **NBC Section 9.12 extraction** | ✅ Complete | Excavation (9 articles, 20 reqs) |
| **NBC Section 9.13 extraction** | ✅ Complete | Dampproofing/Waterproofing (15 articles, 59 reqs) |
| **NBC Section 9.14 extraction** | ✅ Complete | Drainage (19 articles, 31 reqs) |
| **NBC Section 9.15 extraction** | ✅ Complete | Footings and Foundations (20 articles, 51 reqs) |
| **NBC Section 9.16-9.18 extraction** | 🔄 In Progress | Floors-on-Ground, Columns, Crawl Spaces |
| **NBC import script** | ✅ Complete | Reusable script for all sections |
| **Extraction methodology docs** | ✅ Complete | docs/code_extraction_methodology.md |
| **SDAB issues checklist** | ✅ Complete | 20 issue types with citations, risk levels |
| **DP refusal checklist** | ✅ Complete | 12 categories with relaxation success rates |
| **Backend API testing** | ✅ Complete | All endpoints verified working |
| **Permit workflow status report** | ✅ Complete | docs/permit_workflow_status.md |
| **Drawing extraction research** | ✅ Complete | docs/drawing_extraction_libraries.md |
| **VLM-free pipeline design** | ✅ Complete | docs/vlm_free_drawing_pipeline.md |

#### Current Database State

```
calgary_codes database:
├── zones: 68 records (with HEIGHT/FAR rules for 27 zones)
├── parcels: 414,605 records (390,844 linked to zones)
├── codes: 1 record (NBC(AE) 2023)
├── articles: 145 records (Sections 9.5-9.15)
└── requirements: 324 records (verified dimensional values)

data/codes/:
├── nbc_section_9.8_raw.json + _structured.json (Stairs)
├── nbc_section_9.9_raw.json + _structured.json (Egress)
└── nbc_section_9.10_raw.json + _structured.json (Fire)

data/analysis/:
├── sdab_issues_checklist.json (64KB - 20 issue types, 1,433 decisions)
└── dp_refusal_checklist.json (30KB - 12 categories, 188,019 permits)

data/zoning/:
├── land-use-districts.json (10,249 zone polygons)
├── property-zone-mapping.json (577,803 mappings)
└── land-use-designation-codes.json (68 zones)

data/permits/:
├── sdab-decisions.json (1,433 appeal records)
└── development-permits.json (188,019 permits)

docs/:
└── code_extraction_methodology.md (extraction process documentation)
```

#### NBC Section 9.8 Extraction Summary

**Extracted & Verified Values:**
| Element | Value | Source Article |
|---------|-------|----------------|
| Stair width (residential exit) | 900mm min | 9.8.2.1.(1) |
| Stair width (dwelling unit) | 860mm min | 9.8.2.1.(2) |
| Headroom (general) | 2050mm min | 9.8.2.2.(2) |
| Headroom (dwelling) | 1950mm min | 9.8.2.2.(3) |
| Riser (private) | 125-200mm | Table 9.8.4.1 |
| Riser (public) | 125-180mm | Table 9.8.4.1 |
| Run (private) | 255-355mm | Table 9.8.4.2 |
| Run (public) | 280mm min | Table 9.8.4.2 |
| Handrail height | 865-1070mm | 9.8.7.4.(2) |
| Guard height (general) | 1070mm min | 9.8.8.3.(1) |
| Guard height (dwelling) | 900mm min | 9.8.8.3.(2) |

**Research Finding:** No existing machine-readable NBC data exists. We are creating the first structured database of NBC(AE) 2023.

#### SDAB & Development Permit Analytics (for Issue Checklist)

**Appeal Insights** (from 1,433 SDAB decisions):
- Most appealed: Single Residential (679), Commercial (371)
- Common uses: Secondary Suites (93), Cannabis (112), Accessory Buildings (56)
- Outcomes: 29% ALLOWED, 21% ALLOWED IN PART, 29% DENIED

**Permit Insights** (from 188,019 DPs):
- 4,292 Refused - These contain deficiency reasons
- Top categories: Relaxation requests (15,400), Secondary suites (14,062)
- Many setback/height relaxations indicate common code conflicts

**Strategy for Issue Detection:**
1. Analyze refused permits to identify common deficiency patterns
2. Cross-reference SDAB decisions with property types to build risk profiles
3. Create checklist items based on most commonly appealed issues
4. Flag high-risk permit types (secondary suites, relaxations) for extra review

#### NBC Section 9.9 Extraction Summary (Means of Egress)

**Key Requirements Extracted:**
| Element | Value | Source Article |
|---------|-------|----------------|
| Exit width (min) | 900mm | 9.9.3.2 |
| Corridor width (min) | 1100mm | 9.9.3.3 |
| Door width (min) | 810mm | 9.9.6.2 |
| Door height (min) | 2030mm | 9.9.6.3 |
| Travel distance (max, sprinklered) | 45m | 9.9.8.2 |
| Travel distance (max, unsprinklered) | 30m | 9.9.8.2 |
| Dead-end corridor (max) | 6m | 9.9.8.5 |

#### NBC Section 9.10 Extraction Summary (Fire Protection)

**Key Requirements Extracted:**
| Element | Value | Source Article |
|---------|-------|----------------|
| Floor fire resistance (min) | 45 min | 9.10.8.1 |
| Firewall rating (min) | 2 h | 9.10.11.1 |
| Spatial separation (min) | 1.2m | 9.10.15.3 |
| Interior flame spread (max) | FSR 150 | 9.10.17.1 |
| Exit flame spread (max) | FSR 25 | 9.10.17.4 |
| Fire block spacing (max) | 20m | 9.10.16.4 |

#### SDAB & DP Issue Checklists Summary

**SDAB Checklist** (data/analysis/sdab_issues_checklist.json):
- 1,433 decisions analyzed → 20 issue types categorized
- Risk levels: HIGH (2), MEDIUM (7), MODERATE (7), LOW (4)
- Top success rates: Mixed Use (87.5%), Semi-Detached (78.6%)
- Lowest success rates: Liquor Store (38.5%), Retail (37.5%)

**DP Refusal Checklist** (data/analysis/dp_refusal_checklist.json):
- 188,019 permits analyzed → 4,293 refused (2.28% rate)
- 12 refusal categories with sample citations
- Key relaxation success rates: Setback (92%), Height (85%), Coverage (84%)
- Most affected zones: R-1, DC, R-2, R-C1, R-C2

---

### Session: January 9, 2026 (Evening - Late)

**Status: Phase 2 - Full Stack Application Complete**

#### Major Accomplishments

| Component | Status | Description |
|-----------|--------|-------------|
| **Authentication System** | ✅ Complete | Full user auth with login, register, password reset, email verification |
| **Role-Based Access Control** | ✅ Complete | USER, REVIEWER, ADMIN roles with hierarchical permissions |
| **Admin Dashboard** | ✅ Complete | Stats, user management, role changes, activate/deactivate |
| **Permit Application Tracker** | ✅ Complete | Full CRUD, document uploads, status workflow |
| **Guide Mode** | ✅ Complete | Project analysis, Part 9/3 classification, fee estimation |
| **Review Mode** | ✅ Complete | Drawing upload, AI analysis, compliance checking |
| **Explore Mode** | ✅ Complete | Code search, browse by category, natural language queries |
| **NBC Part 9 Extraction** | ✅ Complete | Sections 9.5-9.36 extracted to structured JSON (~500 articles) |

#### New Features Implemented

**1. Authentication & User Management**
- `/api/v1/auth/*` - Login, register, logout, refresh, password reset, email verification
- `/api/v1/admin/*` - User stats, list users, CRUD operations, role management
- JWT-based authentication with HTTP-only cookies
- Password hashing with bcrypt
- Session management with refresh tokens

**2. Admin Dashboard (`/admin`)**
- Total users, active users, verified users, new signups
- Users by role breakdown (Free Users, Reviewers, Admins)
- Quick actions: Manage Users, View Permits

**3. User Management (`/admin/users`)**
- Searchable/filterable user list
- Role change (User → Reviewer → Admin)
- Activate/Deactivate accounts
- Verify unverified users
- Delete users

**4. Role-Based Navigation**
- Sidebar shows different sections based on user role
- Admin section: Dashboard, User Management
- Reviewer section: Review Queue, All Permits
- Public/User sections: Explore, Guide, Review, My Permits

**5. Permit Application System**
- 6 permit types: BP, DP, TP_ELECTRICAL, TP_PLUMBING, TP_GAS, TP_HVAC
- Multi-step application form with document uploads
- Status workflow: draft → submitted → under_review → approved/rejected/corrections_required
- Reviewer notes and status history

#### Bug Fixes

| Bug | Fix | File |
|-----|-----|------|
| Guide "Continue to Review" button not working | Added onClick handler with navigate() | GuidePage.tsx |
| Permit form validation errors | Updated field names to match backend schema | PermitApplicationPage.tsx, types/index.ts |
| Browse by Code "query too short" error | Changed min_length to 1, added browse mode | codes.py, explore.py |

#### NBC Part 9 Extraction Status

**Sections Extracted (to JSON):**

| Section Range | Topic | Articles | Status |
|--------------|-------|----------|--------|
| 9.5 | Accessibility | 8 | ✅ Structured JSON |
| 9.6 | Glass | 4 | ✅ Structured JSON |
| 9.7 | Windows, Doors, Skylights | 10 | ✅ Structured JSON |
| 9.8 | Stairs, Ramps, Handrails, Guards | 30 | ✅ Structured JSON |
| 9.9 | Means of Egress | 22 | ✅ Structured JSON |
| 9.10 | Fire Protection | 22 | ✅ Structured JSON |
| 9.11 | Sound Transmission | 4 | ✅ Structured JSON |
| 9.12 | Excavation | 9 | ✅ Structured JSON |
| 9.13 | Dampproofing & Waterproofing | 15 | ✅ Structured JSON |
| 9.14 | Drainage | 19 | ✅ Structured JSON |
| 9.15 | Footings and Foundations | 20 | ✅ Structured JSON |
| 9.16 | Floors on Ground | 14 | ✅ Structured JSON |
| 9.17 | Columns | 14 | ✅ Structured JSON |
| 9.18 | Crawl Spaces | 11 | ✅ Structured JSON |
| 9.19 | Supports for Braced Wall Panels | 5 | ✅ Structured JSON |
| 9.20 | Wall Framing | 70 | ✅ Structured JSON |
| 9.21 | Floor Framing | 31 | ✅ Structured JSON |
| 9.22 | Ceiling & Roof Framing (Wood) | 21 | ✅ Structured JSON |
| 9.23 | Roof Trusses | 21 | ✅ Structured JSON |
| 9.24 | Sheathing | 15 | ✅ Structured JSON |
| 9.25 | Interior Wall & Ceiling Finishes | 14 | ✅ Structured JSON |
| 9.26 | Cladding | 12 | ✅ Structured JSON |
| 9.27 | Roofing | 12 | ✅ Structured JSON |
| 9.28 | Masonry Chimneys & Fireplaces | 10 | ✅ Structured JSON |
| 9.29 | Reserved | 0 | N/A |
| 9.30 | Reserved | 0 | N/A |
| 9.31 | Plumbing | 12 | ✅ Structured JSON |
| 9.32 | Heating/HVAC | 13 | ✅ Structured JSON |
| 9.33 | Ventilation | 20 | ✅ Structured JSON |
| 9.34 | Electrical | 10 | ✅ Structured JSON |
| 9.35 | Garages & Carports | 16 | ✅ Structured JSON |
| 9.36 | Energy Efficiency | 21 | ✅ Structured JSON |
| **TOTAL** | | **~500** | **32 sections** |

#### PDF Extraction Status

| Document | Size | Extraction Status | Notes |
|----------|------|-------------------|-------|
| **NBC-AE-2023.pdf** | 23.8 MB | ⚠️ Part 9 only | ~500 articles to JSON, 100 in DB |
| **NECB-2020.pdf** | 4.4 MB | ❌ Not extracted | Energy code |
| **NFC-AE-2023.pdf** | 6.3 MB | ❌ Not extracted | Fire code |
| **NPC-2020.pdf** | 5.0 MB | ❌ Not extracted | Plumbing code |
| **Land Use Bylaw** | 12 MB | ❌ Not extracted | Calgary zoning |
| **Standata (30 PDFs)** | ~7 MB | ❌ Not extracted | Interpretation bulletins |
| **Permit guides** | ~40 MB | ❌ Not extracted | Fee schedules, design guides |

**Key Gap:** ~500 NBC articles extracted to JSON but only 100 loaded into database. Need to run import script to load all structured JSON files.

#### Test Credentials

Created test accounts for development (see `TEST_CREDENTIALS.md`):

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@codecheck.calgary | Admin123! |
| Reviewer | reviewer@codecheck.calgary | Reviewer123! |
| Free User | user@codecheck.calgary | User123! |

Seed script: `python -m scripts.seed_users`

#### Current Database State

```
SQLite (building_codes.db):
├── codes: 1 record (NBC(AE) 2023)
├── articles: 100 records (Section 9.10 Fire Protection only)
├── zones: 0 records (need import)
├── parcels: 0 records (need import)
├── users: [via auth system]
└── permit_applications: [via permit system]

PostgreSQL (calgary_codes_db - port 5432):
├── users table with role column
├── sessions for auth
└── permit_applications with documents

Structured JSON (data/codes/):
├── 32 sections extracted (9.5-9.36)
├── ~500 articles total
└── Ready for database import
```

#### Next Steps (Priority Order)

1. **Load all NBC JSON to database** - Import ~500 articles from structured JSON files
2. **Extract remaining codes** - NECB 2020, NFC 2023, NPC 2020, Land Use Bylaw
3. **Extract Standata bulletins** - 30 interpretation documents
4. **Integrate zone/parcel data** - Load Calgary zoning data into PostgreSQL
5. **Add relaxation/variance detection** - Flag when proposed buildings need relaxations
6. **Integrate issue checklists into Guide mode** - Pre-warn users of common pitfalls
7. **Email notifications** - Password reset, email verification delivery
8. **Payment/subscription integration** - Stripe for premium tiers

#### Technical Notes

- PostgreSQL running via Docker (`calgary_codes_db` container)
- Use alternative port if 5432 is occupied (do not stop system services)
- GIN index on articles.search_vector uses `gin_trgm_ops` operator class
- PostGIS not available in pgvector image (using text WKT for geometry)
- Virtual environment at: `app/backend/.venv`

#### Commands to Resume

```bash
# Start database (if Docker Desktop is running)
cd /Users/mohmmadhanafy/Building-code-consultant/app/backend
docker-compose up -d

# Activate virtual environment
source .venv/bin/activate

# Run tests
python -m pytest tests/ -v

# Import more NBC sections
cd ../scripts
python import_nbc_codes.py --section 9.9

# Start backend API
cd ../backend
uvicorn app.main:app --reload --port 8000

# Start frontend
cd ../frontend
npm run dev
```

#### Extraction Scripts

```bash
# Extract new NBC section (adjust page numbers)
# 1. Use pdfplumber to extract raw text
# 2. Review and create structured JSON
# 3. Import to database:
python import_nbc_codes.py --section X.X --verify  # Verify first
python import_nbc_codes.py --section X.X           # Then import
```

---

### Session: January 10, 2026

**Status: Phase 3 - Full Code Extraction & Database Loading Complete + DSSP Module Design**

#### Major Accomplishments

| Task | Status | Details |
|------|--------|---------|
| **NECB-2020 Extraction** | ✅ Complete | 353 articles (Energy Code) |
| **NFC-AE-2023 Extraction** | ✅ Complete | 1,878 articles (Fire Code) |
| **NPC-2020 Extraction** | ✅ Complete | 340 articles (Plumbing Code) |
| **Land Use Bylaw Extraction** | ✅ Complete | 37 districts, 1,053 pages |
| **STANDATA Extraction** | ✅ Complete | 41 bulletins (20 BCI, 7 BCB, 4 FCB, 10 PCB) |
| **Permit Guides Extraction** | ✅ Complete | 6 guides + 4 standards (10 docs) |
| **Database Loading** | ✅ Complete | All data loaded to PostgreSQL |
| **DSSP Module Design** | ✅ Complete | Comprehensive module added to plan |

#### Extraction Scripts Created

| Script | Location | Purpose |
|--------|----------|---------|
| `extract_all_codes.py` | `/app/scripts/` | Extract NECB, NFC, NPC, Land Use Bylaw |
| `extract_standata_json.py` | `/app/scripts/` | Extract 41 STANDATA bulletins to JSON |
| `extract_permits_standards.py` | `/app/scripts/` | Extract permit guides and standards |
| `load_all_to_database.py` | `/app/scripts/` | Load all JSON to PostgreSQL database |

#### Final Database State

```
PostgreSQL (calgary_codes_db - port 5432):

CODES (6 total):
├── NBC(AE) 2023      → 505 articles
├── NECB 2020         → 353 articles
├── NFC(AE) 2023      → 1,878 articles
├── NPC 2020          → 340 articles
├── LUB 1P2007        → 0 articles (zones loaded separately)
└── GUIDES 2024       → 10 articles (reference docs)

TOTAL: 3,086 articles loaded

REQUIREMENTS: 896 checkable requirements (from NBC Part 9)

STANDATA BULLETINS (41 total):
├── BCI: 20 bulletins (Building Code Interpretations)
├── BCB: 7 bulletins (Building Code Bulletins)
├── FCB: 4 bulletins (Fire Code Bulletins)
└── PCB: 10 bulletins (Plumbing Code Bulletins)

ZONES (27 total):
├── Residential: 5 zones
├── Multi-Residential: 4 zones
├── Commercial: 7 zones
├── Industrial: 2 zones
└── Special Purpose: 9 zones
```

#### JSON Files Created

```
data/codes/
├── necb_2020_structured.json          (570 KB - Energy Code)
├── nfc_ae_2023_structured.json        (1.1 MB - Fire Code)
├── npc_2020_structured.json           (470 KB - Plumbing Code)
├── land_use_bylaw_structured.json     (1.3 MB - Zoning)
├── standata_bulletins.json            (465 KB - 41 bulletins)
├── permits_standards_extracted.json   (398 KB - Guides)
└── fee_schedule_extracted.json        (11 KB - Permit fees)
```

#### DSSP Module Added to Plan

Comprehensive Development Site Servicing Plan module designed with:

**Inputs Defined:**
- Site information (address, area, zoning)
- Proposed development (footprint, units, occupants)
- Existing infrastructure (storm/sanitary/water connections)
- Site conditions (grades, soil, groundwater)
- Stormwater options (strategy, outlet, storage, quality)

**Calculation Engine:**
- Stormwater: Rational Method, Calgary IDF curves, retention sizing, ICD sizing
- Sanitary: Population flows, Harmon peaking factor, pipe sizing
- Water: Domestic demand, fire flow, service sizing
- Grading: Minimum slopes, lot drainage, building grades

**Output Deliverables:**
- Sheet 1: Site Servicing Plan
- Sheet 2: Grading Plan
- Sheet 3: Stormwater Management Plan
- Sheet 4: Details
- Sheet 5: Floor Plan (architect upload)
- Supporting reports and calculations

**Database Schema:** 6 new tables for DSSP data
**API Endpoints:** 23 endpoints for DSSP operations
**Implementation Phases:** D1-D4 (14 weeks total)

#### PDF Extraction Status (Updated)

| Document | Size | Extraction Status | Output |
|----------|------|-------------------|--------|
| **NBC-AE-2023.pdf** | 23.8 MB | ✅ Part 9 Complete | 505 articles in DB |
| **NECB-2020.pdf** | 4.4 MB | ✅ Complete | 353 articles in DB |
| **NFC-AE-2023.pdf** | 6.3 MB | ✅ Complete | 1,878 articles in DB |
| **NPC-2020.pdf** | 5.0 MB | ✅ Complete | 340 articles in DB |
| **Land Use Bylaw** | 12 MB | ✅ Complete | 37 districts, 27 zones in DB |
| **STANDATA (41 PDFs)** | ~4 MB | ✅ Complete | 41 bulletins in DB |
| **Permit Guides (6 PDFs)** | ~40 MB | ✅ Complete | JSON + fee schedule |
| **Standards (4 PDFs)** | ~4 MB | ✅ Complete | JSON extracted |

#### Commands Used

```bash
# Extract all codes
cd /Users/mohmmadhanafy/Building-code-consultant/app/backend
source .venv/bin/activate
python ../scripts/extract_all_codes.py --all

# Extract STANDATA bulletins
python ../scripts/extract_standata_json.py

# Extract permit guides and standards
python ../scripts/extract_permits_standards.py

# Load everything to database
python ../scripts/load_all_to_database.py --force
```

#### Next Steps

1. **Implement DSSP calculation engine** - ✅ Complete (see below)
2. **Add embeddings for semantic search** - Generate vectors for all articles
3. **Integrate DSSP with Guide mode** - Link servicing design to permit workflow
4. **Build drawing generation system** - ✅ Complete (SVG generator)
5. **Add real-time compliance checking** - Validate inputs against code requirements

---

### Session: January 10, 2026 (Continued - Late)

**Status: Phase 3 - DSSP & Quantity Survey Modules Complete with Full Test Coverage**

#### Major Accomplishments

| Task | Status | Details |
|------|--------|---------|
| **DSSP Calculation Engine** | ✅ Complete | Stormwater, Sanitary, Water Service calculations |
| **Calgary IDF Curves** | ✅ Complete | 2, 5, 10, 25, 50, 100-year return periods |
| **Rational Method** | ✅ Complete | Q = C × i × A with Calgary coefficients |
| **Manning's Equation** | ✅ Complete | Pipe sizing for storm/sanitary |
| **Harmon Peaking Factor** | ✅ Complete | PF = 1 + 14/(4 + √P) |
| **Hazen-Williams** | ✅ Complete | Water service head loss calculations |
| **DSSP API Endpoints** | ✅ Complete | 7 endpoints for all calculations |
| **DSSP Frontend UI** | ✅ Complete | Professional engineering dashboard |
| **DSSP Drawing Generator** | ✅ Complete | SVG output for 5 DSSP sheets |
| **Quantity Survey Module** | ✅ Complete | Cost estimation & BOQ generation |
| **Calgary Cost Data** | ✅ Complete | 2024-2026 construction costs |
| **Parametric Estimator** | ✅ Complete | Class D estimates with CSI breakdown |
| **BOQ Generator** | ✅ Complete | Detailed line items by CSI division |
| **Permit Fee Calculator** | ✅ Complete | $10.14/$1,000 Calgary rate |
| **QS API Endpoints** | ✅ Complete | 9 endpoints for estimates and BOQ |
| **QS Frontend UI** | ✅ Complete | Industrial blueprint aesthetic |
| **Unit Tests - DSSP** | ✅ Complete | 59 tests (IDF, Storm, Sanitary, Water) |
| **Unit Tests - QS** | ✅ Complete | 53 tests (Cost, Estimator, BOQ) |

#### Files Created

**DSSP Module:**
```
app/backend/app/services/dssp/
├── __init__.py          - Module exports
├── idf_curves.py        - Calgary IDF curve service (286 lines)
├── stormwater.py        - Rational Method & Manning's (536 lines)
├── sanitary.py          - Harmon peaking & sanitary design (578 lines)
├── water.py             - Hazen-Williams & water sizing (652 lines)
└── drawing_generator.py - SVG generator for 5 sheets (800+ lines)

app/backend/app/api/dssp.py - API endpoints (340 lines)
app/frontend/src/pages/DSSPCalculatorPage.tsx - React UI (1,200+ lines)
data/codes/calgary_idf_curves.json - IDF coefficients & runoff C values
```

**Quantity Survey Module:**
```
app/backend/app/services/quantity_survey/
├── __init__.py          - Module exports
├── cost_data.py         - Calgary cost data service (191 lines)
├── estimator.py         - Parametric estimator (369 lines)
└── boq_generator.py     - BOQ generator (765 lines)

app/backend/app/api/quantity_survey.py - API endpoints (280 lines)
app/frontend/src/pages/QuantitySurveyPage.tsx - React UI (950+ lines)
data/codes/calgary_construction_costs.json - Construction costs by type/quality
```

**Unit Tests:**
```
app/backend/tests/
├── test_dssp_calculations.py   - 59 tests (900+ lines)
└── test_quantity_survey.py     - 53 tests (680+ lines)
```

#### DSSP Calculation Formulas Implemented

| Calculation | Formula | Calgary Values |
|-------------|---------|----------------|
| **IDF Intensity** | i = a / (t + b)^c | a=820-1680, b=7.0-7.8, c=0.81-0.84 |
| **Rational Method** | Q = C × i × A / 360 | C per land use, i from IDF, A in hectares |
| **Time of Concentration** | Tc = 3.26 × (1.1-C) × L^0.5 / S^(1/3) | Airport method (Calgary standard) |
| **Manning's Equation** | Q = (1/n) × A × R^(2/3) × S^(1/2) | n=0.011-0.024 by material |
| **Harmon Peaking** | PF = 1 + 14 / (4 + √P) | P in thousands, limits 1.5-4.0 |
| **Hazen-Williams** | h = 10.67 × Q^1.852 / (C^1.852 × D^4.87) × L | C=120-150 by material |

#### Calgary Design Standards Implemented

**Stormwater:**
- Minimum storm main: 300mm
- Maximum velocity: 4.5 m/s
- Minimum velocity: 0.6 m/s
- Design flow ratio: 80% full
- Minimum cover: 2.0m (frost)

**Sanitary:**
- Minimum sanitary main: 200mm
- Maximum velocity: 3.0 m/s
- Self-cleansing velocity: 0.75 m/s
- Design flow ratio: 75% full
- Infiltration: 0.28 L/s/ha

**Water:**
- Minimum residential main: 150mm
- Minimum commercial main: 200mm
- Minimum pressure: 275 kPa (40 psi)
- Fire flow pressure: 140 kPa (20 psi)
- Hydrant spacing: 150m residential, 100m commercial

#### Quantity Survey Features

**Parametric Estimation:**
- 8 project types (residential, commercial, industrial, institutional)
- 5 quality levels (economy to luxury)
- Height factor for multi-storey (1.0 to 1.35+)
- Location factor (Calgary = 1.0)
- Inflation adjustment (2024-2026)
- CSI division breakdown (14 divisions)
- Soft costs (contingency, design, permits, other)

**Bill of Quantities:**
- 9 CSI divisions generated
- Quality multiplier (0.8 to 2.0)
- Basement/garage add-ons
- Line items with quantities, units, rates
- Section totals and grand total
- 10% default contingency

**Permit Fee Calculator:**
- Building permit: $10.14/$1,000
- Electrical permit: $6.05/$1,000
- Plumbing permit: $6.05/$1,000
- Gas permit: $5.03/$1,000
- Minimum fees applied

#### Test Results

```
======================= 112 passed, 31 warnings in 0.13s =======================

DSSP Tests (59):
├── TestIDFCurveService: 12 tests
├── TestStormwaterCalculator: 13 tests
├── TestSanitaryCalculator: 14 tests
├── TestWaterCalculator: 17 tests
└── TestIntegration: 3 tests

Quantity Survey Tests (53):
├── TestCostDataService: 18 tests
├── TestEstimatorService: 14 tests
├── TestBOQGeneratorService: 14 tests
├── TestCSIDivisions: 3 tests
└── TestIntegration: 5 tests
```

#### API Endpoints Added

**DSSP (`/api/v1/dssp/`):**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/idf/intensity` | POST | Calculate rainfall intensity |
| `/idf/table` | GET | Get IDF table |
| `/stormwater/rational-method` | POST | Calculate peak flow |
| `/stormwater/design-pipe` | POST | Size storm pipe |
| `/sanitary/design-flow` | POST | Calculate sanitary flow |
| `/sanitary/design-pipe` | POST | Size sanitary pipe |
| `/water/design-flow` | POST | Calculate water demand |
| `/water/design-service` | POST | Size water service |

**Quantity Survey (`/api/v1/quantity-survey/`):**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/project-types` | GET | List available project types |
| `/quality-levels` | GET | List quality levels |
| `/csi-breakdown/{type}` | GET | Get CSI division breakdown |
| `/cost-per-sf` | POST | Get cost per SF |
| `/parametric-estimate` | POST | Full parametric estimate |
| `/permit-fee` | POST | Calculate single permit fee |
| `/all-permit-fees` | POST | Calculate all permit fees |
| `/residential-boq` | POST | Generate residential BOQ |
| `/quick-estimate` | POST | Quick cost range estimate |

#### Frontend Routes Added

| Route | Component | Purpose |
|-------|-----------|---------|
| `/dssp` | DSSPCalculatorPage | DSSP calculation dashboard |
| `/quantity-survey` | QuantitySurveyPage | Cost estimation & BOQ |

#### DSSP Drawing Generator Output

The drawing generator creates SVG drawings for:
1. **Sheet 1: Drainage Area Plan** - Catchment boundaries, flow directions, areas
2. **Sheet 2: Storm Sewer Design** - Pipe profiles, manholes, grades
3. **Sheet 3: Sanitary Sewer Design** - Pipe profiles, connections
4. **Sheet 4: Water Service Design** - Service connections, hydrants
5. **Sheet 5: Summary Sheet** - Calculation summary, standards compliance

#### Next Steps

1. ✅ ~~Implement DSSP calculation engine~~ - Complete
2. ✅ ~~Build drawing generation system~~ - Complete (SVG)
3. ✅ ~~Add unit tests~~ - Complete (112 tests)
4. **Add embeddings for semantic search** - Generate vectors for all articles
5. **Integrate DSSP with permit workflow** - Link to Guide/Review modes
6. **Implement Fire Safety Calculator** - Priority P1 future module
7. **Implement NECB Energy Calculator** - Priority P1 future module
8. **Add PDF export for drawings** - react-pdf or similar
9. **Add DXF export option** - CAD compatibility

#### Commands to Run Tests

```bash
cd /Users/mohmmadhanafy/Building-code-consultant/app/backend
source venv/bin/activate

# Run all DSSP and QS tests
python -m pytest tests/test_dssp_calculations.py tests/test_quantity_survey.py -v

# Run with coverage
python -m pytest tests/test_dssp_calculations.py tests/test_quantity_survey.py --cov=app/services

# Run specific test class
python -m pytest tests/test_dssp_calculations.py::TestStormwaterCalculator -v
```

---

### Session: January 10, 2026 (Continued - Afternoon)

**Status: Phase 3 - DSSP Calculator UX Fix Complete**

#### Issue Fixed

**Problem:** DSSP Calculator preset scenarios and form values were not persisting when switching between the Stormwater, Sanitary, and Water Service tabs. Each tab had independent local state that was lost on tab switch.

**Root Cause:** Each tab component (StormwaterTab, SanitaryTab, WaterTab) was using its own `useState` hooks for form values and calculation results. When users switched tabs, the components unmounted and remounted with fresh state.

#### Solution Implemented

| Task | Status | Details |
|------|--------|---------|
| **State Architecture Refactor** | ✅ Complete | Lifted shared state to parent DSSPCalculatorPage |
| **Unified Preset Handler** | ✅ Complete | Single handler loads all three tab presets |
| **Props-Based State Management** | ✅ Complete | Tabs receive state and handlers via props |
| **TypeScript Compilation** | ✅ Verified | No errors |

#### Code Changes

**File Modified:** `app/frontend/src/pages/DSSPCalculatorPage.tsx`

**1. Added State Interfaces:**
```typescript
interface StormwaterState {
  pipeId: string;
  catchments: CatchmentInput[];
  slopePct: string;
  returnPeriod: number;
  material: string;
  minDiameter: number;
  result: PipeDesignResult | null;
}

interface SanitaryState {
  pipeId: string;
  loads: SanitaryLoadInput[];
  slopePct: string;
  material: string;
  minDiameter: number;
  result: SanitaryPipeResult | null;
}

interface WaterState {
  serviceId: string;
  loads: WaterLoadInput[];
  lengthM: number;
  availablePressure: number;
  elevationChange: number;
  material: string;
  result: WaterServiceResult | null;
}
```

**2. Moved State to Parent:**
- `projectName` - Shared across all tabs
- `selectedPreset` - Unified preset selection
- `stormwaterState`, `sanitaryState`, `waterState` - Tab-specific data

**3. Created Unified Preset Handler:**
```typescript
const handlePresetSelect = useCallback(async (key: string) => {
  setSelectedPreset(key);
  // Load stormwater preset
  const stormScenario = await presetsApi.getStormwaterScenario(key);
  // Load sanitary preset
  const sanScenario = await presetsApi.getSanitaryScenario(key);
  // Load water preset
  const waterScenario = await presetsApi.getWaterScenario(key);
  // Update all three states
}, []);
```

**4. Refactored Tab Components:**
- Each tab now receives props instead of managing own state
- State updates flow through parent component
- Calculation results persist across tab switches

#### Verification

| Test | Result |
|------|--------|
| Select preset on Stormwater tab | ✅ Values populated |
| Switch to Sanitary tab | ✅ Preset selection persisted, project name intact |
| Switch to Water Service tab | ✅ Project name persisted |
| Switch back to Stormwater | ✅ All values and results intact |
| TypeScript compilation | ✅ No errors |

#### Technical Notes

- State persistence is handled entirely in React (no localStorage/sessionStorage)
- Preset loading is async and fetches all three scenarios in parallel
- Tab components are now "controlled components" receiving state via props
- No database changes required - frontend-only fix

---

## Landing Page & Marketing Website

### Overview

The landing page is the first impression for potential customers. It must clearly communicate our value proposition as a SaaS platform that helps Calgary builders, architects, and developers navigate the complex world of building codes and permits.

### Landing Page Structure

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              NAVIGATION BAR                                      │
│  [Logo: CodeCheck Calgary]  [Features]  [Pricing]  [Blog]  [Login]  [Sign Up]   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                           HERO SECTION                                           │
│                                                                                  │
│     "Get Your Calgary Building Permit Right the First Time"                     │
│                                                                                  │
│     AI-powered code compliance checking that catches issues before              │
│     the City does. Reduce permit delays by 80%.                                 │
│                                                                                  │
│     [Start Free Trial]            [Watch Demo Video]                            │
│                                                                                  │
│     ✓ NBC(AE) 2023 Compliant    ✓ Calgary Bylaws    ✓ SDAB Insights            │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                        PROBLEM/SOLUTION SECTION                                  │
│                                                                                  │
│  "The Average Permit Takes 3 Submissions to Approve"                            │
│                                                                                  │
│  [BEFORE]                              [AFTER]                                  │
│  ┌─────────────────────┐               ┌─────────────────────┐                  │
│  │ • 6-8 week delays   │     →         │ • First-pass ready  │                  │
│  │ • $2,000+ in fees   │               │ • Confidence score  │                  │
│  │ • Guessing game     │               │ • Full compliance   │                  │
│  └─────────────────────┘               └─────────────────────┘                  │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                          THREE MODES SECTION                                     │
│                                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                          │
│  │   EXPLORE   │    │    GUIDE    │    │   REVIEW    │                          │
│  │             │    │             │    │             │                          │
│  │ "What does  │    │ "What do I  │    │ "Are my     │                          │
│  │  the code   │    │  need for   │    │  drawings   │                          │
│  │  say about  │    │  my project │    │  compliant? │                          │
│  │  stairs?"   │    │  at 123     │    │  Check now. │                          │
│  │             │    │  Main St?"  │    │             │                          │
│  │ [Try Now]   │    │ [Try Now]   │    │ [Try Now]   │                          │
│  └─────────────┘    └─────────────┘    └─────────────┘                          │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                        WHAT WE CHECK AGAINST                                     │
│                                                                                  │
│  Our system validates your plans against 15+ regulatory sources:                │
│                                                                                  │
│  [NBC 2023]  [NECB 2020]  [Bylaw 1P2007]  [STANDATA]  [Calgary Amendments]      │
│                                                                                  │
│  → 324+ specific code requirements                                              │
│  → 68 Calgary zone designations                                                 │
│  → 1,433 SDAB decisions analyzed                                                │
│  → 188,019 permits for pattern detection                                        │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                          SOCIAL PROOF SECTION                                    │
│                                                                                  │
│  "Trusted by Calgary's Building Professionals"                                  │
│                                                                                  │
│  ★★★★★                         ★★★★★                         ★★★★★             │
│  "Saved us from a major        "The SDAB risk                "Finally, a tool  │
│   setback issue that           assessment alone               that knows       │
│   would have cost $15K"        is worth the price"           Calgary codes"    │
│                                                                                  │
│  - John D., Builder            - Sarah M., Architect         - Mike T., Dev    │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                          PRICING PREVIEW                                         │
│                                                                                  │
│  Simple, transparent pricing. Cancel anytime.                                   │
│                                                                                  │
│  [Starter: $49/mo]    [Professional: $199/mo]    [Enterprise: Custom]           │
│                                                                                  │
│                    [See Full Pricing Details →]                                 │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                               CTA SECTION                                        │
│                                                                                  │
│     Ready to streamline your permit process?                                    │
│                                                                                  │
│     [Start Your 14-Day Free Trial]    No credit card required.                 │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                               FOOTER                                             │
│  [About] [Contact] [Privacy] [Terms] [API Docs] [Status]                        │
│                                                                                  │
│  © 2026 CodeCheck Calgary. Made in Alberta 🍁                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Messaging Points

1. **Value Proposition**: "Get your permit right the first time"
2. **Pain Point**: Average 3 submissions, 6-8 weeks delay, costly revisions
3. **Solution**: AI-powered compliance checking before submission
4. **Credibility**: Based on actual Calgary codes, SDAB data, permit patterns
5. **Trust**: Local focus (Calgary-specific), professional audience

### Feature Descriptions (for landing page)

| Feature | User-Facing Description | Hidden Technical Detail |
|---------|-------------------------|------------------------|
| EXPLORE Mode | "Search and understand any building code requirement instantly" | RAG + semantic search over structured NBC database |
| GUIDE Mode | "Enter your address, get a complete permit checklist tailored to your project" | Parcel-zone linking + requirement generation |
| REVIEW Mode | "Upload drawings, get a detailed compliance report with code references" | VLM-free PDF extraction + rule engine matching |
| SDAB Insights | "Know your appeal success rate before you build" | ML classification from 1,433 SDAB decisions |
| Risk Assessment | "Identify potential issues before they become expensive problems" | Pattern matching from 188,019 permit applications |

### Do NOT Expose

- **Specific algorithms** used for compliance checking
- **Database schema** or internal data structures
- **Extraction methodologies** for codes or drawings
- **Machine learning model** details
- **Proprietary rule engine** logic
- **Data sources** beyond what's publicly known (NBC, Bylaws)

---

## Authentication & Authorization System

### Overview

Multi-tenant SaaS requiring secure authentication, role-based access control, and subscription management.

### Authentication Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AUTHENTICATION FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │  User    │────▶│   Auth0/     │────▶│   Backend    │────▶│   Database   │   │
│  │  Client  │◀────│   Clerk      │◀────│   FastAPI    │◀────│   PostgreSQL │   │
│  └──────────┘     └──────────────┘     └──────────────┘     └──────────────┘   │
│                          │                    │                                  │
│                          │ JWT Token          │ Validate Token                   │
│                          ▼                    ▼                                  │
│                   ┌──────────────┐     ┌──────────────┐                         │
│                   │   OAuth      │     │   RBAC       │                         │
│                   │   Providers  │     │   Middleware │                         │
│                   │   (Google,   │     │              │                         │
│                   │   Microsoft) │     │              │                         │
│                   └──────────────┘     └──────────────┘                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Authentication Methods

1. **Email/Password** - Traditional signup with email verification
2. **Google OAuth** - One-click Google sign-in
3. **Microsoft OAuth** - Enterprise SSO for architectural firms
4. **Magic Link** - Passwordless email login option

### User Roles & Permissions

| Role | Permissions | Use Case |
|------|-------------|----------|
| `free_user` | Explore mode (5 queries/day), Guide mode preview | Trial users |
| `starter` | Explore (unlimited), Guide (10 projects/mo) | Individual builders |
| `professional` | All modes, 50 projects/mo, API access | Architects, designers |
| `enterprise` | Unlimited, priority support, custom integrations | Firms, developers |
| `admin` | All + user management, analytics | Internal staff |

### Database Schema for Auth

```sql
-- Users table (managed by Auth0/Clerk, synced locally)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    auth_provider_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    role VARCHAR(50) DEFAULT 'free_user',
    subscription_tier VARCHAR(50),
    subscription_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    metadata JSONB
);

-- Organizations (for team features)
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50),
    max_seats INTEGER,
    owner_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Organization members
CREATE TABLE organization_members (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50) DEFAULT 'member',
    invited_by UUID REFERENCES users(id),
    joined_at TIMESTAMP DEFAULT NOW()
);

-- API keys for programmatic access
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    scopes TEXT[],
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Security Requirements

1. **Password Requirements**: Min 12 chars, complexity rules, breach detection
2. **MFA Support**: TOTP, SMS (optional), passkeys (future)
3. **Session Management**: 24h expiry, single device option, session listing
4. **Rate Limiting**: Login attempts (5/min), API calls (tier-based)
5. **Audit Logging**: All auth events logged with IP, user agent, outcome

### Recommended Auth Provider: **Clerk**

| Feature | Benefit |
|---------|---------|
| Pre-built components | React/Next.js ready, reduces dev time |
| OAuth built-in | Google, Microsoft, GitHub out of box |
| User management | Dashboard for admin, no custom build needed |
| Webhooks | Sync user events to our backend |
| Organizations | Team/firm support built-in |
| Pricing | Free tier available, scales well |

---

## Pricing Model

### Pricing Strategy

Based on:
1. **Value-based pricing**: What is a rejected permit worth? ($2,000-10,000 in delays)
2. **Competitive analysis**: Similar SaaS tools in construction tech
3. **Usage tiers**: Align with user types (hobbyist → professional → enterprise)

### Pricing Tiers

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    PRICING PLANS                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐            │
│  │      FREE       │ │     STARTER     │ │  PROFESSIONAL   │ │   ENTERPRISE    │            │
│  │                 │ │                 │ │   ⭐ POPULAR     │ │                 │            │
│  │   $0/forever    │ │    $49/month    │ │   $199/month    │ │ Custom Pricing  │            │
│  │                 │ │  ($39/mo annual)│ │ ($159/mo annual)│ │                 │            │
│  │                 │ │                 │ │                 │ │                 │            │
│  │ ✓ Explore Mode  │ │ ✓ Unlimited     │ │ ✓ Everything in │ │ ✓ Everything in │            │
│  │   (25/month)    │ │   Explore       │ │   Starter, plus:│ │   Professional  │            │
│  │                 │ │                 │ │                 │ │                 │            │
│  │ ✓ Guide Mode    │ │ ✓ Guide Mode    │ │ ✓ Review Mode   │ │ ✓ Unlimited     │            │
│  │   (3 projects)  │ │   (15/month)    │ │   (50/month)    │ │   everything    │            │
│  │                 │ │                 │ │                 │ │                 │            │
│  │ ✓ NBC(AE) 2023  │ │ ✓ Review Mode   │ │ ✓ SDAB risk     │ │ ✓ API access    │            │
│  │   access        │ │   (5/month)     │ │   assessment    │ │                 │            │
│  │                 │ │                 │ │                 │ │ ✓ Custom        │            │
│  │ ✓ Basic         │ │ ✓ Calgary LUB   │ │ ✓ Priority      │ │   integrations  │            │
│  │   checklist     │ │                 │ │   support       │ │                 │            │
│  │                 │ │ ✓ PDF export    │ │                 │ │ ✓ Dedicated     │            │
│  │ ✓ Community     │ │                 │ │ ✓ Team collab   │ │   support       │            │
│  │   support       │ │ ✓ Email support │ │   (5 seats)     │ │                 │            │
│  │                 │ │                 │ │                 │ │ ✓ SLA guarantee │            │
│  │                 │ │                 │ │ ✓ API access    │ │                 │            │
│  │ [Get Started]   │ │  [Start Trial]  │ │  [Start Trial]  │ │ [Contact Sales] │            │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘            │
│                                                                                               │
│           Free tier is forever. Paid plans include 14-day free trial.                        │
│                         No credit card required to start.                                     │
│                                                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Feature Matrix

| Feature | Free | Starter | Professional | Enterprise |
|---------|------|---------|--------------|------------|
| Explore Mode | 25/month | Unlimited | Unlimited | Unlimited |
| Guide Mode | 3 projects/mo | 15/month | 50/month | Unlimited |
| Review Mode | — | 5/month | 50/month | Unlimited |
| NBC(AE) 2023 Access | ✓ | ✓ | ✓ | ✓ |
| Calgary Land Use Bylaw | — | ✓ | ✓ | ✓ |
| SDAB Risk Assessment | — | — | ✓ | ✓ |
| PDF Reports | — | Basic | Detailed | Custom |
| API Access | — | — | ✓ | ✓ |
| Team Members | 1 | 1 | 5 | Custom |
| Support | Community | Email | Priority | Dedicated |
| Custom Integrations | — | — | — | ✓ |

### Free Tier Strategy

**Purpose**: Lower barrier to entry, build trust, encourage upgrades

**Free Tier Features**:
- 25 Explore searches/month (code lookup)
- 3 Guide projects/month (basic permit guidance)
- NBC(AE) 2023 code access
- Basic compliance checklist
- Community support (forums, docs)

**Conversion Strategy**:
1. Show upgrade prompts when limits approached (20+ searches)
2. Preview locked features (show SDAB risk with blur)
3. Email nurture sequence after 7 days of activity
4. Highlight time savings ("You saved 2 hours this month")

### Payment Integration: **Stripe**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PAYMENT FLOW                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  User signs up → Free tier (forever) → Upgrade prompt when limits hit           │
│                       │                        │                                 │
│                       ▼                        ▼                                 │
│              [Using Free Tier]         [Stripe Checkout]                         │
│               - 25 searches/mo          - Credit Card                            │
│               - 3 Guide projects        - Apple/Google Pay                       │
│               - Community support       - Bank Transfer (enterprise)             │
│                       │                        │                                 │
│                       ▼                        ▼                                 │
│              [Upgrade Prompts]         [Paid Subscription]                       │
│              - "Need more searches?"   - Full tier access                        │
│              - Feature previews        - 14-day trial for paid                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Revenue Projections

| Scenario | Year 1 | Year 2 | Year 3 |
|----------|--------|--------|--------|
| Conservative (100 paid) | $120K | $240K | $400K |
| Moderate (500 paid) | $600K | $1.2M | $2M |
| Aggressive (2000 paid) | $2.4M | $4.8M | $8M |

---

## Blog System

### Purpose

1. **SEO**: Attract organic traffic for Calgary building code queries
2. **Authority**: Establish expertise in Calgary construction compliance
3. **Content Marketing**: Convert readers to trial users
4. **Education**: Help users understand the value before signup

### Blog Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BLOG SYSTEM                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Content Types:                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Code Updates   │  │  How-To Guides  │  │  Case Studies   │                  │
│  │                 │  │                 │  │                 │                  │
│  │ "NBC 2023       │  │ "Complete Guide │  │ "How We Helped  │                  │
│  │  Changes You    │  │  to Secondary   │  │  XYZ Builder    │                  │
│  │  Need to Know"  │  │  Suite Permits" │  │  Save 6 Weeks"  │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  SDAB Insights  │  │  Industry News  │  │  Product Updates│                  │
│  │                 │  │                 │  │                 │                  │
│  │ "What SDAB      │  │ "Calgary's New  │  │ "New Feature:   │                  │
│  │  Decision Data  │  │  Development    │  │  Drawing        │                  │
│  │  Reveals About  │  │  Priorities     │  │  Review Now     │                  │
│  │  Setback        │  │  for 2026"      │  │  Available"     │                  │
│  │  Appeals"       │  │                 │  │                 │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│                                                                                  │
│  Technical Stack:                                                                │
│  - Static Generation (Next.js) for SEO                                          │
│  - MDX for rich content                                                          │
│  - Categories & Tags                                                             │
│  - Related posts                                                                 │
│  - Newsletter signup                                                             │
│  - Social sharing                                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Initial Blog Post: Launch Announcement

**Title**: "Introducing CodeCheck Calgary: AI-Powered Building Code Compliance for Alberta"

**Structure**:
```markdown
# Introducing CodeCheck Calgary: AI-Powered Building Code Compliance for Alberta

*January 2026 | 5 min read*

## The Problem We're Solving

If you've ever applied for a building permit in Calgary, you know the frustration.
The average residential permit takes 3 submissions before approval. Commercial
projects? Even worse. Each resubmission means weeks of delay, thousands in
holding costs, and the stress of uncertainty.

**Why does this happen?**

Calgary's building approval process requires compliance with:
- The National Building Code of Canada 2023 (Alberta Edition)
- The National Energy Code for Buildings 2020
- Calgary Land Use Bylaw 1P2007
- Dozens of STANDATA bulletins and amendments
- Hundreds of referenced CSA, ULC, and ASTM standards

That's thousands of pages of requirements. Even experienced professionals miss things.

## Our Solution

CodeCheck Calgary is an AI-powered compliance checking platform built
specifically for Calgary's regulatory environment. We've done something
that's never been done before: **we've digitized and structured the
entire NBC(AE) 2023 Part 9 residential code into a searchable,
machine-readable format**.

This means our system can:

### 1. EXPLORE: Search Any Code Requirement Instantly

"What's the minimum stair width for a residential exit?"

Instead of flipping through a 1,200-page PDF, get the answer immediately
with the exact article reference.

### 2. GUIDE: Know What You Need Before You Design

Enter your property address. We'll tell you:
- What zone you're in
- What's allowed to be built
- What permits you'll need
- What common issues to avoid at that location

We've analyzed **188,019 Calgary development permits** to identify
patterns in what gets approved and what gets refused.

### 3. REVIEW: Check Your Drawings Before the City Does

Upload your plans. Our system extracts dimensions and specifications,
then checks them against every applicable code requirement. You'll get
a detailed report showing:
- ✅ What passes
- ⚠️ What needs attention
- 📋 Exact code references for everything

## What We Review Against

Our database includes:

| Source | Coverage |
|--------|----------|
| NBC(AE) 2023 | 324+ requirements from Part 9 residential |
| Calgary Zoning | 68 zone designations with rules |
| SDAB Decisions | 1,433 appeal outcomes analyzed |
| Development Permits | 188,019 permit records for pattern detection |

We're continuously expanding coverage to include commercial (Part 3),
energy code (NECB 2020), and more specialized requirements.

## Who This Is For

- **Builders** who want to avoid costly resubmissions
- **Architects & Designers** who need quick code lookups
- **Developers** planning multi-unit projects in Calgary
- **Homeowners** considering renovations or secondary suites

## Try It Free

We're launching with a 14-day free trial. No credit card required.

[Start Your Free Trial →]

---

*CodeCheck Calgary is built by construction industry veterans and AI
engineers who believe technology should make building easier, not harder.
We're based in Calgary, and we understand local requirements because
we live them.*

Questions? Email us at hello@codecheckcalgary.ca
```

### Blog Content Calendar (First 3 Months)

| Week | Title | Category | Goal |
|------|-------|----------|------|
| Launch | "Introducing CodeCheck Calgary" | Announcement | Brand awareness |
| 2 | "Complete Guide to Calgary Secondary Suite Permits" | How-To | SEO traffic |
| 3 | "NBC 2023 vs NBC 2019: Key Changes for Residential" | Code Updates | Authority |
| 4 | "What 1,433 SDAB Decisions Tell Us About Setback Appeals" | SDAB Insights | Differentiation |
| 5 | "The True Cost of Permit Delays in Calgary" | Industry | Pain point |
| 6 | "Understanding Calgary's R-CG Zone Requirements" | How-To | SEO traffic |
| 7 | "Stair Code Requirements Explained (NBC 9.8)" | Code Explainer | SEO traffic |
| 8 | "5 Common Permit Mistakes Calgary Builders Make" | How-To | Lead gen |
| 9 | "Fire Separation Requirements for Attached Garages" | Code Explainer | SEO traffic |
| 10 | "Laneway Housing in Calgary: Zoning & Code Guide" | How-To | Trend topic |
| 11 | "REVIEW Mode: How AI Checks Your Drawings" | Product | Feature launch |
| 12 | "Q1 2026: Calgary Development Trends" | Industry | Newsletter content |

---

## Standards & Codes We Review Against

### Complete Regulatory Framework

CodeCheck Calgary validates building plans against the following regulatory sources:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    REGULATORY SOURCES WE CHECK                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  PRIMARY BUILDING CODES                                                          │
│  ═══════════════════                                                             │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ National Building Code of Canada 2023 - Alberta Edition (NBC(AE))       │    │
│  │                                                                          │    │
│  │ Part 3: Fire Protection, Occupant Safety, and Accessibility             │    │
│  │   - 3.1 General                                                          │    │
│  │   - 3.2 Building Fire Safety                                             │    │
│  │   - 3.3 Safety within Floor Areas                                        │    │
│  │   - 3.4 Exits                                                            │    │
│  │   - 3.5 Vertical Transportation                                          │    │
│  │   - 3.6 Service Facilities                                               │    │
│  │   - 3.7 Health Requirements                                              │    │
│  │   - 3.8 Barrier-Free Design                                              │    │
│  │                                                                          │    │
│  │ Part 9: Housing and Small Buildings (PRIMARY FOCUS)                      │    │
│  │   - 9.5 Accessibility ✅                                                  │    │
│  │   - 9.6 Glass ✅                                                          │    │
│  │   - 9.7 Windows, Doors, Skylights ✅                                      │    │
│  │   - 9.8 Stairs, Ramps, Handrails, Guards ✅                               │    │
│  │   - 9.9 Means of Egress ✅                                                │    │
│  │   - 9.10 Fire Protection ✅                                               │    │
│  │   - 9.11 Sound Transmission ✅                                            │    │
│  │   - 9.12 Excavation ✅                                                    │    │
│  │   - 9.13 Dampproofing/Waterproofing ✅                                    │    │
│  │   - 9.14 Drainage ✅                                                      │    │
│  │   - 9.15 Footings and Foundations ✅                                      │    │
│  │   - 9.16 Floors-on-Ground 🔄                                              │    │
│  │   - 9.17 Columns 🔄                                                       │    │
│  │   - 9.18 Crawl Spaces 🔄                                                  │    │
│  │   - 9.19-9.36 (Remaining sections - in progress)                         │    │
│  │                                                                          │    │
│  │ ✅ = Extracted & Verified   🔄 = In Progress                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ National Energy Code for Buildings 2020 (NECB)                           │    │
│  │                                                                          │    │
│  │ - Part 3: Building Envelope                                              │    │
│  │ - Part 4: Lighting                                                       │    │
│  │ - Part 5: HVAC                                                           │    │
│  │ - Part 6: Service Water Heating                                          │    │
│  │ - Part 8: Performance Path                                               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  CALGARY MUNICIPAL REGULATIONS                                                   │
│  ═══════════════════════════                                                     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Land Use Bylaw 1P2007                                                    │    │
│  │                                                                          │    │
│  │ Coverage:                                                                │    │
│  │ - 68 land use districts (zones) ✅                                       │    │
│  │ - 10,249 zone polygons mapped ✅                                         │    │
│  │ - 577,803 property-to-zone mappings ✅                                   │    │
│  │                                                                          │    │
│  │ Key Regulations Checked:                                                 │    │
│  │ - Maximum building height                                                │    │
│  │ - Floor Area Ratio (FAR)                                                 │    │
│  │ - Lot coverage                                                           │    │
│  │ - Setback requirements (front, side, rear)                               │    │
│  │ - Parking requirements                                                   │    │
│  │ - Landscaping requirements                                               │    │
│  │ - Use permissions (discretionary vs permitted)                           │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Calgary-Specific Amendments & Guidelines                                 │    │
│  │                                                                          │    │
│  │ - Calgary Amendments to NBC(AE)                                          │    │
│  │ - Calgary Residential Infill Guidelines                                  │    │
│  │ - Secondary Suite Policy                                                 │    │
│  │ - Laneway/Backyard Suite Regulations                                     │    │
│  │ - Green Line TOD Area Plans                                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ALBERTA PROVINCIAL                                                              │
│  ═════════════════                                                               │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ STANDATA Bulletins                                                       │    │
│  │                                                                          │    │
│  │ Alberta-specific interpretations and amendments to the NBC, including:   │    │
│  │ - Building Code interpretations                                          │    │
│  │ - Fire Code bulletins                                                    │    │
│  │ - Plumbing Code bulletins                                                │    │
│  │ - Safety Codes Act requirements                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  REFERENCED STANDARDS (Selected - NBC references 200+)                           │
│  ═══════════════════                                                             │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ CSA Standards (Canadian Standards Association)                           │    │
│  │ - CSA A23.1/A23.2: Concrete                                              │    │
│  │ - CSA A165: Masonry                                                      │    │
│  │ - CSA A370: Connectors for joist hangers                                 │    │
│  │ - CSA A440: Windows                                                      │    │
│  │ - CSA B149: Gas installation                                             │    │
│  │ - CSA S406: Permanent wood foundations                                   │    │
│  │ - CSA O86: Wood engineering design                                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ ULC Standards (Underwriters Laboratories of Canada)                      │    │
│  │ - ULC S102: Fire spread ratings                                          │    │
│  │ - ULC S134: Fire testing of exterior wall assemblies                     │    │
│  │ - ULC S701: Thermal insulation                                           │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ ASTM Standards (American Society for Testing and Materials)              │    │
│  │ - ASTM C4: Clay drain tile                                               │    │
│  │ - ASTM C412M: Concrete drain tile                                        │    │
│  │ - ASTM C700: Vitrified clay pipe                                         │    │
│  │ - (Referenced in NBC for specific material requirements)                 │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  DATA-DRIVEN INSIGHTS                                                            │
│  ════════════════════                                                            │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ SDAB (Subdivision and Development Appeal Board) Decisions                │    │
│  │                                                                          │    │
│  │ - 1,433 appeal records analyzed ✅                                       │    │
│  │ - Success rates by property type                                         │    │
│  │ - Common grounds for appeal                                              │    │
│  │ - Variance patterns                                                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Development Permit Records                                               │    │
│  │                                                                          │    │
│  │ - 188,019 permit applications analyzed ✅                                │    │
│  │ - 4,293 refusals with deficiency patterns                                │    │
│  │ - Approval rates by zone and project type                                │    │
│  │ - Common deficiencies leading to resubmission                            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Current Database Statistics

| Category | Count | Status |
|----------|-------|--------|
| NBC Articles Extracted | 145 | ✅ Sections 9.5-9.15 |
| NBC Requirements Structured | 324 | ✅ Verified |
| Calgary Zones | 68 | ✅ Complete |
| Zone Polygons | 10,249 | ✅ With HEIGHT/FAR |
| Parcel Records | 414,605 | ✅ Linked to zones |
| Property-Zone Mappings | 577,803 | ✅ Complete |
| SDAB Decisions | 1,433 | ✅ Analyzed |
| Development Permits | 188,019 | ✅ Pattern extracted |

### Compliance Checking Coverage

**What We Currently Check (Phase 1 - Residential Part 9)**:

| Category | Articles | Key Checks |
|----------|----------|------------|
| Stairs | 9.8.1-9.8.8 | Width, risers, runs, headroom, handrails, guards |
| Egress | 9.9.1-9.9.9 | Exit widths, travel distance, corridor dimensions |
| Fire Protection | 9.10.1-9.10.17 | Fire separations, ratings, flame spread |
| Foundations | 9.15.1-9.15.5 | Footing sizes, wall thickness, reinforcement |
| Glass | 9.6.1-9.6.7 | Safety glazing, tempered requirements |
| Windows/Doors | 9.7.1-9.7.6 | Egress windows, dimensions, hardware |

**Coming Soon (Phase 2)**:

| Category | Target Date |
|----------|-------------|
| Roof Framing (9.23) | Q1 2026 |
| Wall Framing (9.20-9.22) | Q1 2026 |
| Heating/Ventilation (9.32-9.33) | Q2 2026 |
| Plumbing (9.31) | Q2 2026 |
| Part 3 Commercial | Q3 2026 |
| NECB Energy Code | Q4 2026 |

---

## Implementation Notes for Web Sections

### Frontend Stack for Landing/Auth/Blog

```
Technology Choices:
├── Framework: Next.js 14 (App Router)
│   - Server components for landing (fast load)
│   - Static generation for blog (SEO)
│   - API routes for auth callbacks
│
├── Authentication: Clerk
│   - <SignIn>, <SignUp> components
│   - useUser() hook for user state
│   - Webhooks to sync with backend
│
├── Payments: Stripe
│   - Stripe Checkout for subscriptions
│   - Customer portal for management
│   - Webhooks for payment events
│
├── Blog: MDX + Contentlayer
│   - Static generation at build time
│   - Rich content with components
│   - Automatic table of contents
│
└── Styling: Tailwind CSS + shadcn/ui
    - Consistent design system
    - Pre-built components
    - Dark mode support
```

### API Endpoints Needed

```
Authentication:
POST   /api/auth/webhook          # Clerk webhook handler
GET    /api/users/me              # Current user profile
PATCH  /api/users/me              # Update profile
DELETE /api/users/me              # Delete account

Subscriptions:
POST   /api/subscriptions/checkout  # Create Stripe checkout
GET    /api/subscriptions/portal    # Get customer portal URL
POST   /api/subscriptions/webhook   # Stripe webhook handler
GET    /api/subscriptions/current   # Current subscription status

Usage Tracking:
GET    /api/usage/current           # Current period usage
GET    /api/usage/history           # Historical usage

Blog (if dynamic):
GET    /api/blog/posts              # List posts
GET    /api/blog/posts/:slug        # Get post by slug
POST   /api/blog/newsletter         # Newsletter signup
```

---

### Session: January 11, 2026

**Status: Phase 3 - AI Q&A System with Hybrid Search Complete**

#### Major Accomplishments

| Component | Status | Description |
|-----------|--------|-------------|
| **LLM Docker Container** | ✅ Complete | Separate container for LiquidAI LFM2.5-1.2B model |
| **llama.cpp Integration** | ✅ Complete | Switched from transformers to llama.cpp for efficient CPU inference |
| **Hybrid Search (pgvector)** | ✅ Complete | Vector + keyword search with RRF fusion |
| **Embedding Generation** | ✅ Complete | 3128 articles + 41 STANDATA bulletins embedded |
| **Academic Citation System** | ✅ Complete | [1], [2] style citations with References section |
| **Chat Widget Enhancement** | ✅ Complete | Blinking loader, academic-style references display |
| **Frontend Type Updates** | ✅ Complete | Reference interface, ChatResponse with citations |

#### AI Q&A Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Q&A CHAT SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   User Question                                                 │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────┐                  │
│   │         HYBRID SEARCH                    │                  │
│   │                                          │                  │
│   │   1. Extract query embedding             │                  │
│   │   2. Vector search (pgvector cosine)     │                  │
│   │   3. Keyword search (PostgreSQL FTS)     │                  │
│   │   4. RRF Fusion (k=60)                   │                  │
│   │   5. Deduplicate & rank                  │                  │
│   └─────────────────────────────────────────┘                  │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────┐                  │
│   │         CONTEXT BUILDER                  │                  │
│   │                                          │                  │
│   │   • Number sources [1], [2], [3]...      │                  │
│   │   • Build context from articles/standata │                  │
│   │   • Format references                    │                  │
│   └─────────────────────────────────────────┘                  │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────┐                  │
│   │    LLM SERVICE (Docker Container)        │                  │
│   │                                          │                  │
│   │    Model: LiquidAI LFM2.5-1.2B-Instruct │                  │
│   │    Format: GGUF Q4_K_M quantization      │                  │
│   │    Engine: llama.cpp (CPU optimized)     │                  │
│   │    Memory: ~2GB for inference            │                  │
│   └─────────────────────────────────────────┘                  │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────┐                  │
│   │         RESPONSE FORMATTER               │                  │
│   │                                          │                  │
│   │   • answer_with_citations (text + [N])   │                  │
│   │   • references (numbered list)           │                  │
│   │   • sources (detailed context items)     │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Files Created/Modified

**New Files:**
| File | Purpose |
|------|---------|
| `llm_service/Dockerfile` | Docker container for LLM service |
| `llm_service/main.py` | FastAPI LLM service with llama.cpp |
| `llm_service/requirements.txt` | LLM service dependencies |
| `app/services/embedding_service.py` | Sentence-transformers embedding service |
| `scripts/generate_embeddings.py` | Batch embedding generation script |

**Modified Files:**
| File | Changes |
|------|---------|
| `docker-compose.yml` | Added llm-service container with resource limits |
| `app/api/chat.py` | Hybrid search, citations, references |
| `app/models/standata.py` | Added embedding column (vector 384) |
| `app/services/llm_service.py` | HTTP client for containerized LLM |
| `frontend/src/api/client.ts` | Reference type, updated ChatResponse |
| `frontend/src/components/ChatWidget.tsx` | Academic citations, blinking loader |

#### Database Changes

```sql
-- Added embedding columns for vector search
ALTER TABLE articles ADD COLUMN embedding vector(384);
ALTER TABLE standata ADD COLUMN embedding vector(384);

-- Vector indexes for similarity search
CREATE INDEX idx_articles_embedding ON articles USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_standata_embedding ON standata USING ivfflat (embedding vector_cosine_ops);
```

#### Embedding Statistics

| Table | Records | Status |
|-------|---------|--------|
| Articles | 3,128 | ✅ All embedded |
| STANDATA | 41 | ✅ All embedded |
| Total | 3,169 | Complete |

#### Technology Stack Updates

| Component | Previous | Current | Benefit |
|-----------|----------|---------|---------|
| LLM Runtime | transformers | llama.cpp | 50% less memory, faster CPU |
| Search | Keyword only | Hybrid (vector + keyword) | Better semantic results |
| Model Format | PyTorch | GGUF Q4_K_M | 4x smaller, faster load |
| Citations | Simple sources | Academic [1], [2] style | Professional references |

#### LLM Container Configuration

```yaml
llm-service:
  build: ./llm_service
  ports:
    - "8081:8081"
  volumes:
    - llm_models:/models
  environment:
    - MODEL_REPO=LiquidAI/LFM2.5-1.2B-Instruct-GGUF
    - MODEL_FILE=LFM2.5-1.2B-Instruct-Q4_K_M.gguf
    - CONTEXT_SIZE=4096
    - N_THREADS=4
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 4G
```

#### Session Update: January 11, 2026 (Late Evening)

**Status: LFM2.5 Model Successfully Integrated**

##### Issue Resolved
- **Problem**: llama-cpp-python 0.2.90 didn't support LFM2 architecture ("unknown model architecture: 'lfm2'")
- **Solution**: Upgraded to llama-cpp-python 0.3.16 which includes LFM2 support
- **Reference**: https://docs.liquid.ai/lfm/inference/llama-cpp

##### Configuration Updates

| Setting | Value | Source |
|---------|-------|--------|
| llama-cpp-python | 0.3.16 | PyPI latest |
| temperature | 0.1 | LiquidAI docs |
| top_k | 50 | LiquidAI docs |
| top_p | 0.1 | LiquidAI docs |
| repeat_penalty | 1.05 | LiquidAI docs |

##### Prompt Engineering Improvements
- Optimized system prompt for LFM2.5's RAG/extraction strengths
- Added explicit example of good vs bad responses
- Reduced max_new_tokens to 150 for focused answers
- Included few-shot example in prompt

##### Verified Working
```bash
# Model info
curl http://localhost:8081/model-info
# Returns: LiquidAI/LFM2.5-1.2B-Instruct, 697 MB, loaded: true

# Chat test
curl -X POST http://localhost:8002/api/v1/chat/ask \
  -d '{"message": "What is the minimum stair width?"}'
# Returns: "The minimum stair width is 900 mm [2]..."
```

##### Resource Usage
- Model file: 697 MB
- Runtime memory: ~1.5 GB
- CPU during inference: ~300-400%
- Latency: ~20-30s per response (CPU inference)

#### Next Steps

1. ~~Complete LLM Container Build~~ ✅ Done
2. ~~Test End-to-End Q&A~~ ✅ Done
3. **Integrate Fee Schedule** - Connect real pricing to Quantity Survey module

---

*Document Version: 2.3*
*Last Updated: January 11, 2026*
*Added: AI Q&A with hybrid search, LLM Docker container, academic citation system, embedding generation*
*Updated: Technology stack with llama.cpp, pgvector integration, ChatWidget with references*

---

### Session: January 11, 2026 (Late Night)

**Status: Extraction Method Comparison Complete - Pythonic vs VLM**

#### Objective

Compare extraction quality between:
1. **Pythonic extraction** (pdfplumber, PyMuPDF)
2. **VLM extraction** (Qwen3-VL 30B via Ollama)

Target: NBC Part 1 articles that define Part 9 scope (Article 1.3.3.3)

#### Methods Tested

| Method | Library | Description |
|--------|---------|-------------|
| pdfplumber | pdfplumber | Standard PDF text extraction |
| pymupdf | PyMuPDF/fitz | Alternative PDF library, text mode |
| pymupdf_blocks | PyMuPDF/fitz | Block-level extraction for structure |
| vlm_qwen3vl_30b | Ollama + Qwen3-VL | Vision-Language Model OCR |

#### Qwen3-VL Configuration (Best Practices)

| Parameter | Value | Source |
|-----------|-------|--------|
| Model | qwen3-vl:30b | Ollama registry |
| DPI | 300 | Optimal for document OCR |
| Temperature | 0.7 | Qwen3-VL docs (document extraction) |
| Top_p | 0.8 | Qwen3-VL docs |
| Top_k | 20 | Default |
| num_predict | 8192 | Allow full article extraction |

#### Results Summary

| Method | Quality Score | Time | Text Length | Subsections |
|--------|--------------|------|-------------|-------------|
| **pdfplumber** | 91.67/100 | 4.69s | 2,062 chars | 3 |
| pymupdf | 87.50/100 | 0.064s | 2,334 chars | 3 |
| vlm_qwen3vl_30b | 83.33/100 | 71.4s | 2,377 chars | **6** |
| pymupdf_blocks | 79.17/100 | 0.06s | 2,359 chars | 3 |

#### Quality Analysis

**PDFPlumber (Highest Score: 91.67)**
- Extracted all numeric values: 3 storeys, 600m², 1200m², 2400m², 300m²
- **Issue**: Text has spacing problems ("Part 9of Division Bappliestoall...")
- Subsection parsing incomplete (only 3 of 6 sentences)
- Fast enough for production use (4.69s)

**VLM Qwen3-VL (Score: 83.33)**
- **Clean, readable text** with proper spacing
- **Correctly parsed all 6 sentences** with structure
- **Semantic labels** on numeric values (max_storeys, max_building_area_m2)
- Slower (71s) but best for accuracy-critical applications
- Better understanding of document structure

#### Key Finding: Quality Score vs Actual Quality

The automated quality score favors pythonic extraction because:
1. It found more numeric values (as a flat list)
2. Text length metrics don't penalize spacing issues

**However**, VLM extraction produced:
- Properly spaced, human-readable text
- Correct structural parsing (all 6 sentences)
- Semantically labeled data extraction
- Better for downstream NLP/RAG applications

#### Recommendation

| Use Case | Recommended Method |
|----------|-------------------|
| Bulk extraction (speed priority) | pymupdf (0.06s, 87.5%) |
| Balance of speed/quality | pdfplumber (4.69s, 91.67%) |
| Accuracy-critical extraction | VLM qwen3-vl:30b (71s, best structure) |
| Production Q&A database | Hybrid: pythonic + VLM validation |

#### Hybrid Approach (Recommended)

1. **First pass**: Use pdfplumber for fast bulk extraction
2. **Validation pass**: Use VLM on critical articles (Part 1 scope, Part 9 key sections)
3. **Store both**: Keep raw extraction + VLM-enhanced version
4. **Use VLM for**:
   - Articles with complex tables
   - Critical dimensional requirements
   - Scope-defining articles (like 1.3.3.3)

#### Files Created

```
app/scripts/compare_extraction_methods.py   # Comparison script
data/extraction_comparison/
├── comparison_summary_20260111_014839.json
├── pdfplumber_extraction_20260111_014839.json
├── pymupdf_extraction_20260111_014839.json
├── pymupdf_blocks_extraction_20260111_014839.json
└── vlm_qwen3vl_30b_extraction_20260111_014839.json
```

#### VLM Extracted Article 1.3.3.3 (Clean Text)

```
1.3.3.3. Application of Parts 9, 10 and 11

1) Part 9 of Division B applies to all buildings described in Article 1.1.1.1.
   of 3 storeys or less in building height, having a building area not exceeding
   600 m², and used for major occupancies classified as
   a) Group B, Division 4, home-type care occupancies,
   b) Group C, residential occupancies,
   c) Group D, business and personal services occupancies,
   d) Group E, mercantile occupancies, or
   e) Group F, Divisions 2 and 3, medium- and low-hazard industrial occupancies.

2) Part 10 of Division B applies to all buildings described in Article 1.1.1.1.
   conforming to Sentence (3) in which accommodation is provided for an
   industrial workforce living and working in a temporary location.

[...sentences 3-6 also extracted with proper formatting...]
```

#### Next Steps

1. ✅ Extraction comparison complete
2. **Apply hybrid extraction** to remaining critical articles
3. **Re-extract Part 1 scope articles** using VLM for database
4. **Add extraction quality flags** to articles table (pythonic_only vs vlm_validated)

---

### Session: January 11, 2026 (Continued - VLM Extraction Pipeline)

**Status: Full VLM Extraction Pipeline Operational**

#### Objective

Implement production VLM extraction using Qwen3-VL 30B via LM Studio to re-extract ALL building codes with clean, properly-spaced text for improved semantic search quality.

#### Major Accomplishments

| Task | Status | Details |
|------|--------|---------|
| **VLM Extraction Script** | ✅ Complete | `app/scripts/vlm_extract_all.py` with LM Studio integration |
| **Database Repopulation Script** | ✅ Complete | `app/scripts/repopulate_db.py` for loading VLM JSON |
| **Database Model Update** | ✅ Complete | Added extraction tracking columns to `articles` table |
| **LM Studio Integration** | ✅ Complete | Switched from Ollama to LM Studio (35s vs 130s per page) |
| **LFM Bug Fix** | ✅ Complete | Fixed KV cache consecutive request bug in LLM service |
| **VLM Extraction Quality Test** | ✅ Complete | Semantic search correctly retrieves relevant articles |
| **NBC Part 1 Extraction** | ✅ Complete | Division A articles including 1.3.3.3 (701KB) |
| **NBC Part 9 General** | ✅ Complete | Sections 9.1-9.4 extracted (316KB) |
| **NBC Part 9 Full** | 🔄 In Progress | Main Part 9 sections (running overnight) |

#### LM Studio Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Server URL | http://10.0.0.133:8080 | OpenAI-compatible API |
| Model | qwen/qwen3-vl-30b | Vision-Language Model |
| Temperature | 0.7 | Optimal for document extraction |
| Top_p | 0.8 | Per Qwen3-VL documentation |
| Max Tokens | 8192 | Allow full article extraction |
| Image DPI | 300 | Optimal for OCR |

#### LFM Consecutive Request Bug Fix

**Problem:** LFM LLM failed with "llama_decode returned -1" on second consecutive request.

**Root Cause:** llama.cpp KV cache not being reset between requests.

**Solution Applied to `llm_service/main.py`:**
```python
def reset_model():
    """Reset the model's KV cache to fix consecutive request issues."""
    global _llm
    if _llm is not None:
        try:
            _llm.reset()  # Clear KV cache
            logger.debug("Model KV cache reset")
        except Exception as e:
            logger.warning(f"Could not reset model: {e}")

@app.post("/generate")
async def generate_response(request: GenerateRequest):
    reset_model()  # Reset before each request
    # ... rest of generation
```

**Verification:** Tested 3 consecutive requests - all succeeded.

#### Database Schema Updates

Added extraction tracking columns to `app/backend/app/models/codes.py`:

```python
class Article(Base):
    # ... existing columns ...

    # Extraction tracking (for VLM re-extraction)
    extraction_model = Column(String(100), nullable=True)  # e.g., "qwen3-vl:30b", "pdfplumber"
    extraction_confidence = Column(String(20), nullable=True)  # HIGH, MEDIUM, LOW
    vlm_extracted = Column(Boolean, default=False)  # True if extracted via VLM
    extraction_date = Column(DateTime, nullable=True)
```

#### Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `app/scripts/vlm_extract_all.py` | CREATE | Main VLM extraction script |
| `app/scripts/repopulate_db.py` | CREATE | Database reload with embeddings |
| `app/backend/app/models/codes.py` | MODIFY | Added extraction tracking columns |
| `app/backend/llm_service/main.py` | MODIFY | Fixed KV cache reset bug |
| `CLAUDE.md` | MODIFY | Added VLM pipeline documentation |
| `data/codes/vlm/` | CREATE | VLM extraction output directory |

#### VLM Extracted Files

| File | Size | Status | Articles |
|------|------|--------|----------|
| `nbc_ae_2023_part1_vlm.json` | 701 KB | ✅ Complete | 418 articles |
| `nbc_ae_2023_part9_general_vlm.json` | 316 KB | ✅ Complete | ~100 articles |
| `nbc_ae_2023_part9_vlm.json` | - | 🔄 In Progress | ~291 pages |
| `necb_2020_vlm.json` | - | ⏳ Pending | ~353 articles |
| `nfc_ae_2023_vlm.json` | - | ⏳ Pending | ~1,878 articles |
| `npc_2020_vlm.json` | - | ⏳ Pending | ~340 articles |

#### Extraction Performance

| Metric | Value |
|--------|-------|
| Average time per page | 35-40 seconds |
| Rest interval | 1 minute every 20 pages |
| Progress saving | Every 10 pages |
| Image format | PNG at 300 DPI |
| JSON output | Structured with articles array |

#### Quality Test Results

Tested semantic search with VLM-extracted articles:

**Query:** "What buildings does Part 9 apply to?"

**Top Result:** Article 1.3.3 (Application of Parts 9, 10 and 11)
- Similarity Score: 0.83
- Correctly identifies building height (3 storeys), area (600m²), and occupancy types
- Clean, properly-spaced text compared to pythonic extraction

**LFM Response Quality:**
- Accurate answer citing sources
- Proper formatting with code section references
- Fast response after KV cache fix

#### Extraction Pipeline Commands

```bash
# Start VLM extraction (runs overnight)
cd /Users/mohmmadhanafy/Building-code-consultant/app/backend
source .venv/bin/activate
python ../scripts/vlm_extract_all.py --all --output ../../../data/codes/vlm/

# Check extraction progress
tail -f data/codes/vlm/extraction_log.txt

# After extraction: Load to database with embeddings
python ../scripts/repopulate_db.py --source ../../../data/codes/vlm/ --backup

# Test semantic search
curl -X POST http://localhost:8002/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What buildings does Part 9 apply to?"}'
```

#### Next Steps

1. ✅ ~~Create VLM extraction script~~ - Complete
2. ✅ ~~Fix LFM consecutive request bug~~ - Complete
3. ✅ ~~Test extraction quality~~ - Complete
4. 🔄 Complete full Part 9 extraction (overnight)
5. ⏳ Extract remaining codes (NECB, NFC, NPC)
6. ⏳ Run `repopulate_db.py` to load all VLM articles
7. ⏳ Generate embeddings for all ~3000 articles
8. ⏳ Verify semantic search quality improvement

---

*Document Version: 2.5*
*Last Updated: January 11, 2026*
*Added: VLM extraction pipeline implementation, LM Studio integration, LFM KV cache bug fix, extraction tracking columns*
