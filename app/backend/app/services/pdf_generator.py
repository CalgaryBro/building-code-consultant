"""
PDF Generation Service for Calgary Building Code Expert System.

This service generates downloadable PDF checklists and reports including:
- Development Permit (DP) checklists
- Building Permit (BP) checklists
- Document checklists
- Compliance reports

Uses ReportLab for PDF generation with professional layout.
"""
import io
from datetime import datetime
from typing import Optional, List, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Line, Rect
from reportlab.graphics.charts.legends import Legend

from ..config import get_settings

settings = get_settings()


# --- Color Scheme ---
BRAND_COLOR = colors.HexColor("#1E3A5F")  # Calgary blue
ACCENT_COLOR = colors.HexColor("#E31837")  # Calgary red
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MEDIUM_GRAY = colors.HexColor("#CCCCCC")
DARK_GRAY = colors.HexColor("#333333")
SUCCESS_COLOR = colors.HexColor("#28A745")
WARNING_COLOR = colors.HexColor("#FFC107")
DANGER_COLOR = colors.HexColor("#DC3545")


# --- Custom Styles ---
def get_custom_styles():
    """Create custom paragraph styles for the PDF documents."""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=12,
        textColor=BRAND_COLOR,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    ))

    # Subtitle style
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        textColor=DARK_GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER
    ))

    # Section header style
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=BRAND_COLOR,
        fontName='Helvetica-Bold',
        borderPadding=(5, 5, 5, 5)
    ))

    # Subsection header style
    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=DARK_GRAY,
        fontName='Helvetica-Bold'
    ))

    # Checklist item style
    styles.add(ParagraphStyle(
        name='ChecklistItem',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=4,
        spaceAfter=4,
        leftIndent=25,
        fontName='Helvetica'
    ))

    # Info text style
    styles.add(ParagraphStyle(
        name='InfoText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=DARK_GRAY,
        fontName='Helvetica'
    ))

    # Footer style
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=MEDIUM_GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER
    ))

    return styles


def _create_header(project_data: Dict[str, Any], permit_type: str, styles) -> List:
    """Create the document header section."""
    elements = []

    # Title
    title = f"{permit_type} Checklist"
    elements.append(Paragraph(title, styles['CustomTitle']))

    # System name
    elements.append(Paragraph(
        "Calgary Building Code Expert System",
        styles['CustomSubtitle']
    ))

    elements.append(Spacer(1, 20))

    # Project info table
    project_info = [
        ["Project:", project_data.get('project_name', 'N/A')],
        ["Address:", project_data.get('address', 'N/A')],
        ["Application #:", project_data.get('application_number', 'N/A')],
        ["Generated:", datetime.now().strftime("%B %d, %Y at %I:%M %p")],
    ]

    if project_data.get('parcel_id'):
        project_info.append(["Parcel ID:", project_data['parcel_id']])

    if project_data.get('project_type'):
        project_info.append(["Project Type:", project_data['project_type'].replace('_', ' ').title()])

    info_table = Table(project_info, colWidths=[1.5*inch, 5*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BRAND_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Divider line
    elements.append(_create_divider())
    elements.append(Spacer(1, 15))

    return elements


def _create_divider() -> Drawing:
    """Create a horizontal divider line."""
    d = Drawing(500, 3)
    d.add(Line(0, 1.5, 500, 1.5, strokeColor=MEDIUM_GRAY, strokeWidth=1))
    return d


def _create_checkbox_item(text: str, checked: bool = False, styles=None) -> Paragraph:
    """Create a checklist item with checkbox symbol."""
    checkbox = "[X]" if checked else "[  ]"
    return Paragraph(f"{checkbox}  {text}", styles['ChecklistItem'])


def _create_checklist_table(items: List[Dict[str, Any]], styles) -> Table:
    """Create a formatted checklist table with checkboxes."""
    table_data = []

    for item in items:
        checkbox = "[  ]"  # Empty checkbox
        text = item.get('text', '')
        notes = item.get('notes', '')
        required = item.get('required', True)

        # Format the row
        if notes:
            text_cell = Paragraph(f"<b>{text}</b><br/><font size='8' color='gray'>{notes}</font>", styles['Normal'])
        else:
            text_cell = Paragraph(text, styles['Normal'])

        required_text = "Required" if required else "Optional"
        required_color = DANGER_COLOR if required else MEDIUM_GRAY

        table_data.append([checkbox, text_cell, required_text])

    table = Table(table_data, colWidths=[0.4*inch, 4.6*inch, 1*inch])
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, -1), 12),
        ('FONT', (2, 0), (2, -1), 'Helvetica'),
        ('FONTSIZE', (2, 0), (2, -1), 8),
        ('TEXTCOLOR', (2, 0), (2, -1), MEDIUM_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, LIGHT_GRAY),
    ]))

    return table


