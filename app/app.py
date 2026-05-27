import os
import base64
import pickle
from pathlib import Path

import faiss
import numpy as np
import streamlit as st
from openai import OpenAI


# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="SCA AI Engineering Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

CSS_PATH = BASE_DIR / "styles" / "sca_theme.css"
LOGO_PATH = BASE_DIR / "assets" / "sca_logo.svg"

INDEX_PATH = ROOT_DIR / "faiss_index.bin"
DOCS_PATH = ROOT_DIR / "docs.pkl"

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"


# =====================================================
# ESTILOS Y LOGO
# =====================================================

if CSS_PATH.exists():
    st.markdown(
        f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )

logo_base64 = ""

if LOGO_PATH.exists():
    logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()


def logo_html(width=210):
    if not logo_base64:
        return ""
    return f'<img src="data:image/svg+xml;base64,{logo_base64}" width="{width}">'


# =====================================================
# OPENAI / RAG
# =====================================================

@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


@st.cache_resource(show_spinner=False)
def load_rag():
    if not INDEX_PATH.exists() or not DOCS_PATH.exists():
        return None, []

    index = faiss.read_index(str(INDEX_PATH))

    with open(DOCS_PATH, "rb") as f:
        docs = pickle.load(f)

    return index, docs


client = get_openai_client()


def get_embedding(text: str):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000]
    )
    return np.array(response.data[0].embedding).astype("float32")


def search_rag(query: str, top_k: int = 5):
    index, docs = load_rag()

    if client is None or index is None or not docs:
        return []

    query_vector = get_embedding(query)
    query_vector = np.array([query_vector]).astype("float32")

    distances, indices = index.search(query_vector, top_k)

    results = []

    for i in indices[0]:
        if 0 <= i < len(docs):
            results.append(docs[i])

    return results


def build_context(chunks):
    if not chunks:
        return "No hay documentos RAG disponibles para esta consulta."

    context = ""

    for i, chunk in enumerate(chunks, start=1):
        context += f"\n--- Documento {i} ---\n{chunk}\n"

    return context[:12000]


# =====================================================
# SESSION STATE
# =====================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hola Seba. Soy el SCA AI Engineering Assistant. "
                "Puedo ayudarte con ingeniería PLC/SCADA, licitaciones, "
                "cotizaciones técnicas, arquitectura industrial y análisis de documentos."
            )
        }
    ]

