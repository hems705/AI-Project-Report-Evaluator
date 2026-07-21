from pypdf import PdfReader
from google import genai
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

reader = PdfReader("Hemanth reume 1.pdf")
full_text = ""
for page in reader.pages:
    full_text += page.extract_text()

lines = full_text.split(chr(10))
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

# Set up ChromaDB (local, persistent storage in a folder called chroma_db)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="resume_chunks")

# Embed and store each chunk
for i, chunk in enumerate(chunks):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=chunk
    )
    embedding = result.embeddings[0].values
    collection.add(
        ids=[f"chunk_{i}"],
        embeddings=[embedding],
        documents=[chunk]
    )
    print(f"Stored chunk {i+1}/{len(chunks)}")

print()
print("All chunks stored in ChromaDB successfully!")
print("Total items in collection:", collection.count())
