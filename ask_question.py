from google import genai
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="resume_chunks")

question = "What projects has this person built?"

# Step 1: Embed the question
question_embedding = client.models.embed_content(
    model="gemini-embedding-001",
    contents=question
).embeddings[0].values

# Step 2: Search ChromaDB for the most relevant chunk
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=2
)

retrieved_chunks = results["documents"][0]
context = chr(10).join(retrieved_chunks)

# Step 3: Build the prompt with context (this is prompt engineering + system prompt in action!)
prompt = f"""You are a helpful assistant answering questions about a resume.
Only use the following context to answer. If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {question}
"""

# Step 4: Generate the answer
response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=prompt
)

print("QUESTION:", question)
print()
print("ANSWER:", response.text)
print()
print("--- SOURCE CHUNKS USED ---")
for i, chunk in enumerate(retrieved_chunks):
    print(f"Source {i+1}: {chunk[:100]}...")
