import os
import math
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Engineering Project Evaluation Tool",
    page_icon="📄",
    layout="wide",
)

# Spacious modern styling
st.markdown(
    """
    <style>
      .main .block-container {
        max-width: 1240px;
        padding-top: 2.5rem;
        padding-bottom: 5rem;
        padding-left: 3rem;
        padding-right: 3rem;
      }
      .summary-card {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 14px;
        padding: 24px 32px;
        margin-top: 1.5rem;
        margin-bottom: 2.5rem;
      }
      /* Custom Drag-and-Drop Box Styling */
      [data-testid="stFileUploaderDropzone"] {
        border: 2.5px dashed #3b82f6 !important;
        border-radius: 16px !important;
        background-color: rgba(59, 130, 246, 0.04) !important;
        padding: 40px 25px !important;
        text-align: center !important;
        transition: all 0.25s ease-in-out !important;
      }
      [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #1d4ed8 !important;
        background-color: rgba(59, 130, 246, 0.09) !important;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.15) !important;
      }
      .criterion-card {
        margin-bottom: 2rem !important;
      }
      .section-heading {
        margin-top: 2.2rem;
        margin-bottom: 1rem;
      }
      h1 {
        font-weight: 800 !important;
        margin-bottom: 0.5rem !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# App Header
st.title("📄 AI Engineering Project Evaluation Tool")
st.markdown(
    """
    Upload your engineering project report in PDF format.
    The system parses the document, ingests it into **ChromaDB**, retrieves key sections via **RAG**,
    and evaluates it against an academic **100-Point Rubric** powered by **Gemini**.
    """
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api/evaluate")


def evaluate_pdf(pdf_bytes: bytes, filename: str) -> dict:
    """Send PDF to FastAPI backend for RAG ingestion and rubric evaluation."""
    files = {"file": (filename, pdf_bytes, "application/pdf")}
    try:
        resp = requests.post(BACKEND_URL, files=files, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        st.error("⏳ Evaluation timed out. Please try uploading a shorter PDF or try again.")
        return {}
    except requests.exceptions.ConnectionError:
        st.error("🔌 Could not connect to the backend server. Make sure FastAPI is running on port 8000.")
        return {}
    except requests.exceptions.HTTPError as http_err:
        try:
            detail = resp.json().get("detail", str(http_err))
        except Exception:
            detail = str(http_err)
        st.error(f"❌ Server Error: {detail}")
        return {}
    except Exception as exc:
        st.error(f"❌ Backend error: {exc}")
        return {}


# Drag-and-Drop Drop Box
st.markdown("### 📥 Drag & Drop PDF Report Box")
st.caption("Drag your project report PDF directly from your computer into the box below:")

uploaded_pdf = st.file_uploader(
    "Drag & drop your PDF file here, or click to browse",
    type=["pdf"],
    help="Drag and drop your undergraduate engineering project report (max 25MB).",
)

# Optional quick-test button using pre-loaded sample
with st.expander("✨ Or test with a pre-loaded sample report", expanded=False):
    sample_col1, sample_col2 = st.columns(2)
    with sample_col1:
        load_sample_1 = st.button("📄 Test: Edge Computing IoT Gateway", use_container_width=True)
    with sample_col2:
        load_sample_2 = st.button("📄 Test: Smart Waste Sorting Robot", use_container_width=True)

pdf_bytes = None
pdf_filename = None

if uploaded_pdf is not None:
    if uploaded_pdf.size > 25 * 1024 * 1024:
        st.error("📛 File is too large. Maximum allowed size is 25MB.")
        st.stop()
    pdf_bytes = uploaded_pdf.read()
    pdf_filename = uploaded_pdf.name
    st.info(f"📂 Loaded from Drop Box: **{pdf_filename}**")
elif load_sample_1:
    sample_path = "samples/Edge_Computing_IoT_Gateway.pdf"
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_filename = os.path.basename(sample_path)
        st.info(f"📂 Loaded Sample: **{pdf_filename}**")
elif load_sample_2:
    sample_path = "samples/Autonomous_Smart_Waste_Sorter.pdf"
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_filename = os.path.basename(sample_path)
        st.info(f"📂 Loaded Sample: **{pdf_filename}**")

if not pdf_bytes:
    st.info("👆 Drag and drop a project report PDF into the drop box above to begin evaluation.")
    st.stop()

with st.spinner("🔍 Parsing PDF, building vector index, and evaluating rubric..."):
    result = evaluate_pdf(pdf_bytes, pdf_filename)

if not result:
    st.stop()

# Extract total and criteria
criteria = [k for k in result.keys() if k != "total"]
total = result.get("total", {})
total_score = total.get("score", 0)
max_total = total.get("max_points", 100)

# Compute percentage & theme
pct = min(100, max(0, int((total_score / max_total) * 100))) if max_total > 0 else 0

if pct >= 80:
    score_color = "#10b981"  # Green
    grade_label = "Grade: Excellent"
    grade_desc = "The report demonstrates comprehensive methodology, strong evidence, and clear technical documentation."
elif pct >= 65:
    score_color = "#3b82f6"  # Blue
    grade_label = "Grade: Good"
    grade_desc = "Solid engineering foundation with minor gaps in testing, validation, or documentation."
elif pct >= 50:
    score_color = "#f59e0b"  # Amber
    grade_label = "Grade: Satisfactory"
    grade_desc = "Core objectives partially addressed; improvements recommended in methodology or evidence."
else:
    score_color = "#ef4444"  # Red
    grade_label = "Grade: Needs Substantial Work"
    grade_desc = "Critical methodology, implementation evidence, or testing data is absent."

# Radial Gauge math
radius = 54
circumference = 2 * math.pi * radius
stroke_offset = circumference - (circumference * (pct / 100))

# Executive Summary Section
st.markdown('<div class="summary-card">', unsafe_allow_html=True)
col_gauge, col_info = st.columns([1, 2.5], gap="large")

with col_gauge:
    circle_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          margin: 0;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          background: transparent;
        }}
        .gauge-wrapper {{
          position: relative;
          width: 145px;
          height: 145px;
          display: flex;
          align-items: center;
          justify-content: center;
        }}
        svg {{
          transform: rotate(-90deg);
        }}
        .bg-circle {{
          fill: none;
          stroke: rgba(128, 128, 128, 0.2);
          stroke-width: 11;
        }}
        .progress-circle {{
          fill: none;
          stroke: {score_color};
          stroke-width: 11;
          stroke-linecap: round;
          stroke-dasharray: {circumference:.2f};
          stroke-dashoffset: {stroke_offset:.2f};
          transition: stroke-dashoffset 1s ease;
        }}
        .center-text {{
          position: absolute;
          text-align: center;
        }}
        .score-val {{
          font-size: 34px;
          font-weight: 800;
          color: {score_color};
          line-height: 1;
        }}
        .score-max {{
          font-size: 13px;
          font-weight: 600;
          color: #6b7280;
          margin-top: 4px;
        }}
        .grade-pill {{
          margin-top: 10px;
          font-size: 14px;
          font-weight: 700;
          color: {score_color};
          text-align: center;
        }}
      </style>
    </head>
    <body>
      <div class="gauge-wrapper">
        <svg width="145" height="145">
          <circle class="bg-circle" cx="72.5" cy="72.5" r="{radius}"></circle>
          <circle class="progress-circle" cx="72.5" cy="72.5" r="{radius}"></circle>
        </svg>
        <div class="center-text">
          <div class="score-val">{total_score}</div>
          <div class="score-max">/ {max_total}</div>
        </div>
      </div>
      <div class="grade-pill">{grade_label} ({pct}%)</div>
    </body>
    </html>
    """
    components.html(circle_html, height=200)

with col_info:
    st.markdown("### 📊 Executive Assessment")
    st.markdown(f"**Overall Grade:** `{grade_label}`")
    st.markdown(f"**Score:** **{total_score} out of {max_total} points** ({pct}%)")
    st.markdown(f"**Summary Feedback:** {grade_desc}")
    st.caption("Review each rubric criterion below for side-by-side strengths, gaps, and actionable recommendations.")

st.markdown('</div>', unsafe_allow_html=True)

# High-Level Score Overview Table
st.markdown("### 📋 Score Summary at a Glance")

summary_rows = []
for crit in criteria:
    item = result[crit]
    c_score = item.get("score", 0)
    c_max = item.get("max_points", 0)
    c_pct = (c_score / c_max * 100) if c_max > 0 else 0
    
    if c_pct >= 80:
        status_label = "🟢 Strong"
    elif c_pct >= 60:
        status_label = "🟡 Good"
    elif c_pct >= 40:
        status_label = "🟠 Needs Polish"
    else:
        status_label = "🔴 Significant Gap"

    summary_rows.append({
        "Criterion": crit,
        "Score": c_score,
        "Max Points": c_max,
        "Score %": f"{c_pct:.0f}%",
        "Assessment": status_label,
    })

summary_df = pd.DataFrame(summary_rows)
st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Criterion": st.column_config.TextColumn("Criterion", width="large"),
        "Score": st.column_config.NumberColumn("Score", width="small"),
        "Max Points": st.column_config.NumberColumn("Max Points", width="small"),
        "Score %": st.column_config.TextColumn("Percentage", width="small"),
        "Assessment": st.column_config.TextColumn("Assessment", width="medium"),
    },
)