def _create_footer_content() -> str:
    """Create footer content text."""
    return (
        "Calgary Building Code Expert System | "
        f"Generated {datetime.now().strftime('%Y-%m-%d')} | "
        "For informational purposes only. Always verify with City of Calgary."
    )


def _add_page_footer(canvas, doc):
    """Add footer to each page."""
    canvas.saveState()

    # Footer text
    footer_text = _create_footer_content()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MEDIUM_GRAY)
    canvas.drawCentredString(letter[0] / 2, 0.5 * inch, footer_text)

    # Page number
    page_num = canvas.getPageNumber()
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {page_num}")

    canvas.restoreState()


# --- DP Document Requirements ---
DP_REQUIRED_DOCUMENTS = [
    {
        "text": "Completed Development Permit Application Form",
        "notes": "Include all required signatures",
        "required": True
    },
    {
        "text": "Certificate of Title (less than 30 days old)",
        "notes": "Must show current ownership",
        "required": True
    },
    {
        "text": "Real Property Report / Survey",
        "notes": "Showing property boundaries and existing structures",
        "required": True
    },
    {
        "text": "Site Plan",
        "notes": "Show lot dimensions, setbacks, building footprint, parking, landscaping",
        "required": True
    },
    {
        "text": "Floor Plans",
        "notes": "All levels including basement. Show room labels and dimensions",
        "required": True
    },
    {
        "text": "Building Elevations",
        "notes": "All sides of building showing materials and heights",
        "required": True
    },
    {
        "text": "Roof Plan",
        "notes": "Show slopes, drainage, mechanical equipment screening",
        "required": False
    },
    {
        "text": "Landscape Plan",
        "notes": "Required for multi-residential and commercial projects",
        "required": False
    },
    {
        "text": "Parking Layout",
        "notes": "Show stall dimensions, drive aisles, accessible stalls",
        "required": False
    },
    {
        "text": "Signage Details",
        "notes": "If signage is proposed",
        "required": False
    },
    {
        "text": "Traffic Impact Assessment",
        "notes": "May be required for large developments",
        "required": False
    },
    {
        "text": "Environmental Site Assessment",
        "notes": "If previous commercial/industrial use",
        "required": False
    },
]

