import os
import pickle
import faiss
import numpy as np
from openai import OpenAI
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KNOWLEDGE_FOLDER = os.path.join(BASE_DIR, "knowledge_base")
INDEX_FOLDER = os.path.join(BASE_DIR, "index")

INDEX_PATH = os.path.join(INDEX_FOLDER, "faiss.index")
CHUNKS_PATH = os.path.join(INDEX_FOLDER, "chunks.pkl")


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        import streamlit as st
        api_key = st.secrets.get("OPENAI_API_KEY", api_key)
    except Exception:
        pass

    if not api_key:
        raise ValueError("Falta OPENAI_API_KEY")

    return OpenAI(api_key=api_key)


client = get_openai_client()


def extract_pdf_text(path):
    text = ""

    try:
        reader = PdfReader(path)

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    except Exception as e:
        print(f"Error leyendo PDF {path}: {e}")

    return text


def chunk_text(text, size=1200, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()

        if len(chunk) > 100:
            chunks.append(chunk)

        start += size - overlap

    return chunks


def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def build_knowledge():
    os.makedirs(INDEX_FOLDER, exist_ok=True)

    all_chunks = []

    print("Leyendo carpeta knowledge_base...")

    if not os.path.exists(KNOWLEDGE_FOLDER):
        print("No existe la carpeta knowledge_base")
        return None, None

    for filename in os.listdir(KNOWLEDGE_FOLDER):
        path = os.path.join(KNOWLEDGE_FOLDER, filename)

        if filename.lower().endswith(".pdf"):
            print(f"Leyendo PDF: {filename}")

            text = extract_pdf_text(path)
            chunks = chunk_text(text)

            all_chunks.extend(chunks)

        elif filename.lower().endswith(".txt"):
            print(f"Leyendo TXT: {filename}")

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            chunks = chunk_text(text)
            all_chunks.extend(chunks)

    if not all_chunks:
        print("No se encontraron textos útiles.")
        return None, None

    print(f"Generando embeddings para {len(all_chunks)} chunks...")

    embeddings = []

    for i, chunk in enumerate(all_chunks):
        embedding = get_embedding(chunk)
        embeddings.append(embedding)

        if i % 10 == 0:
            print(f"Procesados {i}/{len(all_chunks)}")

    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(all_chunks, f)

    print("Base de conocimiento creada correctamente.")

    return index, all_chunks


def load_knowledge():
    os.makedirs(INDEX_FOLDER, exist_ok=True)

    if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
        print("Cargando índice existente...")

        index = faiss.read_index(INDEX_PATH)

        with open(CHUNKS_PATH, "rb") as f:
            chunks = pickle.load(f)

        return index, chunks

    return build_knowledge()


def search(query, index, chunks, k=5):
    query_embedding = np.array([get_embedding(query)]).astype("float32")

    distances, indices = index.search(query_embedding, k)

    results = []

    for idx in indices[0]:
        if 0 <= idx < len(chunks):
            results.append(chunks[idx])

    return results