if "project_memory" not in st.session_state:
    st.session_state.project_memory = {
        "cliente": "",
        "planta": "",
        "sistema_actual": "",
        "sistema_objetivo": "",
        "alcance": "",
        "exclusiones": "",
    }


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.markdown(
        f"""
        <div class="sca-logo-box">
            {logo_html(215)}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="sca-section-title">▣ NAVEGACIÓN</div>', unsafe_allow_html=True)

    st.page_link("app.py", label="Inicio", icon="🏠")
    st.page_link("pages/1_Licitaciones.py", label="Licitaciones", icon="📑")
    st.page_link("pages/2_Generador_de_Cotizaciones.py", label="Generador de Cotizaciones", icon="💰")

    st.markdown('<div class="sca-section-title">▣ PANEL INDUSTRIAL</div>', unsafe_allow_html=True)

    cards = [
        ("🤖", "Asistente Proyecto desde Cero", "Crea proyectos industriales guiados paso a paso."),
        ("💬", "Chat Técnico", "Consulta técnica sobre PLC, SCADA, redes OT y automatización."),
        ("🏗️", "Arquitectura PLC/HMI", "Diseño conceptual de arquitecturas industriales."),
        ("💰", "Generador de Cotizaciones", "Cotiza migraciones PLC, SCADA, FAT, SAT y puesta en marcha."),
        ("📑", "Licitaciones", "Analiza bases técnicas, riesgos, alcance y preguntas faltantes."),
        ("📋", "Análisis Lista IO", "Revisión inteligente de señales, tags y arquitectura."),
    ]

    for icon, title, desc in cards:
        st.markdown(
            f"""
            <div class="sca-card">
                <b>{icon} {title}</b><br>
                <span style="font-size:12px;color:#9fbad8!important;">{desc}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


# =====================================================
# HERO
# =====================================================

col_top_1, col_top_2 = st.columns([2, 1])

with col_top_1:
    st.markdown("### Bienvenido al")
    st.markdown(
        """
        <div class="sca-title">
            SCA <span>AI Engineering Assistant</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="sca-subtitle">
            Plataforma industrial IA para ingeniería, licitaciones,
            PLC, SCADA, cotizaciones y automatización.
        </div>
        """,
        unsafe_allow_html=True
    )

with col_top_2:
    st.markdown(
        f"""
        <div style="text-align:right;margin-top:20px;">
            {logo_html(260)}
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")

st.markdown(
    """
    <div class="sca-hero">
        <div>
            <div style="font-size:42px;color:#00e5ff;">🧠</div>
            <h2>¿En qué puedo ayudarte hoy?</h2>
            <p style="color:#9fbad8!important;">
                Selecciona un módulo o consulta directamente al asistente industrial.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")


# =====================================================
# BOTONES PRINCIPALES
# =====================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.page_link(
        "pages/2_Generador_de_Cotizaciones.py",
        label="💰 Abrir Generador de Cotizaciones"
    )

with c2:
    st.page_link(
        "pages/1_Licitaciones.py",
        label="📑 Abrir Licitaciones"
    )

with c3:
    st.button("⚙️ Ingeniería PLC", disabled=True)

with c4:
    st.button("🖥️ SCADA / HMI", disabled=True)


# =====================================================
# ESTADO DEL MOTOR
# =====================================================

st.write("")

status_1, status_2, status_3 = st.columns(3)

with status_1:
    if client:
        st.success("OpenAI conectado")
    else:
        st.error("OpenAI no conectado")

with status_2:
    if INDEX_PATH.exists() and DOCS_PATH.exists():
        st.success("Motor RAG conectado")
    else:
        st.warning("RAG aún no indexado")

with status_3:
    st.info("Modo SCA Industrial")


# =====================================================
# CHAT + MEMORIA
# =====================================================

st.write("")
main_col, memory_col = st.columns([0.68, 0.32], gap="large")

with main_col:
    st.markdown("## 💬 Chat Técnico Industrial")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Consulta sobre PLC, SCADA, licitación, cotización o ingeniería...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if client is None:
                answer = (
                    "No encontré la API Key de OpenAI. "
                    "Debes configurarla en Streamlit Cloud Secrets o como variable de entorno OPENAI_API_KEY."
                )
                st.warning(answer)

            else:
                with st.spinner("Analizando contexto técnico..."):
                    chunks = search_rag(prompt)
                    context = build_context(chunks)

                    memory = st.session_state.project_memory

                    system_prompt = f"""
Eres SCA AI Engineering Assistant, un agente experto en automatización industrial,
PLC, SCADA, HMI, redes OT, licitaciones y cotizaciones técnicas.

Debes responder como ingeniero senior de automatización.

Reglas:
- Usa el contexto documental cuando esté disponible.
- Si falta información, pregunta solo el siguiente dato necesario.
- Ayuda a crear alcances, exclusiones, arquitectura, listas IO, propuestas,
  cotizaciones, FAT, SAT, puesta en marcha y migraciones.
- No inventes datos críticos.
- Mantén tono profesional, claro y práctico.

Memoria actual del proyecto:
Cliente: {memory["cliente"]}
Planta / Área: {memory["planta"]}
Sistema actual: {memory["sistema_actual"]}
Sistema objetivo: {memory["sistema_objetivo"]}
Alcance preliminar: {memory["alcance"]}
Exclusiones: {memory["exclusiones"]}

Contexto documental RAG:
{context}
"""

                    response = client.chat.completions.create(
                        model=CHAT_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *st.session_state.messages[-12:]
                        ],
                        temperature=0.25
                    )

                    answer = response.choices[0].message.content
                    st.markdown(answer)

            st.session_state.messages.append({"role": "assistant", "content": answer})


with memory_col:
    st.markdown("## 🧠 Memoria del Proyecto")

    st.session_state.project_memory["cliente"] = st.text_input(
        "Cliente",
        st.session_state.project_memory["cliente"]
    )

    st.session_state.project_memory["planta"] = st.text_input(
        "Planta / Área",
        st.session_state.project_memory["planta"]
    )

    st.session_state.project_memory["sistema_actual"] = st.text_input(
        "Sistema actual",
        st.session_state.project_memory["sistema_actual"]
    )

    st.session_state.project_memory["sistema_objetivo"] = st.text_input(
        "Sistema objetivo",
        st.session_state.project_memory["sistema_objetivo"]
    )

    st.session_state.project_memory["alcance"] = st.text_area(
        "Alcance preliminar",
        st.session_state.project_memory["alcance"],
        height=120
    )

    st.session_state.project_memory["exclusiones"] = st.text_area(
        "Exclusiones",
        st.session_state.project_memory["exclusiones"],
        height=120
    )

    if st.button("🧹 Limpiar chat", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Chat reiniciado. ¿Qué proyecto industrial revisamos ahora?"
            }
        ]
        st.rerun()


# =====================================================
# FOOTER
# =====================================================

st.markdown(
    """
    <div class="sca-footer">
        <b style="color:#00e5ff;">SCA Ingeniería y Automatización</b>
        &nbsp;•&nbsp; Todos los derechos reservados
        &nbsp;•&nbsp; 2026
    </div>
    """,
    unsafe_allow_html=True
)


