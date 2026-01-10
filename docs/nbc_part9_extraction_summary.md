# NBC Part 9 Extraction Summary

**Date:** 2026-01-09
**Extraction Status:** Complete (Sections 9.5-9.36)

## Overview

This document summarizes the structured extraction of National Building Code of Canada 2023 - Alberta Edition (NBC(AE)) Part 9 - Houses and Small Buildings.

## Completed Sections

### Previously Extracted (9.5-9.21)

| Section | Title | Articles | Status |
|---------|-------|----------|--------|
| 9.5 | Site Preparation | - | Complete |
| 9.6 | Excavation | - | Complete |
| 9.7 | Backfill | - | Complete |
| 9.8 | Stairs, Ramps, Handrails and Guards | - | Complete |
| 9.9 | Means of Egress | - | Complete |
| 9.10 | Fire Protection | - | Complete |
| 9.11 | Sound Control | - | Complete |
| 9.12 | Interior Finishes | - | Complete |
| 9.13 | Dampproofing and Waterproofing | - | Complete |
| 9.14 | Drainage | - | Complete |
| 9.15 | Footings and Foundations | - | Complete |
| 9.16 | Floors-on-Ground | 11 | Complete |
| 9.17 | Columns | 12 | Complete |
| 9.18 | Crawl Spaces | 9 | Complete |
| 9.19 | Roof Spaces | 5 | Complete |
| 9.20 | Masonry and ICF Walls | 70 | Complete |
| 9.21 | Chimneys and Flues | 22 | Complete |

### Newly Extracted (9.22-9.36)

| Section | Title | Articles | Key Requirements |
|---------|-------|----------|------------------|
| 9.22 | Cladding | 21 | Min clearance 150mm above grade, stucco min 17mm |
| 9.23 | Roof and Wall Sheathing | 21 | Plywood min 7.5mm roof/6mm wall, OSB min 9.5mm |
| 9.24 | Fireplaces | 15 | Hearth extension min 400mm front, 200mm sides |
| 9.25 | Heat Transfer/Condensation | 14 | Calgary Zone 7A: Wall RSI 3.85, Ceiling RSI 8.81 |
| 9.26 | Thermal Insulation | 12 | Slab perimeter min 600mm horizontal/vertical |
| 9.27 | Air Barrier Systems | 12 | Max permeance 0.02 L/(s*m2) at 75 Pa |
| 9.28 | Vapour Barriers | 10 | Polyethylene min 0.15mm, max permeance 60 ng/(Pa*s*m2) |
| 9.29 | Reserved | 0 | Section reserved in NBC 2023 |
| 9.30 | Reserved | 0 | Section reserved in NBC 2023 |
| 9.31 | Service Facilities | 12 | Hot water max 49C at fixtures |
| 9.32 | Ventilation | 15 | Kitchen exhaust min 50 L/s, bathroom min 25 L/s |
| 9.33 | HVAC Equipment | 20 | Interior design temp 22C, Calgary design -33C |
| 9.34 | Elevating Devices | 10 | Platform lift max travel 3000mm in Part 9 |
| 9.35 | Garages and Carports | 16 | 45-min fire separation, 12.7mm Type X gypsum |
| 9.36 | Energy Efficiency | 24 | Zone 7A: Wall RSI 4.31, Ceiling RSI 10.43 |

## Key Dimensional Requirements Summary

### Calgary-Specific (Climate Zone 7A)

**Energy Efficiency (Section 9.36):**
- Above-grade walls: RSI 4.31 effective (R-24.5)
- Ceiling below attic: RSI 10.43 effective (R-59)
- Basement walls: RSI 2.98 effective (R-17)
- Windows: U <= 1.40 W/(m2K), ER >= 25
- Air tightness: <= 2.5 ACH @ 50 Pa
- Furnace: >= 95% AFUE
- HRV: >= 70% sensible recovery

**Thermal Envelope (Section 9.25):**
- Above-grade walls: RSI 3.85 min
- Ceiling below attic: RSI 8.81 min
- Basement walls: RSI 2.98 min

### Critical Dimensional Requirements

**Garages (Section 9.35):**
- Fire separation: 45 minutes
- Gypsum board: 12.7mm Type X
- Door rating: 20 minutes, self-closing
- Floor: 100mm below dwelling floor

**Ventilation (Section 9.32):**
- Principal system: 0.3 L/s per m2, min 50 L/s total
- Kitchen exhaust: min 50 L/s
- Bathroom exhaust: min 25 L/s
- Air intake height: min 450mm above grade
- Air intake separation from exhaust: min 1800mm

**Fireplaces (Section 9.24):**
- Hearth extension front (< 0.5 m2 opening): 400mm
- Hearth extension front (>= 0.5 m2 opening): 500mm
- Hearth extension sides: 200mm
- Combustion air duct: min 6450 mm2

**Cladding (Section 9.22):**
- Clearance above grade (general): 150mm
- Clearance above grade (masonry): 200mm
- Clearance above paved surface: 50mm

**Sheathing (Section 9.23):**
- Nail spacing at edges: max 150mm
- Nail spacing intermediate: max 300mm
- Panel edge distance: min 10mm
- Panel gap: 2-3mm

## File Locations

All structured JSON files are located at:
```
/Users/mohmmadhanafy/Building-code-consultant/data/codes/
```

File naming convention:
```
nbc_section_9.XX_structured.json
```

## Data Format

Each JSON file follows this structure:
```json
{
  "metadata": {
    "code": "National Building Code of Canada 2023 - Alberta Edition",
    "short_name": "NBC(AE)",
    "version": "2023",
    "section": "9.XX",
    "section_title": "...",
    "extraction_date": "2026-01-09",
    "verification_status": "pending_professional_review"
  },
  "articles": [
    {
      "article_number": "9.XX.X.X",
      "title": "...",
      "requirements": [
        {
          "id": "9.XX.X.X-1",
          "element": "...",
          "requirement_type": "dimensional|prescriptive|reference|material|prohibition",
          "min_value": number,
          "max_value": number,
          "unit": "mm|m|%|RSI|etc",
          "description": "...",
          "exact_quote": "..."
        }
      ]
    }
  ]
}
```

## Next Steps

1. **Database Import:** Run import scripts to load structured JSON into PostgreSQL database
2. **Professional Review:** All extractions marked as `pending_professional_review`
3. **Cross-Reference Validation:** Verify cross-references between sections
4. **STANDATA Integration:** Cross-reference with Alberta STANDATA bulletins for interpretations

## Notes

- Sections 9.29 and 9.30 are reserved in NBC 2023 (empty sections)
- Section 9.21 covers masonry chimneys; factory-built chimneys covered in 9.33.10
- Energy requirements in 9.36 may be superseded by NECB 2020 for some building types
- Calgary-specific climate data based on Zone 7A (approximately 5000 HDD)

---

**Extraction completed by:** Claude Opus 4.5
**Verification status:** Pending professional review