# --- BP Document Requirements ---
BP_REQUIRED_DOCUMENTS = [
    {
        "text": "Approved Development Permit (if applicable)",
        "notes": "Include DP approval letter and conditions",
        "required": True
    },
    {
        "text": "Completed Building Permit Application Form",
        "notes": "Include all required signatures",
        "required": True
    },
    {
        "text": "Site Plan",
        "notes": "Show lot dimensions, setbacks, building footprint, underground utilities",
        "required": True
    },
    {
        "text": "Architectural Drawings",
        "notes": "Floor plans, elevations, sections with dimensions and notes",
        "required": True
    },
    {
        "text": "Structural Drawings",
        "notes": "Foundation plan, framing plans, structural details",
        "required": True
    },
    {
        "text": "Structural Engineer's Seal",
        "notes": "Required for Part 3 buildings and engineered components",
        "required": False
    },
    {
        "text": "Mechanical Drawings (HVAC)",
        "notes": "Required for commercial and Part 3 buildings",
        "required": False
    },
    {
        "text": "Plumbing Drawings",
        "notes": "Include riser diagrams for multi-storey buildings",
        "required": False
    },
    {
        "text": "Electrical Drawings",
        "notes": "Single line diagram, panel schedules, load calculations",
        "required": False
    },
    {
        "text": "Fire Safety Plan",
        "notes": "Required for Part 3 buildings",
        "required": False
    },
    {
        "text": "Energy Compliance Documentation",
        "notes": "NBC 9.36 or NECB compliance path documentation",
        "required": True
    },
    {
        "text": "Geotechnical Report",
        "notes": "May be required based on site conditions",
        "required": False
    },
    {
        "text": "Truss Engineering",
        "notes": "Sealed truss drawings and layouts",
        "required": False
    },
    {
        "text": "Sprinkler System Drawings",
        "notes": "If sprinklered building",
        "required": False
    },
]


