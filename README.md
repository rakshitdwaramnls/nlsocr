# 📄 PDF OCR Converter

A free, web-hosted tool to convert scanned/unreadable PDFs into fully searchable, OCR-compliant documents.

Built with **Streamlit** + **ocrmypdf** + **Tesseract**.

---

## 🚀 Deploy for Free on Streamlit Community Cloud

1. **Fork or push this repo to your GitHub account.**

2. **Go to [share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.

3. Click **"New app"** → select your repo → set main file to `app.py` → click **Deploy**.

4. That's it. You'll get a public URL like `https://yourname-pdf-ocr.streamlit.app`.

> Streamlit Cloud reads `packages.txt` to install system dependencies (Tesseract, Poppler) automatically.

---

## 📁 File Structure

```
├── app.py            # Main Streamlit app
├── requirements.txt  # Python dependencies
├── packages.txt      # System-level apt packages (Tesseract, Poppler)
└── README.md
```

---

## ✨ Features

- Upload any scanned or image-only PDF
- Auto-deskew tilted scans
- Clean noise before OCR
- Multi-language support (English, French, German, Spanish, Japanese, Arabic, Hindi, Chinese, and more)
- Configurable output optimisation (file size vs quality)
- Skip pages that already have text
- Download the OCR'd PDF instantly

---

## 🛠 Run Locally

```bash
# Install system deps (Ubuntu/Debian)
sudo apt install tesseract-ocr tesseract-ocr-all poppler-utils unpaper

# Install Python deps
pip install -r requirements.txt

# Run
streamlit run app.py
```

---

## ⚠️ Limits (Streamlit Free Tier)

| Resource | Limit |
|----------|-------|
| RAM | 1 GB |
| Storage | Ephemeral (files deleted after session) |
| Concurrent users | A few (sleeps after inactivity, wakes on visit) |
| Cost | **Free** |

For heavier workloads, consider **Hugging Face Spaces** (free, 16 GB RAM).
