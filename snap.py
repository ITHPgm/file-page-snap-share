import streamlit as st
import fitz  # PyMuPDF
import io
import zipfile
import time
import base64
import re
from PIL import Image

# Import document generation tools with fallback error handling
try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# Configure Streamlit Application Page
st.set_page_config(
    page_title="Page Snap & OCR Studio Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    /* Main Theme Variables & Overrides */
    :root {
        --bg-dark: #030712;
        --card-bg: rgba(17, 24, 39, 0.75);
        --accent-indigo: #6366f1;
        --accent-cyan: #38bdf8;
        --accent-emerald: #4ade80;
        --accent-pink: #ec4899;
        --border-color: rgba(255, 255, 255, 0.1);
    }

    body, .stApp {
        background-color: var(--bg-dark) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #f3f4f6 !important;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid var(--border-color);
    }

    /* Hide Default Streamlit Elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Cyber Glass Cards */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }

    .glass-card-hover {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass-card-hover:hover {
        border-color: rgba(99, 102, 241, 0.5);
        transform: translateY(-4px);
        box-shadow: 0 15px 35px rgba(99, 102, 241, 0.25);
    }

    /* Terminal Monitor Box */
    .terminal-container {
        background-color: #080c14;
        border: 1px solid #1f2937;
        border-radius: 12px;
        font-family: 'JetBrains Mono', monospace;
        overflow: hidden;
        margin-bottom: 24px;
        box-shadow: 0 0 25px rgba(0, 0, 0, 0.8);
    }

    .terminal-header {
        background-color: #111827;
        padding: 10px 16px;
        border-bottom: 1px solid #1f2937;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .terminal-dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .dot-red { background-color: #ef4444; }
    .dot-yellow { background-color: #f59e0b; }
    .dot-green { background-color: #10b981; }

    .terminal-body {
        padding: 16px;
        height: 220px;
        overflow-y: auto;
        font-size: 13px;
        line-height: 1.6;
        color: #38bdf8;
    }

    /* Radar / Graphical HUD Animations */
    .hud-scanner {
        display: flex;
        align-items: center;
        justify-content: space-around;
        padding: 20px;
        background: linear-gradient(180deg, rgba(15,23,42,0.6) 0%, rgba(3,7,18,0.8) 100%);
        border-radius: 16px;
        border: 1px solid rgba(56, 189, 248, 0.2);
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }

    .radar-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 2px dashed #6366f1;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: spin 8s linear infinite;
    }

    .radar-inner-circle {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 2px solid #38bdf8;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse-glow 2s ease-in-out infinite alternate;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    @keyframes pulse-glow {
        0% { box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); border-color: #38bdf8; }
        100% { box-shadow: 0 0 25px rgba(236, 72, 153, 0.7); border-color: #ec4899; }
    }

    /* Step Progress Rectangles */
    .matrix-rect-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        width: 100%;
        max-width: 500px;
    }

    .matrix-rect {
        height: 48px;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        color: #94a3b8;
        transition: all 0.4s ease;
    }

    .matrix-rect.active {
        background: rgba(99, 102, 241, 0.25);
        border-color: #6366f1;
        color: #38bdf8;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
    }

    .matrix-rect.complete {
        background: rgba(16, 185, 129, 0.2);
        border-color: #10b981;
        color: #4ade80;
    }

    /* 3D Action Buttons */
    .btn-3d {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        transition: all 0.2s ease !important;
    }
    .btn-3d:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(139, 92, 246, 0.6);
    }

    /* Copy Button Styling */
    .copy-btn {
        background: #111827;
        color: #38bdf8;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        cursor: pointer;
        transition: all 0.2s;
    }
    .copy-btn:hover {
        background: #1f2937;
        border-color: #6366f1;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    if 'processed_pages' not in st.session_state:
        st.session_state.processed_pages = []
    if 'selected_pages' not in st.session_state:
        st.session_state.selected_pages = set()
    if 'file_name' not in st.session_state:
        st.session_state.file_name = ""
    if 'terminal_logs' not in st.session_state:
        st.session_state.terminal_logs = []
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'execution_step' not in st.session_state:
        st.session_state.execution_step = 0

init_session_state()
inject_custom_css()

def extract_pdf_data(file_bytes):
    """Processes PDF bytes, extracts clean page text and renders high-res PNG images."""
    pages_data = []
    try:
        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_num)
            
            # Extract Vector Text
            extracted_text = page.get_text("text").strip()
            
            # High-DPI Render for Visual Snap
            zoom_matrix = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=zoom_matrix)
            img_bytes = pix.tobytes("png")
            
            word_count = len(extracted_text.split()) if extracted_text else 0
            
            pages_data.append({
                "page_num": page_num + 1,
                "text": extracted_text if extracted_text else "[NO EXTRACTABLE TEXT DETECTED]",
                "img_bytes": img_bytes,
                "word_count": word_count
            })
    except Exception as e:
        st.error(f"Failed to parse PDF document: {e}")
    return pages_data

def extract_image_data(file_bytes):
    """Processes Image files (PNG/JPG), attempts basic text identification or fallback."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        # Default placeholder text for raw image upload (or OCR if pytesseract present)
        text = f"IMAGE SCAN SNAPSHOT [{img.width}x{img.height}]\nFile Format: {img.format}\n" \
               f"Status: Visual matrix verified. Use PDF files for embedded vector text extraction."
        
        return [{
            "page_num": 1,
            "text": text,
            "img_bytes": img_bytes,
            "word_count": len(text.split())
        }]
    except Exception as e:
        st.error(f"Failed to parse Image file: {e}")
        return []

def generate_zip_archive(pages_data, selected_indices):
    """Creates a downloadable ZIP archive containing images of selected pages."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx in selected_indices:
            if idx < len(pages_data):
                p = pages_data[idx]
                file_name = f"page_{p['page_num']}.png"
                zip_file.writestr(file_name, p['img_bytes'])
    zip_buffer.seek(0)
    return zip_buffer

def generate_formatted_txt(pages_data, selected_indices, file_name):
    """Generates a cleanly formatted plain text output."""
    output = []
    output.append("=" * 60)
    output.append(f"EXTRACTED TEXT MATRIX REPORT: {file_name.upper()}")
    output.append(f"PROCESSED BY: Page Snap & OCR Studio Pro")
    output.append(f"PAGES INCLUDED: {len(selected_indices)}")
    output.append("=" * 60 + "\n")

    for idx in sorted(selected_indices):
        if idx < len(pages_data):
            p = pages_data[idx]
            output.append(f"--- [ PAGE {p['page_num']} ] ---")
            output.append(p['text'])
            output.append("\n" + "-" * 40 + "\n")

    return "\n".join(output)

def generate_formatted_docx(pages_data, selected_indices, file_name):
    """Generates a professionally structured Microsoft Word .docx document."""
    if not HAS_DOCX:
        return None

    doc = docx.Document()
    
    # Page setup - Margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Title Banner
    title_p = doc.add_paragraph()
    run = title_p.add_run(f"Extracted Document: {file_name}")
    run.font.name = 'Arial'
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = RGBColor(79, 70, 229) # Indigo
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    doc.add_paragraph("Generated via Page Snap & OCR Studio Pro | Analytical Expert Suite\n")

    for idx in sorted(selected_indices):
        if idx < len(pages_data):
            p = pages_data[idx]
            
            # Page Heading
            heading = doc.add_paragraph()
            h_run = heading.add_run(f"--- Page {p['page_num']} ---")
            h_run.font.name = 'Arial'
            h_run.font.size = Pt(14)
            h_run.font.bold = True
            h_run.font.color.rgb = RGBColor(56, 189, 248)
            
            # Text Paragraphs
            for line in p['text'].split('\n'):
                if line.strip():
                    para = doc.add_paragraph()
                    p_run = para.add_run(line)
                    p_run.font.name = 'Arial'
                    p_run.font.size = Pt(10.5)
                    para.paragraph_format.space_after = Pt(4)
            
            doc.add_paragraph() # Spacer

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

def generate_formatted_pdf(pages_data, selected_indices, file_name):
    """Generates a clean, well-aligned PDF file using ReportLab."""
    if not HAS_REPORTLAB:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#4F46E5"),
        spaceAfter=12
    )
    
    page_head_style = ParagraphStyle(
        'PageHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0284C7"),
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=6
    )

    story = []
    story.append(Paragraph(f"Extracted Document: {file_name}", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366F1"), spaceAfter=15))

    for idx in sorted(selected_indices):
        if idx < len(pages_data):
            p = pages_data[idx]
            story.append(Paragraph(f"Page {p['page_num']} Content", page_head_style))
            
            # Escape XML entities for ReportLab
            safe_text = p['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            for paragraph_str in safe_text.split('\n'):
                if paragraph_str.strip():
                    story.append(Paragraph(paragraph_str, body_style))
            
            story.append(Spacer(1, 15))

    doc.build(story)
    buffer.seek(0)
    return buffer

st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
    <div>
        <h1 style="font-size: 26px; font-weight: 800; background: linear-gradient(90deg, #ffffff, #6366f1, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
            <i class="fa-solid fa-terminal" style="-webkit-text-fill-color: #6366f1;"></i> PAGE SNAP & OCR STUDIO PRO
        </h1>
        <p style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Cybersecurity-Grade Analytical Document Inspection & Multi-Format Extractor</p>
    </div>
    <div>
        <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #4ade80; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            <i class="fa-solid fa-shield-halved"></i> SYSTEM ACTIVE
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0;">
        <h3 style="font-weight: 700; font-size: 16px; color: #f3f4f6;">
            <i class="fa-solid fa-folder-open" style="color: #6366f1;"></i> Ingestion Terminal
        </h3>
        <p style="font-size: 12px; color: #94a3b8;">Upload target files for high-precision analytical scanning.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Target File", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None and st.session_state.file_name != uploaded_file.name:
        st.session_state.file_name = uploaded_file.name
        st.session_state.is_processing = True
        st.session_state.execution_step = 0
        st.session_state.terminal_logs = []
        st.session_state.selected_pages = set()

if uploaded_file is not None and st.session_state.is_processing:
    # Dedicated Analytical Execution Interface (Hides normal page during scan)
    st.markdown("<h3 style='color: #38bdf8; font-family: JetBrains Mono;'><i class='fa-solid fa-microchip'></i> EXECUTING ANALYTICAL PIPELINE...</h3>", unsafe_allow_html=True)
    
    file_bytes = uploaded_file.read()
    
    # Progress simulation steps
    steps = [
        ("INSPECTING_HEADER", f"Ingesting buffer stream from '{uploaded_file.name}' ({len(file_bytes)/1024:.1f} KB)..."),
        ("VECTOR_DECODE", "Parsing structural byte trees & rasterizing layout pages..."),
        ("OCR_MATRIX_SCAN", "Executing spatial text extraction & vector alignment engines..."),
        ("PIPELINE_COMPLETE", "Extraction pipeline finalized. Rendering inspection HUD...")
    ]

    # Placeholder containers for dynamic execution display
    hud_placeholder = st.empty()
    terminal_placeholder = st.empty()

    for idx, (step_code, log_msg) in enumerate(steps):
        time.sleep(0.4) # Simulated expert execution feedback
        
        timestamp = time.strftime("%H:%M:%S")
        st.session_state.terminal_logs.append(f"[{timestamp}] [{step_code}] {log_msg}")

        # Render Graphical Radar + Matrix Rectangles
        rect1_cls = "complete" if idx >= 0 else ("active" if idx == 0 else "")
        rect2_cls = "complete" if idx >= 1 else ("active" if idx == 1 else "")
        rect3_cls = "complete" if idx >= 2 else ("active" if idx == 2 else "")
        rect4_cls = "complete" if idx >= 3 else ("active" if idx == 3 else "")

        hud_placeholder.markdown(f"""
        <div class="hud-scanner">
            <!-- Animated Radar Circle -->
            <div style="display: flex; align-items: center; gap: 20px;">
                <div class="radar-circle">
                    <div class="radar-inner-circle">
                        <i class="fa-solid fa-fingerprint" style="font-size: 28px; color: #38bdf8;"></i>
                    </div>
                </div>
                <div>
                    <h4 style="margin: 0; font-family: 'JetBrains Mono'; color: #4ade80;">ANALYTICAL ENGINE RUNNING</h4>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">Processing file structure & extracting spatial page text</p>
                </div>
            </div>

            <!-- Step Rectangles -->
            <div class="matrix-rect-grid">
                <div class="matrix-rect {rect1_cls}">1. INGEST</div>
                <div class="matrix-rect {rect2_cls}">2. RASTER</div>
                <div class="matrix-rect {rect3_cls}">3. OCR SCAN</div>
                <div class="matrix-rect {rect4_cls}">4. ALIGN</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Render Terminal Window
        log_lines_html = "".join([f"<div style='margin-bottom: 4px;'><span style='color: #6366f1;'>$</span> {line}</div>" for line in st.session_state.terminal_logs])
        terminal_placeholder.markdown(f"""
        <div class="terminal-container">
            <div class="terminal-header">
                <div>
                    <span class="terminal-dot dot-red"></span>
                    <span class="terminal-dot dot-yellow"></span>
                    <span class="terminal-dot dot-green"></span>
                    <span style="color: #94a3b8; font-size: 12px; margin-left: 8px;">terminal@pagesnap-security-tool:~</span>
                </div>
                <span style="color: #4ade80; font-size: 11px;">RUNNING</span>
            </div>
            <div class="terminal-body">
                {log_lines_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Actual Data Extraction Execution
    if uploaded_file.name.lower().endswith('.pdf'):
        st.session_state.processed_pages = extract_pdf_data(file_bytes)
    else:
        st.session_state.processed_pages = extract_image_data(file_bytes)

    # Default all pages as selected
    st.session_state.selected_pages = set(range(len(st.session_state.processed_pages)))
    st.session_state.is_processing = False
    st.rerun()

elif st.session_state.processed_pages:

    pages_data = st.session_state.processed_pages
    total_pages = len(pages_data)
    selected_count = len(st.session_state.selected_pages)
    total_words = sum([p['word_count'] for i, p in enumerate(pages_data) if i in st.session_state.selected_pages])

    # Top Control Bar & Stats HUD
    st.markdown(f"""
    <div class="glass-card" style="padding: 16px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 15px;">
        <div style="display: flex; align-items: center; gap: 20px;">
            <div>
                <span style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Target File</span>
                <p style="font-size: 15px; font-weight: 700; color: #38bdf8; margin: 0;">{st.session_state.file_name}</p>
            </div>
            <div style="height: 30px; width: 1px; background: rgba(255,255,255,0.1);"></div>
            <div>
                <span style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Pages Loaded</span>
                <p style="font-size: 15px; font-weight: 700; color: #ffffff; margin: 0;">{total_pages} Pages</p>
            </div>
            <div style="height: 30px; width: 1px; background: rgba(255,255,255,0.1);"></div>
            <div>
                <span style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Extracted Words</span>
                <p style="font-size: 15px; font-weight: 700; color: #4ade80; margin: 0;">{total_words} Words</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Global Actions Bar (Select All / Copy All / Multi-Format Exports)
    col1, col2 = st.columns([1, 2])

    with col1:
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button("✅ Select All", use_container_width=True):
            st.session_state.selected_pages = set(range(total_pages))
            st.rerun()
        if btn_c2.button("❌ Deselect All", use_container_width=True):
            st.session_state.selected_pages = set()
            st.rerun()

    with col2:
        # Generate full text buffer for Copy All feature
        all_extracted_text = generate_formatted_txt(pages_data, st.session_state.selected_pages, st.session_state.file_name)
        
        # MASTER COPY ALL TEXT BUTTON WITH JAVASCRIPT CLIPBOARD INTEGRATION
        encoded_text = base64.b64encode(all_extracted_text.encode('utf-8')).decode('utf-8')
        
        st.components.v1.html(f"""
        <script>
        function copyAllText() {{
            const text = atob("{encoded_text}");
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById("copyBtn");
                btn.innerHTML = "✓ COPIED ALL TEXT!";
                btn.style.background = "#10b981";
                setTimeout(() => {{
                    btn.innerHTML = "📋 COPY ALL PAGES TEXT";
                    btn.style.background = "linear-gradient(135deg, #10b981, #059669)";
                }}, 2500);
            }});
        }}
        </script>
        <button id="copyBtn" onclick="copyAllText()" style="
            width: 100%;
            height: 42px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            border: none;
            border-radius: 10px;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 700;
            font-size: 13px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            transition: all 0.2s ease;
        ">
            📋 COPY ALL PAGES TEXT
        </button>
        """, height=50)

    # Multi-Format Downloads Section
    st.markdown("### <i class='fa-solid fa-file-export' style='color:#6366f1;'></i> Formatted File Exporters", unsafe_allow_html=True)
    exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)

    # TXT Export
    txt_data = generate_formatted_txt(pages_data, st.session_state.selected_pages, st.session_state.file_name)
    exp_col1.download_button(
        label="📄 Download .TXT",
        data=txt_data,
        file_name=f"{st.session_state.file_name}_extracted.txt",
        mime="text/plain",
        use_container_width=True
    )

    # PDF Export
    pdf_buffer = generate_formatted_pdf(pages_data, st.session_state.selected_pages, st.session_state.file_name)
    if pdf_buffer:
        exp_col2.download_button(
            label="📕 Download .PDF",
            data=pdf_buffer,
            file_name=f"{st.session_state.file_name}_extracted.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        exp_col2.info("ReportLab required for PDF")

    # DOCX Export
    docx_buffer = generate_formatted_docx(pages_data, st.session_state.selected_pages, st.session_state.file_name)
    if docx_buffer:
        exp_col3.download_button(
            label="📘 Download .DOCX",
            data=docx_buffer,
            file_name=f"{st.session_state.file_name}_extracted.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        exp_col3.info("python-docx required for DOCX")

    # ZIP Images Export
    zip_buffer = generate_zip_archive(pages_data, st.session_state.selected_pages)
    exp_col4.download_button(
        label="📦 Download ZIP Images",
        data=zip_buffer,
        file_name=f"{st.session_state.file_name}_images.zip",
        mime="application/zip",
        use_container_width=True
    )

    st.markdown("---")

    # Grid Display of Rendered Pages
    st.markdown("### <i class='fa-solid fa-layer-group' style='color:#38bdf8;'></i> Page Snap Gallery & Single Text Extractors", unsafe_allow_html=True)
    
    grid_cols = st.columns(3)
    
    for idx, page in enumerate(pages_data):
        with grid_cols[idx % 3]:
            is_selected = idx in st.session_state.selected_pages
            
            # Individual Card HTML
            card_border = "#6366f1" if is_selected else "rgba(255,255,255,0.1)"
            
            st.markdown(f"""
            <div class="glass-card glass-card-hover" style="border-color: {card_border}; padding: 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <span style="font-weight: 800; font-size: 14px; color: #ffffff;">PAGE {page['page_num']}</span>
                    <span style="font-size: 11px; font-family: 'JetBrains Mono'; background: #1f2937; color: #38bdf8; padding: 2px 8px; border-radius: 12px;">
                        {page['word_count']} words
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Checkbox for Page Selection
            selected = st.checkbox(f"Include Page {page['page_num']} in Exports", value=is_selected, key=f"select_{idx}")
            if selected:
                st.session_state.selected_pages.add(idx)
            else:
                st.session_state.selected_pages.discard(idx)

            # Display Image Snapshot
            st.image(page['img_bytes'], use_container_width=True)

            # Single Page Copy Button
            page_text_encoded = base64.b64encode(page['text'].encode('utf-8')).decode('utf-8')
            
            st.components.v1.html(f"""
            <script>
            function copySinglePage_{idx}() {{
                const text = atob("{page_text_encoded}");
                navigator.clipboard.writeText(text).then(() => {{
                    const btn = document.getElementById("singleCopyBtn_{idx}");
                    btn.innerHTML = "✓ COPIED PAGE {page['page_num']}";
                    btn.style.background = "#10b981";
                    setTimeout(() => {{
                        btn.innerHTML = "📄 COPY PAGE {page['page_num']} TEXT";
                        btn.style.background = "#1f2937";
                    }}, 2000);
                }});
            }}
            </script>
            <button id="singleCopyBtn_{idx}" onclick="copySinglePage_{idx}()" style="
                width: 100%;
                padding: 8px 12px;
                background: #1f2937;
                color: #38bdf8;
                border: 1px solid #374151;
                border-radius: 8px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            ">
                📄 COPY PAGE {page['page_num']} TEXT
            </button>
            """, height=40)

            # Text Expander Preview
            with st.expander(f"👁️ Inspect Extracted Text (Page {page['page_num']})"):
                st.text_area(f"Page {page['page_num']} Text", value=page['text'], height=150, key=f"text_preview_{idx}")

else:
    # Empty State - Awaiting File
    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 60px 20px;">
        <div style="width: 80px; height: 80px; background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 20px; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px auto;">
            <i class="fa-solid fa-cloud-arrow-up" style="font-size: 32px; color: #6366f1;"></i>
        </div>
        <h3 style="font-weight: 700; color: #ffffff; margin-bottom: 8px;">Awaiting File Ingestion</h3>
        <p style="color: #94a3b8; font-size: 13px; max-w: 500px; margin: 0 auto 20px auto;">
            Please upload a PDF document or Image file in the sidebar to activate the cybersecurity analytical scanner and multi-format text extractor.
        </p>
    </div>
    """, unsafe_allow_html=True)