def generate_dp_checklist(project_data: Dict[str, Any]) -> bytes:
    """
    Generate a Development Permit checklist PDF.

    Args:
        project_data: Dictionary containing project information including:
            - project_name: Name of the project
            - address: Project address
            - application_number: DP application number
            - parcel_id: Parcel ID (optional)
            - project_type: Type of project
            - zone: Zoning district (optional)
            - proposed_use: Proposed land use (optional)
            - relaxations: List of requested relaxations (optional)

    Returns:
        PDF file as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )

    styles = get_custom_styles()
    elements = []

    # Header
    elements.extend(_create_header(project_data, "Development Permit", styles))

    # Required Documents Section
    elements.append(Paragraph("Required Documents", styles['SectionHeader']))
    elements.append(Paragraph(
        "The following documents are typically required for a Development Permit application. "
        "Check each box as you prepare your submission.",
        styles['InfoText']
    ))
    elements.append(Spacer(1, 10))
    elements.append(_create_checklist_table(DP_REQUIRED_DOCUMENTS, styles))

    elements.append(Spacer(1, 20))

    # Zoning Information Section
    elements.append(Paragraph("Zoning Considerations", styles['SectionHeader']))

    zone_info = project_data.get('zone', 'Not specified')
    proposed_use = project_data.get('proposed_use', 'Not specified')

    zone_items = [
        f"Current Zoning District: {zone_info}",
        f"Proposed Use: {proposed_use}",
    ]

    if project_data.get('relaxations'):
        zone_items.append("Relaxations Requested:")
        for relaxation in project_data['relaxations']:
            zone_items.append(f"  - {relaxation}")

    for item in zone_items:
        elements.append(Paragraph(f"  {item}", styles['Normal']))

    elements.append(Spacer(1, 20))

    # Key Requirements Section
    elements.append(Paragraph("Key Requirements to Verify", styles['SectionHeader']))

    key_requirements = [
        {"text": "Setbacks comply with Land Use Bylaw requirements", "required": True},
        {"text": "Building height within maximum allowed", "required": True},
        {"text": "Site coverage does not exceed maximum", "required": True},
        {"text": "Parking provided meets minimum requirements", "required": True},
        {"text": "Landscaping meets minimum requirements", "required": False},
        {"text": "Signage complies with regulations", "required": False},
        {"text": "Accessibility requirements addressed", "required": True},
    ]

    elements.append(_create_checklist_table(key_requirements, styles))

    elements.append(Spacer(1, 20))

    # Next Steps Section
    elements.append(Paragraph("Next Steps", styles['SectionHeader']))

    next_steps = [
        "1. Complete all required documents listed above",
        "2. Ensure drawings are to scale and properly dimensioned",
        "3. Submit application online through myCity portal or in person",
        "4. Pay applicable application fees",
        "5. Respond promptly to any information requests from the City",
        "6. Once approved, obtain Building Permit before construction begins",
    ]

    for step in next_steps:
        elements.append(Paragraph(step, styles['Normal']))
        elements.append(Spacer(1, 5))

    elements.append(Spacer(1, 20))

    # Contact Information
    elements.append(Paragraph("City of Calgary Contact Information", styles['SectionHeader']))
    elements.append(Paragraph(
        "<b>Planning Services Centre</b><br/>"
        "3rd Floor, Municipal Building<br/>"
        "800 Macleod Trail SE, Calgary, AB T2G 2M3<br/>"
        "Phone: 311 (within Calgary) or 403-268-2489<br/>"
        "Website: calgary.ca/development",
        styles['Normal']
    ))

    # Build the PDF
    doc.build(elements, onFirstPage=_add_page_footer, onLaterPages=_add_page_footer)

    buffer.seek(0)
    return buffer.getvalue()


def generate_bp_checklist(project_data: Dict[str, Any]) -> bytes:
    """
    Generate a Building Permit checklist PDF.

    Args:
        project_data: Dictionary containing project information including:
            - project_name: Name of the project
            - address: Project address
            - application_number: BP application number
            - classification: Building classification (PART_9 or PART_3)
            - occupancy_group: Occupancy classification
            - building_area_sqm: Building area
            - building_height_storeys: Number of storeys

    Returns:
        PDF file as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )

    styles = get_custom_styles()
    elements = []

    # Header
    elements.extend(_create_header(project_data, "Building Permit", styles))

    # Building Classification Section
    elements.append(Paragraph("Building Classification", styles['SectionHeader']))

    classification = project_data.get('classification', 'Not specified')
    occupancy = project_data.get('occupancy_group', 'Not specified')
    area = project_data.get('building_area_sqm', 'Not specified')
    storeys = project_data.get('building_height_storeys', 'Not specified')

    classification_data = [
        ["Building Classification:", classification],
        ["Occupancy Group:", occupancy],
        ["Building Area:", f"{area} m2" if isinstance(area, (int, float)) else area],
        ["Number of Storeys:", str(storeys)],
    ]

    class_table = Table(classification_data, colWidths=[2*inch, 4*inch])
    class_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), BRAND_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, MEDIUM_GRAY),
    ]))

    elements.append(class_table)
    elements.append(Spacer(1, 20))

    # Required Documents Section
    elements.append(Paragraph("Required Documents", styles['SectionHeader']))

    # Determine which documents are required based on classification
    required_docs = BP_REQUIRED_DOCUMENTS.copy()
    if classification == "PART_3":
        # Mark more documents as required for Part 3 buildings
        for doc in required_docs:
            if any(keyword in doc['text'].lower() for keyword in
                   ['structural engineer', 'mechanical', 'fire safety', 'sprinkler']):
                doc['required'] = True

    elements.append(Paragraph(
        "The following documents are required for your Building Permit application. "
        "Requirements may vary based on building classification and complexity.",
        styles['InfoText']
    ))
    elements.append(Spacer(1, 10))
    elements.append(_create_checklist_table(required_docs, styles))

    elements.append(Spacer(1, 20))

    # Code Compliance Section
    elements.append(Paragraph("Building Code Compliance Checklist", styles['SectionHeader']))

    code_items = [
        {"text": "Occupant load calculations provided", "required": True},
        {"text": "Egress width meets requirements (min. 1100mm for stairs)", "required": True},
        {"text": "Travel distance to exits within limits", "required": True},
        {"text": "Fire separations properly rated and detailed", "required": True},
        {"text": "Spatial separation from property lines verified", "required": True},
        {"text": "Construction type suitable for building size and occupancy", "required": True},
        {"text": "Accessibility requirements addressed (barrier-free path)", "required": True},
        {"text": "Guards and handrails meet requirements", "required": True},
        {"text": "Plumbing fixtures count meets occupant load", "required": True},
        {"text": "Energy efficiency requirements documented", "required": True},
    ]

    elements.append(_create_checklist_table(code_items, styles))

    elements.append(Spacer(1, 20))

    # Inspection Requirements Section
    elements.append(Paragraph("Inspection Requirements", styles['SectionHeader']))
    elements.append(Paragraph(
        "The following inspections are typically required during construction:",
        styles['InfoText']
    ))
    elements.append(Spacer(1, 10))

    inspections = [
        {"text": "Footing Inspection - before concrete pour", "required": True},
        {"text": "Foundation Inspection - before backfill", "required": True},
        {"text": "Framing Inspection - before insulation/drywall", "required": True},
        {"text": "Insulation Inspection - before vapor barrier/drywall", "required": True},
        {"text": "Plumbing Rough-in Inspection", "required": True},
        {"text": "Electrical Rough-in Inspection", "required": True},
        {"text": "HVAC Inspection", "required": False},
        {"text": "Fire Stopping Inspection", "required": False},
        {"text": "Final Inspection - before occupancy", "required": True},
    ]

    elements.append(_create_checklist_table(inspections, styles))

    elements.append(Spacer(1, 20))

    # Contact Information
    elements.append(Paragraph("City of Calgary Contact Information", styles['SectionHeader']))
    elements.append(Paragraph(
        "<b>Building Regulations</b><br/>"
        "4th Floor, Municipal Building<br/>"
        "800 Macleod Trail SE, Calgary, AB T2G 2M3<br/>"
        "Phone: 311 (within Calgary) or 403-268-2489<br/>"
        "Website: calgary.ca/building<br/><br/>"
        "<b>To Schedule Inspections:</b><br/>"
        "Call 311 or use myCity online portal",
        styles['Normal']
    ))

    # Build the PDF
    doc.build(elements, onFirstPage=_add_page_footer, onLaterPages=_add_page_footer)

    buffer.seek(0)
    return buffer.getvalue()


