from pathlib import Path
import pickle
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

from ingestor import scan_project_files

# ==========================================
# CONFIG
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[3]

VECTORSTORE_DIR = BASE_DIR / "vectorstore"

INDEX_PATH = VECTORSTORE_DIR / "faiss_index.bin"
DOCS_PATH = VECTORSTORE_DIR / "docs.pkl"

EMBEDDING_MODEL = "text-embedding-3-small"

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================
# HELPERS
# ==========================================

def chunk_text(text, chunk_size=1200, overlap=200):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def get_embedding(text):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000]
    )

    return response.data[0].embedding


# ==========================================
# MAIN
# ==========================================

def build_vectorstore():

    print("\n🧠 Cargando documentos industriales...\n")

    documents = scan_project_files(BASE_DIR)

    if not documents:
        print("❌ No se encontraron documentos.")
        return

    all_chunks = []

    for doc in documents:

        content = doc["content"]

        chunks = chunk_text(content)

        for chunk in chunks:

            all_chunks.append(
                f"""
ARCHIVO: {doc['file_name']}
TIPO: {doc['extension']}

CONTENIDO:
{chunk}
"""
            )

    print(f"📄 Chunks generados: {len(all_chunks)}")

    embeddings = []

    for i, chunk in enumerate(all_chunks):

        print(f"🔹 Embedding {i+1}/{len(all_chunks)}")

        emb = get_embedding(chunk)

        embeddings.append(emb)

    embeddings = np.array(embeddings).astype("float32")

    dim = len(embeddings[0])

    index = faiss.IndexFlatL2(dim)

    index.add(embeddings)

    VECTORSTORE_DIR.mkdir(exist_ok=True)

    faiss.write_index(index, str(INDEX_PATH))

    with open(DOCS_PATH, "wb") as f:
        pickle.dump(all_chunks, f)

    print("\n✅ VECTORSTORE GENERADO")
    print(f"📦 Índice: {INDEX_PATH}")
    print(f"📚 Docs: {DOCS_PATH}")
    print(f"📄 Total chunks: {len(all_chunks)}")


if __name__ == "__main__":
    build_vectorstore()