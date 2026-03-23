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
# Replace G-XXXXXXXXXX with your actual GA4 Measurement ID
GA_MEASUREMENT_ID = "G-XXXXXXXXXX"

components.html(f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}', {{
    page_title: 'PDF OCR Converter',
    page_location: window.location.href,
  }});

  // Helper: send a custom event to GA4 from inside the iframe to the parent
  function trackEvent(eventName, params) {{
    try {{
      // Post message to parent window (Streamlit host)
      window.parent.postMessage({{
        type: 'ga_event',
        eventName: eventName,
        params: params
      }}, '*');
    }} catch(e) {{}}
  }}

  // Listen for event requests from Streamlit (via query param trick)
  const urlParams = new URLSearchParams(window.location.search);
  const gaEvent = urlParams.get('ga_event');
  const gaParams = urlParams.get('ga_params');
  if (gaEvent) {{
    try {{
      gtag('event', gaEvent, gaParams ? JSON.parse(decodeURIComponent(gaParams)) : {{}});
    }} catch(e) {{}}
  }}
</script>

<!-- Re-fire gtag in parent window so events register on the main page -->
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
    """Fire a GA4 custom event by injecting a hidden component."""
    import json, urllib.parse
    encoded = urllib.parse.quote(json.dumps(params))
    components.html(f"""
    <script>
      if (window.parent && window.parent.__gtag) {{
        window.parent.__gtag('event', '{event_name}', {json.dumps(params)});
      }}
    </script>
    """, height=0)


# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Background: dark with subtle green-tinted grid & glow ── */
.stApp {
    background-color: #0a0c0f;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, #0f2a1a33 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, #1a2f0f22 0%, transparent 55%),
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 60px,
            #ffffff04 60px,
            #ffffff04 61px
        ),
        repeating-linear-gradient(
            90deg,
            transparent,
            transparent 60px,
            #ffffff03 60px,
            #ffffff03 61px
        );
    color: #e8e4dc;
    min-height: 100vh;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, header {visibility: hidden;}

