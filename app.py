import streamlit as st
import streamlit.components.v1 as components
import ocrmypdf
import tempfile
import os
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PDF OCR Converter — Rakshit Dwaram",
    page_icon="🔍",
    layout="centered",
)

# ── Google Analytics 4 ───────────────────────────────────────────────────────
GA_MEASUREMENT_ID = "G-F92P8BWS9F"

components.html(f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}', {{
    page_title: 'PDF OCR Converter',
    page_location: window.location.href,
  }});
</script>
<script>
  (function() {{
    var s = window.parent.document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}';
    window.parent.document.head.appendChild(s);
    window.parent.dataLayer = window.parent.dataLayer || [];
    function parentGtag(){{ window.parent.dataLayer.push(arguments); }}
    parentGtag('js', new Date());
    parentGtag('config', '{GA_MEASUREMENT_ID}');
    window.parent.__gtag = parentGtag;
  }})();
</script>
""", height=0)


def fire_ga_event(event_name: str, params: dict = {}):
    import json
    components.html(f"""
    <script>
      if (window.parent && window.parent.__gtag) {{
        window.parent.__gtag('event', '{event_name}', {json.dumps(params)});
      }}
    </script>
    """, height=0)


def add_stamp_to_pdf(input_path: str, output_path: str) -> bool:
    """
    Stamp 'Made OCR friendly by Rakshit Dwaram' at the bottom-right of every page.

    Uses pikepdf ONLY — pikepdf is a hard dependency of ocrmypdf so it is
    ALWAYS available on Streamlit Cloud and any environment where ocrmypdf runs.
    No reportlab required.
    """
    try:
        import pikepdf
        from pikepdf import Pdf, Dictionary, Name, Array

        STAMP_TEXT = "Made OCR friendly by Rakshit Dwaram"
        # Helvetica character width at 7 pt ≈ 4.2 pts per character (conservative)
        TEXT_WIDTH_APPROX = len(STAMP_TEXT) * 4.2
        FONT_SIZE = 7
        MARGIN = 8  # pts from right / bottom edge

        pdf = Pdf.open(input_path)

        for page in pdf.pages:
            mediabox = page.mediabox
            pw = float(mediabox[2])

            x = pw - TEXT_WIDTH_APPROX - MARGIN
            y = 5.0

            # PDF content stream: save state, set green colour, draw text, restore
            content = (
                f"q "
                f"BT "
                f"/Stamp_F1 {FONT_SIZE} Tf "
                f"0.23 0.54 0.25 rg "
                f"{x:.2f} {y:.2f} Td "
                f"({STAMP_TEXT}) Tj "
                f"ET "
                f"Q\n"
            ).encode("latin-1")

            # ── Ensure /Resources/Font contains our font ──────────────────
            if "/Resources" not in page:
                page["/Resources"] = Dictionary()

            res = page["/Resources"]

            if "/Font" not in res:
                res["/Font"] = Dictionary()

            fonts = res["/Font"]

            if "/Stamp_F1" not in fonts:
                fonts["/Stamp_F1"] = Dictionary(
                    Type=Name("/Font"),
                    Subtype=Name("/Type1"),
                    BaseFont=Name("/Helvetica"),
                    Encoding=Name("/WinAnsiEncoding"),
                )

            # ── Append stamp stream to page contents ─────────────────────
            stamp_stream = pdf.make_stream(content)

            if "/Contents" in page:
                existing = page["/Contents"]
                if isinstance(existing, pikepdf.Array):
                    existing.append(stamp_stream)
                    page["/Contents"] = existing
                else:
                    page["/Contents"] = Array([existing, stamp_stream])
            else:
                page["/Contents"] = stamp_stream

        pdf.save(output_path)
        return True

    except Exception as e:
        import shutil
        shutil.copy(input_path, output_path)
        st.warning(f"Stamping skipped ({e}). PDF is still fully OCR'd.")
        return False


# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* ── App background: light warm cream ── */
.stApp {
    background-color: #f5f2ed;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, #d6e8c833 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, #c8dab022 0%, transparent 55%),
        repeating-linear-gradient(0deg, transparent, transparent 60px, #00000006 60px, #00000006 61px),
        repeating-linear-gradient(90deg, transparent, transparent 60px, #00000005 60px, #00000005 61px);
    color: #1a2015;
    min-height: 100vh;
}

/* ── Force all Streamlit block/section containers to be transparent ── */
section[data-testid="stMain"],
.stMainBlockContainer,
div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"],
div[data-testid="column"] {
    background: transparent !important;
}

#MainMenu, footer, header { visibility: hidden; }

.section-divider {
    border: none;
    border-top: 1px solid #c8d8c0;
    margin: 2.5rem 0;
}

/* ── All generic text ── */
p, span, div, li { color: #1a2015; }

/* ── Hero ── */
.hero-wrap { padding: 2.5rem 0 1rem 0; }
.hero-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4a7c59;
    margin-bottom: 0.6rem;
}
.hero-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: -1.5px;
    color: #1a2015;
    line-height: 1.1;
    margin-bottom: 0.5rem;
}
.hero-accent { color: #3a8a40; }
.hero-sub {
    font-size: 1rem;
    color: #6a7a65;
    font-weight: 300;
    line-height: 1.6;
}

/* ══════════════════════════════════════════════
   FILE UPLOADER — override dark inner drag zone
   ══════════════════════════════════════════════ */
[data-testid="stFileUploader"] {
    background: #eef5e8 !important;
    border: 1.5px dashed #a8c8a0 !important;
    border-radius: 10px !important;
    padding: 1.2rem !important;
    transition: border-color 0.25s;
}
[data-testid="stFileUploader"]:hover { border-color: #3a8a40 !important; }

/* The inner dark drag-drop box */
[data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
    border: 1.5px dashed #b8d4b0 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    background: #f0f9eb !important;
    border-color: #3a8a40 !important;
}

/* Text inside the dropzone */
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] small {
    color: #3a5e40 !important;
}

/* "Browse files" button inside uploader */
[data-testid="stFileUploaderDropzone"] button {
    background: #3a8a40 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
}

/* Uploaded file name row */
[data-testid="stFileUploaderFile"],
[data-testid="stFileUploaderFileName"] {
    color: #1a2015 !important;
    background: transparent !important;
}

/* ══════════════════════════════════════════════
   SELECTBOX — override dark background
   ══════════════════════════════════════════════ */
div[data-baseweb="select"] > div,
div[data-baseweb="select"] span {
    background-color: #ffffff !important;
    color: #1a2015 !important;
    border-color: #b8d4b0 !important;
    border-radius: 8px !important;
}
div[data-baseweb="select"] svg { fill: #3a8a40 !important; }

/* Selectbox dropdown menu */
ul[data-testid="stSelectboxVirtualDropdown"],
div[data-baseweb="popover"] ul,
div[data-baseweb="menu"] {
    background: #ffffff !important;
    border: 1px solid #b8d4b0 !important;
    border-radius: 8px !important;
}
div[data-baseweb="menu"] li,
div[data-baseweb="menu"] [role="option"] {
    background: #ffffff !important;
    color: #1a2015 !important;
}
div[data-baseweb="menu"] li:hover,
div[data-baseweb="menu"] [role="option"]:hover,
div[data-baseweb="menu"] [aria-selected="true"] {
    background: #eef5e8 !important;
    color: #1a2015 !important;
}

/* ══════════════════════════════════════════════
   CHECKBOX — fix label visibility
   ══════════════════════════════════════════════ */
label, .stCheckbox label p, [data-testid="stCheckbox"] label {
    color: #1a2015 !important;
    font-size: 0.88rem !important;
}
[data-testid="stCheckbox"] span[data-testid="stMarkdownContainer"] p {
    color: #1a2015 !important;
}
/* Checkbox box itself */
[data-baseweb="checkbox"] div {
    background-color: #ffffff !important;
    border-color: #3a8a40 !important;
}
[data-baseweb="checkbox"] input:checked + div {
    background-color: #3a8a40 !important;
    border-color: #3a8a40 !important;
}

/* ── Options card ── */
.options-card {
    background: #eef5e8;
    border: 1px solid #b8d4b0;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin: 1.2rem 0;
}
.options-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #4a7c59;
    margin-bottom: 1rem;
}

/* ── Selectbox widget label (above the box) ── */
[data-testid="stSelectbox"] label p,
[data-testid="stSelectbox"] > label {
    color: #1a2015 !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #3a8a40 !important;
    color: #ffffff !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 1.5px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.65rem 2rem !important;
    width: 100% !important;
    transition: opacity 0.15s, transform 0.1s !important;
}
.stButton > button:hover { opacity: 0.88 !important; transform: translateY(-1px) !important; }

.stDownloadButton > button {
    background: transparent !important;
    color: #3a8a40 !important;
    border: 1.5px solid #3a8a40 !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
    width: 100% !important;
    padding: 0.65rem 2rem !important;
}
.stDownloadButton > button:hover { background: #3a8a4015 !important; }

/* ── Alerts ── */
.stSuccess, .stError, .stInfo, .stWarning { border-radius: 8px !important; }
[data-testid="stNotification"],
[data-testid="stAlertContainer"] {
    background: #eef5e8 !important;
    color: #1a2015 !important;
    border-radius: 8px !important;
}
.stSpinner > div { color: #3a8a40 !important; }

/* ── Info box ── */
[data-testid="stInfoBanner"], div.stInfo {
    background: #eef5e8 !important;
    color: #1a2015 !important;
    border-left-color: #3a8a40 !important;
}

/* ── Progress bar ── */
.prog-wrap { margin: 1.2rem 0 0.5rem; }
.prog-header {
    display: flex;
    justify-content: space-between;
    font-family: 'Space Mono', monospace;
    font-size: 0.63rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4a7c59;
    margin-bottom: 0.45rem;
}
.prog-track {
    background: #d4e8cc;
    border-radius: 99px;
    height: 10px;
    overflow: hidden;
}
.prog-fill {
    height: 100%;
    background: linear-gradient(90deg, #3a8a40 0%, #7ec850 100%);
    border-radius: 99px;
    transition: width 0.5s cubic-bezier(.4,0,.2,1);
}
.prog-step {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #5a8a60;
    letter-spacing: 1px;
    margin-top: 0.3rem;
}

/* ── Stamp notice ── */
.stamp-notice {
    background: #eef5e8;
    border: 1px solid #b8d4b0;
    border-left: 3px solid #7ec850;
    border-radius: 0 8px 8px 0;
    padding: 0.6rem 1rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: #2a5e35;
    letter-spacing: 1px;
    margin-bottom: 1rem;
}

/* ── About ── */
.about-wrap { margin-top: 1rem; }
.about-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4a7c59;
    margin-bottom: 1.2rem;
}
.about-card {
    background: #eef5e8;
    border: 1px solid #b8d4b0;
    border-left: 3px solid #3a8a40;
    border-radius: 0 10px 10px 0;
    padding: 1.8rem 2rem;
}
.about-name {
    font-family: 'Space Mono', monospace;
    font-size: 1.25rem;
    font-weight: 700;
    color: #1a2015;
    margin-bottom: 0.15rem;
}
.about-title-tag {
    font-size: 0.78rem;
    color: #3a8a40;
    font-family: 'Space Mono', monospace;
    letter-spacing: 1px;
    margin-bottom: 1.4rem;
}
.about-body {
    font-size: 0.92rem;
    color: #3a4e38;
    line-height: 1.85;
    font-weight: 300;
}
.about-body p { margin-bottom: 1rem; }
.about-body p:last-child { margin-bottom: 0; }
.about-highlight { color: #2a6e30; font-weight: 500; }

/* ── Footer ── */
.footer-tag {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #7a9a80;
    text-align: center;
    margin-top: 3rem;
    padding-bottom: 1.5rem;
    letter-spacing: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-eyebrow">Legal Tech Tool</div>
    <div class="hero-title">PDF <span class="hero-accent">OCR</span><br>Converter</div>
    <div class="hero-sub">Turn scanned &amp; unreadable PDFs into fully searchable documents.<br>
    Free to use — built for law students.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# ── About Me ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="about-wrap">
    <div class="about-eyebrow">About the Builder</div>
    <div class="about-card">
        <div class="about-name">Rakshit Dwaram</div>
        <div class="about-title-tag">LL.B. II Year &nbsp;·&nbsp; Engineer &nbsp;·&nbsp; Data Scientist</div>
        <div class="about-body">
            <p>
                I'm currently in my <span class="about-highlight">second year of LL.B.</span>, with a background
                in engineering and prior experience working as a
                <span class="about-highlight">data scientist</span>.
            </p>
            <p>
                While studying law, I ran into a common problem — many of the reading materials we rely on
                are not OCR-compatible, which makes them difficult to search, navigate, and effectively use.
                Instead of working around the problem, I decided to
                <span class="about-highlight">build a solution</span>.
            </p>
            <p>
                I created this application to make legal study materials more accessible and easier to work with,
                especially for students who depend on digital resources. I've kept it
                <span class="about-highlight">free to use</span> because the goal is simple: to help fellow
                law students access and engage with their study materials more efficiently.
            </p>
            <p>
                Coming from a tech background, I see this as a way of contributing back — using what I know
                to solve a real problem in legal education. Going forward, I'm interested in continuing to build
                at the <span class="about-highlight">intersection of law and technology</span>, focusing on
                practical tools that improve access and usability.
            </p>
            <p>contact me: rakshitdwaram@gmail.com</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── File uploader ─────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drop your PDF here or click to browse",
    type=["pdf"],
    help="Supports scanned PDFs, image-only PDFs, and mixed documents.",
)

# ── Options ───────────────────────────────────────────────────────────────────
st.markdown('<div class="options-card"><div class="options-title">⚙ Options</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    language = st.selectbox(
        "Document Language",
        options=["eng", "fra", "deu", "spa", "ita", "por", "chi_sim", "chi_tra", "jpn", "ara", "hin"],
        format_func=lambda x: {
            "eng": "English", "fra": "French", "deu": "German",
            "spa": "Spanish", "ita": "Italian", "por": "Portuguese",
            "chi_sim": "Chinese (Simplified)", "chi_tra": "Chinese (Traditional)",
            "jpn": "Japanese", "ara": "Arabic", "hin": "Hindi"
        }[x],
        index=0,
    )
    deskew = st.checkbox(
        "Auto-deskew pages",
        value=False,
        help="Straighten skewed/tilted scans. ⚠️ Increases output size — only enable if pages are visibly crooked.",
    )

with col2:
    ocr_mode = st.selectbox(
        "OCR Mode",
        options=["skip_text", "force"],
        format_func=lambda x: {
            "skip_text": "Smart — skip pages with existing text (recommended)",
            "force":     "Force — re-OCR every page (may increase file size)",
        }[x],
        index=0,
        help="Smart mode is faster and keeps file sizes small. Force mode is only needed for PDFs with broken/incorrect text layers.",
    )

st.markdown('</div>', unsafe_allow_html=True)

# ── Stamp notice ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="stamp-notice">'
    '🖋&nbsp; Each page will be stamped: <strong>"Made OCR friendly by Rakshit Dwaram"</strong>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Run OCR ───────────────────────────────────────────────────────────────────
if uploaded_file:
    if st.button("🔍  Run OCR"):
        fire_ga_event("ocr_started", {
            "language": language,
            "file_name": uploaded_file.name,
            "file_size_kb": round(uploaded_file.size / 1024, 1),
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path   = os.path.join(tmpdir, "input.pdf")
            ocr_path     = os.path.join(tmpdir, "output_ocr.pdf")
            stamped_path = os.path.join(tmpdir, "output_stamped.pdf")

            with open(input_path, "wb") as f:
                f.write(uploaded_file.read())

            input_size_kb = os.path.getsize(input_path) / 1024

            prog_slot   = st.empty()
            status_slot = st.empty()

            OCR_STEPS = [
                (8,  "Analysing PDF structure…"),
                (20, "Preprocessing pages…"),
                (45, "Running Tesseract OCR engine…"),
                (70, "Embedding invisible text layer…"),
                (82, "Finalising OCR output…"),
            ]

            def render_progress(pct: int, label: str):
                prog_slot.markdown(f"""
                <div class="prog-wrap">
                  <div class="prog-header">
                    <span>OCR Progress</span><span>{pct}%</span>
                  </div>
                  <div class="prog-track">
                    <div class="prog-fill" style="width:{pct}%"></div>
                  </div>
                  <div class="prog-step">{label}</div>
                </div>
                """, unsafe_allow_html=True)

            render_progress(0, "Starting…")
            start = time.time()

            try:
                import threading

                ocr_done  = threading.Event()
                ocr_error = [None]

                def run_ocr():
                    try:
                        # Build kwargs — avoid options that blow up file size
                        kwargs = dict(
                            language=language,
                            # optimize=1 only helps when jbig2/pngquant are present;
                            # on Streamlit Cloud they are absent so skip it to avoid
                            # triggering the "output is Nx larger" warning path.
                            optimize=0,
                            progress_bar=False,
                            deskew=deskew,
                        )
                        if ocr_mode == "force":
                            kwargs["force_ocr"] = True
                        else:
                            # skip_text: only OCR pages that have no existing text layer
                            # This is the key fix — avoids re-encoding image pages unnecessarily
                            kwargs["skip_text"] = True

                        ocrmypdf.ocr(input_path, ocr_path, **kwargs)
                    except Exception as e:
                        ocr_error[0] = e
                    finally:
                        ocr_done.set()

                t = threading.Thread(target=run_ocr, daemon=True)
                t.start()

                for pct, label in OCR_STEPS:
                    if ocr_done.is_set():
                        break
                    render_progress(pct, label)
                    ocr_done.wait(timeout=2.8)

                ocr_done.wait()

                if ocr_error[0]:
                    raise ocr_error[0]

                render_progress(88, "Stamping pages with attribution…")
                stamped_ok = add_stamp_to_pdf(ocr_path, stamped_path)
                time.sleep(0.2)

                render_progress(100, "Complete ✓")
                elapsed = round(time.time() - start, 1)

                final_file = stamped_path if stamped_ok else ocr_path
                with open(final_file, "rb") as out_f:
                    pdf_bytes = out_f.read()

                output_size_kb = len(pdf_bytes) / 1024
                ratio = output_size_kb / input_size_kb if input_size_kb > 0 else 1.0
                size_str = (
                    f"{output_size_kb:.0f} KB"
                    if output_size_kb < 1024
                    else f"{output_size_kb/1024:.1f} MB"
                )
                ratio_str = (
                    f"  ·  {ratio:.1f}× original size"
                    if ratio > 1.15
                    else f"  ·  {ratio:.0%} of original size"
                )
                stamp_note = "  ·  pages stamped ✓" if stamped_ok else ""

                status_slot.success(
                    f"✅  OCR complete in {elapsed}s  ·  {size_str}{ratio_str}{stamp_note}"
                )

                fire_ga_event("ocr_success", {
                    "language": language,
                    "processing_time_s": elapsed,
                    "output_size_kb": round(output_size_kb, 1),
                    "size_ratio": round(ratio, 2),
                    "file_name": uploaded_file.name,
                })

                out_filename = f"{os.path.splitext(uploaded_file.name)[0]}_ocr.pdf"

                st.download_button(
                    label="⬇  Download OCR PDF",
                    data=pdf_bytes,
                    file_name=out_filename,
                    mime="application/pdf",
                )

                # Auto-download
                import base64
                b64 = base64.b64encode(pdf_bytes).decode()
                components.html(f"""
                <script>
                (function() {{
                  try {{
                    var bytes = Uint8Array.from(atob('{b64}'), c => c.charCodeAt(0));
                    var url   = URL.createObjectURL(new Blob([bytes], {{type: 'application/pdf'}}));
                    var a     = document.createElement('a');
                    a.href    = url;
                    a.download = '{out_filename}';
                    document.body.appendChild(a);
                    a.click();
                    setTimeout(function() {{
                      URL.revokeObjectURL(url);
                      document.body.removeChild(a);
                    }}, 1000);
                  }} catch(e) {{
                    console.warn('Auto-download failed:', e);
                  }}
                }})();
                </script>
                """, height=0)

            except ocrmypdf.exceptions.EncryptedPdfError:
                prog_slot.empty()
                st.error("🔒  The PDF is password-protected. Please decrypt it first.")
                fire_ga_event("ocr_failed", {"reason": "encrypted_pdf"})
            except Exception as e:
                prog_slot.empty()
                st.error(f"❌  OCR failed: {e}")
                fire_ga_event("ocr_failed", {"reason": str(e)[:100]})
else:
    st.info("☝️  Upload a PDF above to get started.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer-tag">POWERED BY OCRMYPDF + TESSERACT &nbsp;·&nbsp; BUILT BY RAKSHIT DWARAM</div>',
    unsafe_allow_html=True,
)
