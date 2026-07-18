# 📸 Page Snap & Share

Page Snap & Share is a high-performance web utility built with [Streamlit](https://streamlit.io/) that allows you to transform multi-page PDF documents and images into high-quality visual snapshots. 

Whether you need to extract specific pages for a presentation, generate thumbnails for a project, or quickly share document snippets via social media, this tool handles the heavy lifting locally and securely.

## ✨ Key Features
- **PDF & Image Processing:** High-quality rendering of PDF pages using PyMuPDF (`fitz`).
- **Smart Selection:** Easily select specific pages or use "Select All" for bulk operations.
- **Bulk & Individual Downloads:** Download all selected pages as a `.zip` archive or save individual pages as high-resolution PNGs.
- **Native Social Sharing:** Trigger native OS share sheets to send files directly to WhatsApp, Telegram, or Email.
- **Modern UI:** Built with custom CSS, Font Awesome icons, and a premium 3D button aesthetic.

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- `pip` (Python package installer)

### Installation

1. **Clone the repository:**
   
```
git clone https://github.com/ITHPgm/file-page-snap-share.git
```
2. **Change the directory**
```
cd file-page-snap-share

```
3. **Create an environment**

```
python -m venv venv
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate

   ```
4. **Install streamlit**

```
pip install streamlit pymupdf Pillow
```
5. **Run the snap.py**
```
streamlit run snap.py
```
The application will open in your default web browser (usually at http://localhost:8501).

🛠 Built With
Streamlit - The framework for the web interface.

PyMuPDF - For accurate PDF rendering.

Pillow - For image manipulation and processing.

Font Awesome - For professional UI icons.

📄 License
This project is open-source and available for use under the MIT License.