/* ── Divider ── */
.section-divider {
    border: none;
    border-top: 1px solid #1a2a1e;
    margin: 2.5rem 0;
}

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
    color: #e8e4dc;
    line-height: 1.1;
    margin-bottom: 0.5rem;
}
.hero-accent { color: #7ec850; }
.hero-sub {
    font-size: 1rem;
    color: #5a5e56;
    margin-bottom: 0;
    font-weight: 300;
    line-height: 1.6;
}

/* ── Upload box ── */
[data-testid="stFileUploader"] {
    background: #0f1612;
    border: 1.5px dashed #1e3326;
    border-radius: 10px;
    padding: 1.2rem;
    transition: border-color 0.25s;
}
[data-testid="stFileUploader"]:hover { border-color: #7ec850; }

/* ── Options card ── */
.options-card {
    background: #0d1410;
    border: 1px solid #1a2a1e;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin: 1.2rem 0;
}
.options-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #3a5a40;
    margin-bottom: 1rem;
}

/* Selectbox / checkbox labels */
label { color: #8a9e8e !important; font-size: 0.88rem !important; }

/* ── Buttons ── */
.stButton > button {
    background: #7ec850 !important;
    color: #070e09 !important;
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

/* ── Download button ── */
.stDownloadButton > button {
    background: transparent !important;
    color: #7ec850 !important;
    border: 1.5px solid #7ec850 !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
    width: 100% !important;
    padding: 0.65rem 2rem !important;
}
.stDownloadButton > button:hover { background: #7ec85018 !important; }

/* ── Alerts ── */
.stSuccess, .stError, .stInfo { border-radius: 8px !important; }
.stSpinner > div { color: #7ec850 !important; }

/* ── About Me ── */
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
    background: #0d1410;
    border: 1px solid #1a2a1e;
    border-left: 3px solid #7ec850;
    border-radius: 0 10px 10px 0;
    padding: 1.8rem 2rem;
}
.about-name {
    font-family: 'Space Mono', monospace;
    font-size: 1.25rem;
    font-weight: 700;
    color: #e8e4dc;
    margin-bottom: 0.15rem;
}
.about-title-tag {
    font-size: 0.78rem;
    color: #7ec850;
    font-family: 'Space Mono', monospace;
    letter-spacing: 1px;
    margin-bottom: 1.4rem;
}
.about-body {
    font-size: 0.92rem;
    color: #7a8a7e;
    line-height: 1.85;
    font-weight: 300;
}
.about-body p { margin-bottom: 1rem; }
.about-body p:last-child { margin-bottom: 0; }
.about-highlight { color: #b0d490; font-weight: 400; }

/* ── Footer ── */
.footer-tag {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #1e2e22;
    text-align: center;
    margin-top: 3rem;
    padding-bottom: 1.5rem;
    letter-spacing: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-eyebrow">Legal Tech Tool</div>
    <div class="hero-title">PDF <span class="hero-accent">OCR</span><br>Converter</div>
    <div class="hero-sub">Turn scanned &amp; unreadable PDFs into fully searchable documents.<br>Free to use — built for law students.</div>
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
            </p>
            <p>contact me : rakshitdwaram@gmail.com
            </p>
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
    deskew = st.checkbox("Auto-deskew pages", value=True, help="Straighten skewed/tilted scans")

with col2:
    optimize = st.selectbox(
        "Output optimisation",
        options=[0, 1, 2, 3],
        format_func=lambda x: {0: "None", 1: "Balanced (recommended)", 2: "High", 3: "Maximum"}[x],
        index=1,
    )
    force_ocr = st.checkbox("Force OCR on all pages", value=True, help="Re-OCR every page, even if it already has a text layer")

st.markdown('</div>', unsafe_allow_html=True)

# ── Run OCR ───────────────────────────────────────────────────────────────────
if uploaded_file:
    if st.button("🔍  Run OCR"):
        # Track: user clicked Run OCR
        fire_ga_event("ocr_started", {
            "language": language,
            "file_name": uploaded_file.name,
            "file_size_kb": round(uploaded_file.size / 1024, 1),
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output_ocr.pdf")

            with open(input_path, "wb") as f:
                f.write(uploaded_file.read())

            start = time.time()
            with st.spinner("Running OCR — this may take a moment for large files…"):
                try:
                    ocrmypdf.ocr(
                        input_path,
                        output_path,
                        deskew=deskew,
                        optimize=optimize,
                        force_ocr=force_ocr,
                        language=language,
                        progress_bar=False,
                    )
                    elapsed = round(time.time() - start, 1)

                    with open(output_path, "rb") as out_f:
                        pdf_bytes = out_f.read()

                    size_kb = round(len(pdf_bytes) / 1024, 1)
                    st.success(f"✅  OCR complete in {elapsed}s — output size: {size_kb} KB")

                    # Track: successful conversion
                    fire_ga_event("ocr_success", {
                        "language": language,
                        "processing_time_s": elapsed,
                        "output_size_kb": size_kb,
                        "file_name": uploaded_file.name,
                    })

                    st.download_button(
                        label="⬇  Download OCR PDF",
                        data=pdf_bytes,
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}_ocr.pdf",
                        mime="application/pdf",
                    )

                except ocrmypdf.exceptions.EncryptedPdfError:
                    st.error("🔒  The PDF is password-protected. Please decrypt it first.")
                    fire_ga_event("ocr_failed", {"reason": "encrypted_pdf"})
                except Exception as e:
                    st.error(f"❌  OCR failed: {e}")
                    fire_ga_event("ocr_failed", {"reason": str(e)[:100]})
else:
    st.info("☝️  Upload a PDF above to get started.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer-tag">POWERED BY OCRMYPDF + TESSERACT &nbsp;·&nbsp; BUILT BY RAKSHIT DWARAM</div>',
    unsafe_allow_html=True
)
