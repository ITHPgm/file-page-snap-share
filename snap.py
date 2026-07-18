import streamlit as st
import fitz  # PyMuPDF
import io
import zipfile
from PIL import Image
import urllib.parse
import base64

# Set up the Streamlit page configuration
st.set_page_config(
    page_title="Page Snap & Share",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_premium_css():
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
    /* 3D Button styling */
    div.stButton > button {
        background: linear-gradient(145deg, #4f46e5, #7c3aed);
        color: white;
        border: none;
        border-radius: 12px;
        box-shadow: 0 6px 10px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.12);
        transition: all 0.2s ease;
        font-weight: 600;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }
    
    /* Share Buttons CSS */
    .share-container { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
    .share-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 12px 20px;
        border-radius: 12px;
        color: white !important;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.2s;
    }
    .wa-btn { background: #25D366; }
    .tg-btn { background: #0088cc; }
    .native-btn { background: #6366f1; border: 2px solid #4f46e5; }
    .share-btn:hover { transform: scale(1.02); opacity: 0.9; }
    </style>
    """, unsafe_allow_html=True)

apply_premium_css()

def process_pdf(file_bytes):
    images = []
    try:
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            zoom_matrix = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=zoom_matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return images

def process_image(file_bytes):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        return [img]
    except Exception as e:
        st.error(f"Error reading Image: {e}")
        return []

def create_zip_of_images(images_dict, prefix="page"):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for idx, img in images_dict.items():
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            zip_file.writestr(f"{prefix}_{idx + 1}.png", img_buffer.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

# Streamlit State Initialization
if 'processed_images' not in st.session_state: st.session_state.processed_images = []
if 'selected_pages' not in st.session_state: st.session_state.selected_pages = {}
if 'file_name' not in st.session_state: st.session_state.file_name = ""

st.markdown("<h1><i class='fas fa-camera'></i> Page Snap & Share</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h2><i class='fas fa-folder-open'></i> Upload File</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None and st.session_state.file_name != uploaded_file.name:
        st.session_state.file_name = uploaded_file.name
        st.session_state.selected_pages = {}
        with st.spinner('Generating previews...'):
            file_bytes = uploaded_file.read()
            st.session_state.processed_images = process_pdf(file_bytes) if uploaded_file.name.lower().endswith('pdf') else process_image(file_bytes)

if st.session_state.processed_images:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Select All"):
            for i in range(len(st.session_state.processed_images)):
                st.session_state[f"check_{i}"] = True
                st.session_state.selected_pages[i] = True
            st.rerun()
    with col_b:
        if st.button("Deselect All"):
            for i in range(len(st.session_state.processed_images)):
                st.session_state[f"check_{i}"] = False
            st.session_state.selected_pages = {}
            st.rerun()

    cols = st.columns(3)
    for idx, img in enumerate(st.session_state.processed_images):
        with cols[idx % 3]:
            st.image(img, use_container_width=True)
            if st.checkbox(f"Page {idx + 1}", key=f"check_{idx}", value=st.session_state.selected_pages.get(idx, False)):
                st.session_state.selected_pages[idx] = True
            elif idx in st.session_state.selected_pages:
                del st.session_state.selected_pages[idx]

    st.markdown("---")
    st.markdown("<h2><i class='fas fa-bolt'></i> Actions</h2>", unsafe_allow_html=True)
    
    selected_images = {idx: st.session_state.processed_images[idx] for idx in st.session_state.selected_pages}
    
    if selected_images:
        tab1, tab2 = st.tabs(["🚀 Bulk Actions", "⬇️ Individual Downloads"])
        
        with tab1:
            # Download Zip
            sel_zip = create_zip_of_images(selected_images, "selected")
            st.download_button("📦 Download All Selected (ZIP)", data=sel_zip, file_name="selected_pages.zip", mime="application/zip")
            
            # Share Links
            st.markdown("<h3><i class='fas fa-share-alt'></i> Share via Apps</h3>", unsafe_allow_html=True)
            msg = urllib.parse.quote(f"Check out these {len(selected_images)} pages from {st.session_state.file_name}")
            st.markdown(f"""
            <div class="share-container">
                <a href="https://api.whatsapp.com/send?text={msg}" class="share-btn wa-btn"><i class="fab fa-whatsapp"></i>&nbsp; WhatsApp</a>
                <a href="https://t.me/share/url?url=&text={msg}" class="share-btn tg-btn"><i class="fab fa-telegram"></i>&nbsp; Telegram</a>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💡 To attach images to social media, please download the ZIP file first or use your device's file picker in the apps.")

        with tab2:
            st.markdown("Click any button below to download the specific page as an image file.")
            for idx, img in selected_images.items():
                img_buffer = io.BytesIO()
                img.save(img_buffer, format="PNG")
                st.download_button(
                    label=f"Download Page {idx + 1} Image",
                    data=img_buffer.getvalue(),
                    file_name=f"page_{idx + 1}.png",
                    mime="image/png"
                )
    else:
        st.warning("Select pages to see action options.")
else:
    st.info("👈 Upload a file in the sidebar to begin.")