def generate_document_checklist(permit_type: str, project_data: Dict[str, Any]) -> bytes:
    """
    Generate a generic document checklist PDF for the specified permit type.

    Args:
        permit_type: Type of permit (DP, BP, TRADE, etc.)
        project_data: Dictionary containing project information.

    Returns:
        PDF file as bytes.
    """
    if permit_type.upper() in ['DP', 'DEVELOPMENT_PERMIT', 'DEVELOPMENT']:
        return generate_dp_checklist(project_data)
    elif permit_type.upper() in ['BP', 'BUILDING_PERMIT', 'BUILDING']:
        return generate_bp_checklist(project_data)
    else:
        # Generic checklist for other permit types
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        styles = get_custom_styles()
        elements = []

        # Header
        elements.extend(_create_header(project_data, f"{permit_type} Permit", styles))

        # Generic checklist
        elements.append(Paragraph("Document Checklist", styles['SectionHeader']))

        generic_items = [
            {"text": "Completed application form", "required": True},
            {"text": "Proof of ownership or authorization", "required": True},
            {"text": "Site plan or location diagram", "required": True},
            {"text": "Technical drawings/specifications", "required": True},
            {"text": "Supporting documentation", "required": False},
        ]

        elements.append(_create_checklist_table(generic_items, styles))

        # Build the PDF
        doc.build(elements, onFirstPage=_add_page_footer, onLaterPages=_add_page_footer)

        buffer.seek(0)
        return buffer.getvalue()


