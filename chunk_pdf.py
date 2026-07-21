from pypdf import PdfReader

reader = PdfReader("Hemanth reume 1.pdf")

full_text = ""
for page in reader.pages:
    full_text += page.extract_text()

# Better chunking: split by bullet points and section headers, merge short fragments
lines = full_text.split(chr(10))
chunks = []
current_chunk = ""

for line in lines:
    line = line.strip()
    if not line:
        continue
    # Start a new chunk on bullet points or short ALL-CAPS headers
    if line.startswith("*") or line.startswith("-") or (line.isupper() and len(line) < 40):
        if current_chunk:
            chunks.append(current_chunk.strip())
        current_chunk = line
    else:
        current_chunk += " " + line

if current_chunk:
    chunks.append(current_chunk.strip())

print(f"Total chunks created: {len(chunks)}")
print()
for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(chunk)
    print()
