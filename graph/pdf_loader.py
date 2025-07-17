from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import TokenTextSplitter
import json

PDF_PATH = "/Users/drg/Desktop/Learning MiddleWare/Docs/OSN Memory Mgt/Operating Systems Network Course Reference book OSTEP.pdf"

def load_pdf_as_chunks(file_path, chunk_size=1000, chunk_overlap=100):
    # Step 1: Load all pages
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    print(f"✅ PDF had {len(pages)} pages")

    # Step 2: Combine all text
    full_text = "\n".join([p.page_content for p in pages])

    # Step 3: Token-aware splitting
    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(full_text)
    print(f"✅ Split into {len(chunks)} token-merged chunks")

    # Step 4: Display preview
    for i, chunk in enumerate(chunks[:5]):
        print(f"📄 Chunk {i+1}: {chunk[:500]}...\n")

    return chunks

def save_chunks_to_json(chunks, output_path="ostep_chunks.json"):
    docs = [{"content": chunk} for chunk in chunks]
    with open(output_path, "w") as f:
        json.dump(docs, f, indent=2)
    print(f"💾 Saved {len(docs)} chunks to {output_path}")

if __name__ == "__main__":
    pdf_path = PDF_PATH
    chunks = load_pdf_as_chunks(pdf_path)
    save_chunks_to_json(chunks)  # Optional step 