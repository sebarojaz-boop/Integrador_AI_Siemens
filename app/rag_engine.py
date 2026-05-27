import os
import pickle
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INDEX_FOLDER = os.path.join(BASE_DIR, "index")

INDEX_PATH = os.path.join(INDEX_FOLDER, "faiss.index")
CHUNKS_PATH = os.path.join(INDEX_FOLDER, "chunks.pkl")


def get_api_key():

    try:
        import streamlit as st

        key = st.secrets.get("OPENAI_API_KEY", None)

        if key:
            return key

    except Exception:
        pass

    key = os.getenv("OPENAI_API_KEY")

    return key


def get_openai_client():

    api_key = get_api_key()

    if not api_key:
        raise ValueError("OPENAI_API_KEY no encontrada")

    return OpenAI(api_key=api_key)


client = get_openai_client()


def get_embedding(text):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def load_knowledge():

    print("Cargando índice FAISS...")

    if not os.path.exists(INDEX_PATH):
        print("No existe faiss.index")
        return None, None

    if not os.path.exists(CHUNKS_PATH):
        print("No existe chunks.pkl")
        return None, None

    index = faiss.read_index(INDEX_PATH)

    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)

    print(f"Chunks cargados: {len(chunks)}")

    return index, chunks


def search(query, index, chunks, k=5):

    query_embedding = np.array(
        [get_embedding(query)]
    ).astype("float32")

    distances, indices = index.search(
        query_embedding,
        k
    )

    results = []

    for idx in indices[0]:

        if 0 <= idx < len(chunks):
            results.append(chunks[idx])

    return results