def generate_compliance_report(
    project_id: str,
    checks: List[Dict[str, Any]],
    project_data: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Generate a compliance check results PDF report.

    Args:
        project_id: ID of the project.
        checks: List of compliance check results, each containing:
            - check_category: Category (zoning, egress, fire, etc.)
            - check_name: Name of the check
            - status: Result (pass, fail, warning, needs_review)
            - required_value: Required value/specification
            - actual_value: Value found in documents
            - code_reference: Applicable code reference
            - message: Additional notes/message
        project_data: Optional project information dictionary.

    Returns:
        PDF file as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )

    styles = get_custom_styles()
    elements = []

    # Prepare project data
    if project_data is None:
        project_data = {}
    project_data['project_id'] = project_id

    # Header
    elements.extend(_create_header(project_data, "Compliance Report", styles))

    # Summary Section
    elements.append(Paragraph("Summary", styles['SectionHeader']))

    # Calculate statistics
    total_checks = len(checks)
    passed = sum(1 for c in checks if c.get('status') == 'pass')
    failed = sum(1 for c in checks if c.get('status') == 'fail')
    warnings = sum(1 for c in checks if c.get('status') == 'warning')
    needs_review = sum(1 for c in checks if c.get('status') == 'needs_review')

    # Determine overall status
    if failed > 0:
        overall_status = "FAIL"
        status_color = DANGER_COLOR
    elif warnings > 0 or needs_review > 0:
        overall_status = "NEEDS ATTENTION"
        status_color = WARNING_COLOR
    else:
        overall_status = "PASS"
        status_color = SUCCESS_COLOR

    # Summary table
    summary_data = [
        ["Total Checks:", str(total_checks)],
        ["Passed:", str(passed)],
        ["Failed:", str(failed)],
        ["Warnings:", str(warnings)],
        ["Needs Review:", str(needs_review)],
        ["Overall Status:", overall_status],
    ]

    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -2), 'Helvetica'),
        ('FONT', (1, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (1, 1), (1, 1), SUCCESS_COLOR),  # Passed
        ('TEXTCOLOR', (1, 2), (1, 2), DANGER_COLOR),   # Failed
        ('TEXTCOLOR', (1, 3), (1, 3), WARNING_COLOR),  # Warnings
        ('TEXTCOLOR', (1, 4), (1, 4), WARNING_COLOR),  # Needs Review
        ('TEXTCOLOR', (1, -1), (1, -1), status_color), # Overall
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, -1), (-1, -1), LIGHT_GRAY),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Group checks by category
    categories = {}
    for check in checks:
        cat = check.get('check_category', 'Other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(check)

    # Detail Sections by Category
    for category, category_checks in sorted(categories.items()):
        elements.append(Paragraph(category.title().replace('_', ' '), styles['SectionHeader']))

        # Create table for checks in this category
        table_data = [["Check", "Required", "Actual", "Status"]]

        for check in category_checks:
            status = check.get('status', 'unknown')

            # Status indicator
            if status == 'pass':
                status_text = "PASS"
                status_style_color = SUCCESS_COLOR
            elif status == 'fail':
                status_text = "FAIL"
                status_style_color = DANGER_COLOR
            elif status == 'warning':
                status_text = "WARN"
                status_style_color = WARNING_COLOR
            else:
                status_text = "REVIEW"
                status_style_color = WARNING_COLOR

            check_name = check.get('check_name', 'Unknown')
            required = check.get('required_value', '-')
            actual = check.get('actual_value', '-')

            # Truncate long values
            if isinstance(required, str) and len(required) > 30:
                required = required[:27] + "..."
            if isinstance(actual, str) and len(actual) > 30:
                actual = actual[:27] + "..."

            table_data.append([check_name, str(required), str(actual), status_text])

        # Create the table
        detail_table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 0.75*inch])
        detail_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            # Data rows
            ('FONT', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, MEDIUM_GRAY),
            ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
        ]))

        # Color-code status column
        for i, row in enumerate(table_data[1:], start=1):
            status = row[-1]
            if status == "PASS":
                detail_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (-1, i), (-1, i), SUCCESS_COLOR),
                    ('FONT', (-1, i), (-1, i), 'Helvetica-Bold'),
                ]))
            elif status == "FAIL":
                detail_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (-1, i), (-1, i), DANGER_COLOR),
                    ('FONT', (-1, i), (-1, i), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor("#FFEEEE")),
                ]))
            elif status == "WARN":
                detail_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (-1, i), (-1, i), WARNING_COLOR),
                ]))

        elements.append(detail_table)
        elements.append(Spacer(1, 15))

    # Failed Items Detail Section
    failed_checks = [c for c in checks if c.get('status') == 'fail']
    if failed_checks:
        elements.append(PageBreak())
        elements.append(Paragraph("Failed Items - Required Actions", styles['SectionHeader']))
        elements.append(Paragraph(
            "The following items require attention before the application can proceed:",
            styles['InfoText']
        ))
        elements.append(Spacer(1, 10))

        for i, check in enumerate(failed_checks, 1):
            check_name = check.get('check_name', 'Unknown')
            message = check.get('message', 'No additional details provided.')
            code_ref = check.get('code_reference', '')
            required = check.get('required_value', '')
            actual = check.get('actual_value', '')

            detail_text = f"<b>{i}. {check_name}</b><br/>"
            if required and actual:
                detail_text += f"Required: {required} | Found: {actual}<br/>"
            if code_ref:
                detail_text += f"<i>Code Reference: {code_ref}</i><br/>"
            detail_text += f"Action Required: {message}"

            elements.append(Paragraph(detail_text, styles['Normal']))
            elements.append(Spacer(1, 10))

    # Recommendations Section
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Recommendations", styles['SectionHeader']))

    if failed > 0:
        elements.append(Paragraph(
            "This project has compliance issues that must be addressed before proceeding. "
            "Please review the failed items above and make the necessary corrections to your drawings "
            "or application documents.",
            styles['Normal']
        ))
    elif warnings > 0 or needs_review > 0:
        elements.append(Paragraph(
            "This project has items that require attention or manual verification. "
            "Please review the warnings and items marked for review to ensure compliance.",
            styles['Normal']
        ))
    else:
        elements.append(Paragraph(
            "All automated compliance checks have passed. "
            "However, this report does not replace official City review. "
            "Some requirements may require manual verification during the permit review process.",
            styles['Normal']
        ))

    elements.append(Spacer(1, 20))

    # Disclaimer
    elements.append(Paragraph("Disclaimer", styles['SubsectionHeader']))
    elements.append(Paragraph(
        "<i>This compliance report is generated by the Calgary Building Code Expert System for "
        "informational purposes only. It does not replace official City of Calgary review and approval. "
        "All building projects must obtain proper permits from the City of Calgary before construction. "
        "Building code requirements are subject to change and interpretation by authorities having jurisdiction.</i>",
        styles['InfoText']
    ))

    # Build the PDF
    doc.build(elements, onFirstPage=_add_page_footer, onLaterPages=_add_page_footer)

    buffer.seek(0)
    return buffer.getvalue()


# --- Service Instance ---
class PDFGeneratorService:
    """
    PDF Generator Service class for generating permit checklists and reports.
    """

    def generate_dp_checklist(self, project_data: Dict[str, Any]) -> bytes:
        """Generate Development Permit checklist PDF."""
        return generate_dp_checklist(project_data)

    def generate_bp_checklist(self, project_data: Dict[str, Any]) -> bytes:
        """Generate Building Permit checklist PDF."""
        return generate_bp_checklist(project_data)

    def generate_document_checklist(
        self,
        permit_type: str,
        project_data: Dict[str, Any]
    ) -> bytes:
        """Generate generic document checklist PDF."""
        return generate_document_checklist(permit_type, project_data)

    def generate_compliance_report(
        self,
        project_id: str,
        checks: List[Dict[str, Any]],
        project_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate compliance report PDF."""
        return generate_compliance_report(project_id, checks, project_data)


# Create singleton instance
pdf_generator = PDFGeneratorService()
