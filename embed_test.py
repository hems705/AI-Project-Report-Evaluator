from pypdf import PdfReader
from google import genai
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

# Generate embedding for the first chunk as a test
result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=chunks[0]
)

print("Chunk text:", chunks[0])
print()
print("Embedding (first 10 numbers):", result.embeddings[0].values[:10])
print()
print("Total numbers in this embedding:", len(result.embeddings[0].values))
