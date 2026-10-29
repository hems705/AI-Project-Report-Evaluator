# 📄 AI Engineering Project Evaluation Tool

An AI-powered tool that evaluates engineering project reports against a **100-point academic rubric** using **RAG (Retrieval-Augmented Generation)** and **Google Gemini API**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.65+-red?logo=streamlit)
![Gemini](https://img.shields.io/badge/Google%20Gemini-API-orange?logo=google)

---

## ✨ Features

- **Drag & Drop PDF Upload** — Upload any engineering project report
- **RAG-based Analysis** — Chunks, embeds, and retrieves relevant context from the report
- **100-Point Rubric Evaluation** — Scores across 6 criteria with evidence grounding
- **Interactive Dashboard** — Radial score gauge, side-by-side strengths/weaknesses, actionable suggestions
- **Fast** — End-to-end evaluation in ~5-8 seconds

## 📊 Evaluation Rubric (100 Points)

| Criteria | Max Score |
|---|---|
| Problem Definition & Relevance | 15 |
| Technical Approach / Methodology | 25 |
| Implementation & Results | 25 |
| Innovation & Originality | 15 |
| Report Quality & Structure | 10 |
| References & Citations | 10 |

## 🏗️ Architecture

```
PDF Upload → Text Extraction (PyPDF) → Chunking → Embedding (Gemini)
    → ChromaDB Storage → Context Retrieval → Gemini Evaluation → UI Display
```

```
├── backend/
│   ├── __init__.py
│   ├── evaluator.py      # Rubric evaluation with Gemini API
│   ├── main.py            # FastAPI server
│   └── rag.py             # PDF ingestion, embedding, ChromaDB, Q&A
├── samples/               # Sample project reports for testing
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── streamlit_app.py       # Frontend UI (Streamlit)
├── requirements.txt       # Python dependencies
├── .env.example           # API key template
└── .gitignore
```

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/hems705/RAG-DOCUMENT-QA.git
cd RAG-DOCUMENT-QA
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

### 5. Run the app
```bash
# Terminal 1: Start the FastAPI backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start the Streamlit frontend
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Backend:** FastAPI
- **LLM:** Google Gemini (`gemini-3.5-flash-lite` / `gemini-3.5-flash`)
- **Embeddings:** `gemini-embedding-001`
- **Vector DB:** ChromaDB
- **PDF Parsing:** PyPDF

## 📝 How It Works

1. **Upload** a PDF project report via drag-and-drop
2. **Ingestion** — The PDF is parsed, chunked into ~500-char segments, and embedded using Gemini embeddings
3. **Storage** — Embeddings are stored in ChromaDB for retrieval
4. **Evaluation** — For each rubric criterion, relevant chunks are retrieved and sent to Gemini with strict grounding rules (no hallucination)
5. **Display** — Results shown with a radial score gauge, criterion cards with strengths/weaknesses, and improvement suggestions

## 📄 License

This project is for academic purposes.
