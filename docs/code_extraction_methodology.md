# Building Code Extraction Methodology

This document describes the methodology used to extract building code requirements from official PDF documents and import them into the Calgary Building Code Expert System database.

## Overview

Building codes like the National Building Code of Canada (NBC) are published as PDF documents, not machine-readable formats. After extensive research, we confirmed that **no official APIs, JSON, XML, or structured data formats exist** for Canadian building codes. Therefore, we developed a custom extraction pipeline.

## Extraction Pipeline

### 1. Source Document Acquisition

**Official Sources Used:**
- NRC Publications Archive: https://nrc-publications.canada.ca
- Alberta Queen's Printer: https://www.qp.alberta.ca
- Calgary Open Data: https://data.calgary.ca

**Document Format:** PDF (non-printable electronic version)

### 2. PDF Text Extraction

**Tool Used:** `pdfplumber` (Python library)

**Why pdfplumber:**
- Handles complex PDF layouts better than PyPDF2
- Preserves table structures
- Provides page-by-page extraction
- Works with scanned and native PDFs

**Extraction Code Pattern:**
```python
import pdfplumber
import json

def extract_section(pdf_path, start_page, end_page):
    """Extract text from specific pages of a PDF."""
    extracted = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page - 1, end_page):
            page = pdf.pages[page_num]
            text = page.extract_text()
            extracted.append({
                "page": page_num + 1,
                "text": text
            })

    return extracted
```

### 3. Section Identification

**Process:**
1. Search PDF for section headers (e.g., "Section 9.8")
2. Identify page range for target section
3. Extract all pages in range

**NBC(AE) 2023 Section Locations:**
| Section | Title | Pages |
|---------|-------|-------|
| 9.8 | Stairs, Ramps, Handrails and Guards | 843-858 |
| 9.9 | Means of Egress | 855-870 |
| 9.10 | Fire Protection | 871-920 |

### 4. Raw Text Processing

**Output:** Raw JSON file with page-by-page text
```
data/codes/nbc_section_9.8_raw.json
```

**Challenges Addressed:**
- Text often runs together without spaces (e.g., "notlessthan860mm")
- Table data mixed with paragraph text
- Article numbers embedded in text flow
- Copyright footers on every page

### 5. Structured Data Creation

**Manual Review Required:** Due to the complexity of building code language and the legal implications of errors, human review is essential.

**Process:**
1. Parse raw text to identify article numbers (regex: `\d+\.\d+\.\d+\.\d+`)
2. Extract dimensional values (regex for mm, m, degrees, ratios)
3. Identify tables and parse min/max values
4. Map requirements to applicability conditions
5. Create structured JSON with verified values

**Structured JSON Schema:**
```json
{
  "metadata": {
    "code": "National Building Code of Canada 2023 - Alberta Edition",
    "short_name": "NBC(AE)",
    "version": "2023",
    "section": "9.8",
    "extraction_date": "2026-01-09",
    "extraction_method": "pdfplumber + manual verification",
    "verification_status": "pending_professional_review"
  },
  "articles": [
    {
      "article_number": "9.8.2.1",
      "title": "Stair Width",
      "full_text": "...",
      "requirements": [
        {
          "id": "9.8.2.1-1",
          "element": "stair_width",
          "requirement_type": "dimensional",
          "min_value": 900,
          "unit": "mm",
          "exact_quote": "...",
          "applies_to": ["residential"],
          "source_sentence": "9.8.2.1.(1)"
        }
      ]
    }
  ]
}
```

### 6. Database Import

**Script:** `app/scripts/import_nbc_codes.py`

**Database Models:**
- `Code` - The building code document (e.g., NBC(AE) 2023)
- `Article` - Individual code articles (e.g., 9.8.2.1)
- `Requirement` - Specific checkable requirements with values
- `RequirementCondition` - Conditions/exceptions for requirements

**Import Process:**
```bash
cd app/scripts
python import_nbc_codes.py --section 9.8
```

### 7. Verification

**Automated Checks:**
- Query database for key values
- Compare against source PDF
- Flag any mismatches

**Manual Verification Required:**
- Professional review by licensed architect/engineer
- Cross-reference with STANDATA interpretations
- Verify against Alberta-specific amendments

## Data Quality Assurance

### Extraction Confidence Levels

| Level | Criteria |
|-------|----------|
| HIGH | Direct numeric value from clear text, verified against table |
| MEDIUM | Value inferred from context or complex sentence structure |
| LOW | Ambiguous source text, requires professional interpretation |

### Verification Status

All extracted requirements are marked with:
- `is_verified: false` - Initial import, pending review
- `verified_by` - Name of reviewing professional
- `verifier_designation` - Professional credentials
- `verified_date` - Date of verification

## Files and Locations

```
data/codes/
├── nbc_section_9.8_raw.json        # Raw PDF extraction
├── nbc_section_9.8_structured.json # Structured requirements
└── [future sections...]

app/scripts/
├── import_nbc_codes.py             # Database import script
└── extract_nbc_section.py          # PDF extraction helper

docs/
└── code_extraction_methodology.md  # This document
```

## Extraction for Other Code Sections

To extract additional NBC sections:

1. **Locate Section in PDF:**
```python
import pdfplumber

with pdfplumber.open("data/nbc/NBC-AE-2023.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if "Section 9.10" in text:  # Target section
            print(f"Found on page {i + 1}")
```

2. **Extract Raw Text:**
```python
# Use extract_section() function from step 2
raw_data = extract_section("path/to/pdf", start_page, end_page)
with open("nbc_section_X.X_raw.json", "w") as f:
    json.dump(raw_data, f, indent=2)
```

3. **Create Structured JSON:**
- Review raw text
- Identify articles and requirements
- Extract dimensional values
- Create structured JSON following schema above

4. **Import to Database:**
```bash
python import_nbc_codes.py --section X.X
```

## Research Findings: No Existing Structured Data

We conducted extensive searches for existing machine-readable building code data:

**Searched:**
- GitHub repositories for NBC parsers
- NRC official data portals
- Alberta Open Data
- ICC Code Connect API (US codes only)
- Commercial building code APIs

**Findings:**
- **No public JSON/XML/API** for NBC exists
- ICC Code Connect provides US codes only
- Australian CODE-ACCORD project provides methodology but not Canadian data
- We are creating the first structured database of NBC(AE) 2023

## Future Improvements

1. **VLM Integration:** Consider using vision-language models (e.g., Qwen-VL) for table extraction
2. **OCR Enhancement:** For older scanned code documents
3. **Automated Validation:** Cross-reference with STANDATA bulletins
4. **Version Tracking:** Handle code amendments and updates
5. **Professional Review Workflow:** Build verification UI for licensed professionals

## Legal Considerations

- Building codes are copyrighted documents
- Extracted data is for compliance checking, not republication
- Always cite source document and edition
- Professional verification required before production use
- Users must validate against official published codes

---

**Last Updated:** 2026-01-09
**Extraction Model:** Claude Opus 4.5 (claude-opus-4-5-20251101)
**Verified By:** Pending professional review