st.markdown("<br>", unsafe_allow_html=True)

# Spacious Detailed Rubric Cards (Side-by-Side + Needed Improvements Below)
st.markdown("### 🔍 Rubric Criteria Detailed Breakdown")
st.caption("Each criterion displays strengths & evidence side-by-side with weaknesses & missing info, followed by needed improvements.")

for crit in criteria:
    item = result[crit]
    score = item.get("score", 0)
    max_pts = item.get("max_points", 0)
    ratio = (score / max_pts) if max_pts > 0 else 0

    if ratio >= 0.8:
        badge_color = "#10b981"
        badge_bg = "rgba(16, 185, 129, 0.12)"
    elif ratio >= 0.6:
        badge_color = "#3b82f6"
        badge_bg = "rgba(59, 130, 246, 0.12)"
    elif ratio >= 0.4:
        badge_color = "#f59e0b"
        badge_bg = "rgba(245, 158, 11, 0.12)"
    else:
        badge_color = "#ef4444"
        badge_bg = "rgba(239, 68, 68, 0.12)"

    with st.container(border=True):
        # Header Row: Title & Score Badge
        h_left, h_right = st.columns([3, 1])
        with h_left:
            st.markdown(f"#### 📌 {crit}")
        with h_right:
            st.markdown(
                f"<div style='text-align: right;'>"
                f"<span style='background-color: {badge_bg}; color: {badge_color}; font-weight: 700; font-size: 15px; padding: 6px 14px; border-radius: 20px; border: 1px solid {badge_color};'>"
                f"{score} / {max_pts} pts"
                f"</span></div>",
                unsafe_allow_html=True,
            )

        st.progress(min(1.0, max(0.0, ratio)))
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Side by side: Strengths & Evidence on Left, Weaknesses & Missing on Right
        col_left, col_right = st.columns(2, gap="large")

        with col_left:
            st.markdown("##### ✅ Strengths")
            st.write(item.get("strengths", "No specific strengths highlighted."))
            st.markdown("##### 📖 Supporting Evidence")
            st.info(f"\"{item.get('evidence', 'No direct excerpt quoted.')}\"")

        with col_right:
            st.markdown("##### ⚠️ Weaknesses")
            st.write(item.get("weaknesses", "No major weaknesses detected."))
            st.markdown("##### ❓ Missing Information")
            st.warning(item.get("missing", "No critical omissions noted."))

        # Needed Improvements spanning full width below
        st.markdown("##### 💡 Needed Improvements & Actionable Suggestions")
        st.success(item.get("suggestion", "Continue maintaining current standard."))

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

st.success("✅ Evaluation report generated successfully.")

