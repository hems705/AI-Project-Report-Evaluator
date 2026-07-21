from pypdf import PdfReader

reader = PdfReader("Hemanth reume 1.pdf")

full_text = ""
for page in reader.pages:
    full_text += page.extract_text()

print(full_text)
