import json
import logging
from .rag import ingest_pdf, client, chroma_client, COLLECTION_NAME, embed_batch

logger = logging.getLogger(__name__)

# Rubric definition – max points per criterion (Total = 100)
RUBRIC = {
    "Problem definition": 15,
    "Technical methodology": 20,
    "Implementation and evidence": 20,
    "Innovation": 15,
    "Testing and validation": 15,
    "Documentation and reproducibility": 15,
}


def evaluate_report(pdf_path: str) -> dict:
    """Ingest the PDF and evaluate it against the 100-point rubric.
    Returns a dict of criterion -> {score, max_points, strengths, weaknesses, evidence, missing, suggestion}
    plus a total score.
    """
    # 1. Ingest PDF with batch embedding into ChromaDB
    ingest_pdf(pdf_path)

    # 2. Batch-retrieve context for all criteria
    criteria_names = list(RUBRIC.keys())
    queries = [f"{crit} of the engineering project" for crit in criteria_names]
    query_embeddings = embed_batch(queries)

    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    hits = collection.query(
        query_embeddings=query_embeddings,
        n_results=2,
    )

    context_sections = []
    for idx, crit in enumerate(criteria_names):
        docs = hits["documents"][idx] if hits and hits.get("documents") else []
        text = "\n".join(docs).strip()
        context_sections.append(
            f"--- Criterion: {crit} (Max: {RUBRIC[crit]} pts) ---\n"
            f"Retrieved Excerpt:\n{text if text else 'No direct excerpt found.'}\n"
        )
    combined_context = "\n".join(context_sections)

    # 3. Create comprehensive rubric evaluation prompt with strict grounding
    prompt = f"""You are an expert AI evaluator for undergraduate engineering projects.
Evaluate the student's project report against the 100-point rubric criteria below using ONLY the provided report excerpts.

CRITICAL EVALUATION RULES:
1. STRICT FACTUAL GROUNDING: Base all scores and feedback strictly on the provided report excerpts. Do NOT assume, invent, or extrapolate features, experiments, datasets, hardware, or metrics not explicitly mentioned.
2. EVIDENCE REQUIRED: Provide direct quotes or specific factual references from the report in the "evidence" field. If no evidence exists in the excerpts for a criterion, write: "No direct evidence provided in the report."
3. FLAG MISSING EVIDENCE: In the "missing" field, explicitly call out what key information, experimental validation, baseline comparisons, or technical details are absent from the report.
4. MERIT-BASED SCORING: Deduct points if evidence is missing, vague, or unsubstantiated. Never award full marks without concrete supporting evidence.
5. CONSTRUCTIVE SUGGESTIONS: Provide actionable engineering advice detailing exactly what the student should add or test to improve their project report.

Rubric Criteria:
1. Problem definition (15 max points)
2. Technical methodology (20 max points)
3. Implementation and evidence (20 max points)
4. Innovation (15 max points)
5. Testing and validation (15 max points)
6. Documentation and reproducibility (15 max points)

Project Excerpts:
{combined_context}

Return ONLY a valid JSON object matching this schema:
{{
  "criteria": {{
    "Problem definition": {{
      "score": 0, "max_points": 15, "strengths": "...", "weaknesses": "...", "evidence": "...", "missing": "...", "suggestion": "..."
    }},
    "Technical methodology": {{
      "score": 0, "max_points": 20, "strengths": "...", "weaknesses": "...", "evidence": "...", "missing": "...", "suggestion": "..."
    }},
    "Implementation and evidence": {{
      "score": 0, "max_points": 20, "strengths": "...", "weaknesses": "...", "evidence": "...", "missing": "...", "suggestion": "..."
    }},
    "Innovation": {{
      "score": 0, "max_points": 15, "strengths": "...", "weaknesses": "...", "evidence": "...", "missing": "...", "suggestion": "..."
    }},
    "Testing and validation": {{
      "score": 0, "max_points": 15, "strengths": "...", "weaknesses": "...", "evidence": "...", "missing": "...", "suggestion": "..."
    }},
    "Documentation and reproducibility": {{
      "score": 0, "max_points": 15, "strengths": "...", "weaknesses": "...", "evidence": "...", "missing": "...", "suggestion": "..."
    }}
  }},
  "total_score": 0,
  "max_total": 100
}}
"""

    # 4. Generate evaluation using fast responsive Gemini model
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
    response_data = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            parsed = json.loads(response.text.strip())
            if "criteria" in parsed:
                response_data = parsed
                break
        except Exception as e:
            logger.warning(f"Failed evaluation with {model_name}: {e}")
            continue

    results = {}
    if response_data and "criteria" in response_data:
        eval_criteria = response_data["criteria"]
        for crit, max_pts in RUBRIC.items():
            val = eval_criteria.get(crit, {})
            score = val.get("score", 0)
            try:
                score = int(score)
            except Exception:
                score = 0
            score = max(0, min(max_pts, score))

            results[crit] = {
                "max_points": max_pts,
                "score": score,
                "strengths": val.get("strengths", "N/A"),
                "weaknesses": val.get("weaknesses", "N/A"),
                "evidence": val.get("evidence", "N/A"),
                "missing": val.get("missing", "N/A"),
                "suggestion": val.get("suggestion", "N/A"),
            }
        total_score = sum(v["score"] for v in results.values())
        results["total"] = {"score": total_score, "max_points": 100}
    else:
        # Fallback if model fails
        for crit, max_pts in RUBRIC.items():
            results[crit] = {
                "max_points": max_pts,
                "score": 0,
                "strengths": "Evaluation service busy",
                "weaknesses": "Could not complete automated grading",
                "evidence": "N/A",
                "missing": "API response unavailable",
                "suggestion": "Please retry in a moment",
            }
        results["total"] = {"score": 0, "max_points": 100}

    return results
