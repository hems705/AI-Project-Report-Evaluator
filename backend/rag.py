import os
from pypdf import PdfReader
from google import genai
import chromadb
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chroma_client = chromadb.PersistentClient(path="./chroma_db")
COLLECTION_NAME = "pdf_chunks"


def extract_text(pdf_path):
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
    return full_text


def chunk_text(full_text):
    lines = full_text.split("\n")
    chunks = []
    current_chunk = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("*") or line.startswith("-") or (line.isupper() and len(line) < 40):
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            current_chunk += " " + line
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def embed(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


def embed_batch(texts, batch_size=50):
    """Embed multiple texts in batch requests for speed."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=batch
        )
        for emb in result.embeddings:
            all_embeddings.append(emb.values)
    return all_embeddings


def ingest_pdf(pdf_path):
    full_text = extract_text(pdf_path)
    chunks = [c for c in chunk_text(full_text) if c.strip()]
    if not chunks:
        return {"chunks_stored": 0}

    # wipe the previous PDF's data so uploads don't mix or collide
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    # Batch embed and store for maximum speed
    embeddings = embed_batch(chunks)
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks
    )
    return {"chunks_stored": len(chunks)}


def answer(question):
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    results = collection.query(
        query_embeddings=[embed(question)],
        n_results=2
    )
    retrieved_chunks = results["documents"][0]
    context = "\n".join(retrieved_chunks)

    prompt = f"""You are an AI study assistant helping students learn from their study materials.

Instructions:
- Answer using only the provided context.
- Explain concepts clearly in simple language.
- Organize answers with bullet points when useful.
- Give examples only when supported by the context.
- If the answer is not available in the context, say:
  \"I couldn't find the answer in your uploaded study material.\"

Study Material:
{context}

Student's Question: {question}

Answer:
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    return {"answer": response.text, "sources": retrieved_chunks}


if __name__ == "__main__":
    print(ingest_pdf("edge.pdf"))
    result = answer("What is edge computing?")
    print(result["answer"])

