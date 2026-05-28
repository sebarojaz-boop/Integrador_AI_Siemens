import os
import base64
import pickle
from pathlib import Path

import streamlit as st

try:
    import faiss
    import numpy as np
except Exception:
    faiss = None
    np = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# =====================================================
# CONFIG GENERAL
# =====================================================

st.set_page_config(
    page_title="SCA AI Engineering Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent

CSS_PATH = APP_DIR / "styles" / "sca_theme.css"
LOGO_PATH = APP_DIR / "assets" / "sca_logo.svg"

INDEX_PATH = ROOT_DIR / "faiss_index.bin"
DOCS_PATH = ROOT_DIR / "docs.pkl"

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"


# =====================================================
# CARGA CSS / LOGO
# =====================================================

if CSS_PATH.exists():
    st.markdown(
        f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

logo_base64 = ""

if LOGO_PATH.exists():
    logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()


def logo_html(width=190):
    if not logo_base64:
        return "<div class='fallback-logo'>SCA</div>"
    return f'<img src="data:image/svg+xml;base64,{logo_base64}" width="{width}">'


# =====================================================
# OPENAI / RAG
# =====================================================

@st.cache_resource(show_spinner=False)
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


@st.cache_resource(show_spinner=False)
def load_rag():
    if faiss is None:
        return None, []

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
        input=text[:8000],
    )
    return np.array(response.data[0].embedding).astype("float32")


def search_rag(query: str, top_k: int = 5):
    index, docs = load_rag()

    if client is None or index is None or not docs or np is None:
        return []

    query_vector = get_embedding(query)
    query_vector = np.array([query_vector]).astype("float32")

    _, indices = index.search(query_vector, top_k)

    results = []

    for i in indices[0]:
        if 0 <= i < len(docs):
            results.append(docs[i])

    return results


def build_context(chunks):
    if not chunks:
        return "No hay contexto documental RAG disponible."

    context = ""

    for i, chunk in enumerate(chunks, start=1):
        context += f"\n--- Documento {i} ---\n{chunk}\n"

    return context[:12000]


def ai_response(user_prompt: str, module_context: str = ""):
    if client is None:
        return (
            "OpenAI no está conectado. Configura `OPENAI_API_KEY` en Streamlit Secrets "
            "o como variable de entorno local."
        )

    chunks = search_rag(user_prompt)
    context = build_context(chunks)

    memory = st.session_state.project_memory

    system_prompt = f"""
Eres SCA AI Engineering Assistant, un agente senior de automatización industrial.

Especialidades:
- PLC Siemens TIA Portal
- Rockwell / Allen-Bradley Studio 5000
- SCADA / HMI
- Ignition
- AVEVA / System Platform
- WinCC
- FactoryTalk
- Licitaciones industriales
- Cotizaciones técnicas
- Arquitectura OT
- Listados IO
- Ingeniería de control

Reglas:
- Responde como ingeniero senior.
- Si falta información, pregunta el siguiente dato necesario.
- No inventes datos críticos.
- Mantén respuestas prácticas, profesionales y accionables.
- Usa el contexto documental RAG si existe.
- Mantén continuidad con la memoria del proyecto.

Módulo actual:
{module_context}

Memoria del proyecto:
Cliente: {memory.get("cliente", "")}
Planta: {memory.get("planta", "")}
Sistema actual: {memory.get("sistema_actual", "")}
Sistema objetivo: {memory.get("sistema_objetivo", "")}
Alcance: {memory.get("alcance", "")}
Exclusiones: {memory.get("exclusiones", "")}

Contexto RAG:
{context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.chat_messages[-10:])
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.25,
    )

    return response.choices[0].message.content


# =====================================================
# SESSION STATE
# =====================================================

if "active_module" not in st.session_state:
    st.session_state.active_module = "home"

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "content": (
                "Hola Seba. Soy SCA AI Engineering Assistant. "
                "Puedo ayudarte con PLC, SCADA, licitaciones, cotizaciones, IO, arquitectura OT e ingeniería de control."
            ),
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
# UI HELPERS
# =====================================================

MODULES = {
    "cotizaciones": {
        "icon": "📄",
        "title": "Generación de Cotizaciones",
        "desc": "Genera cotizaciones técnicas y económicas para proyectos industriales.",
        "color": "cyan",
    },
    "licitaciones": {
        "icon": "📋",
        "title": "Evaluación de Licitaciones",
        "desc": "Analiza bases técnicas, riesgos, alcance, preguntas y factibilidad.",
        "color": "purple",
    },
    "siemens": {
        "icon": "SIEMENS",
        "title": "Generar Programa Siemens",
        "desc": "Genera estructuras base para PLC Siemens TIA Portal.",
        "color": "green",
    },
    "rockwell": {
        "icon": "AB",
        "title": "Generar Programa Rockwell",
        "desc": "Genera lógica base para Rockwell / Allen-Bradley Studio 5000.",
        "color": "red",
    },
    "chat": {
        "icon": "💬",
        "title": "Chat Técnico",
        "desc": "Consulta técnica industrial con IA y contexto documental.",
        "color": "blue",
    },
    "io": {
        "icon": "I/O",
        "title": "Análisis Listado IO",
        "desc": "Analiza señales, tags, arquitectura, criticidad y omisiones.",
        "color": "cyan",
    },
    "scada": {
        "icon": "🖥️",
        "title": "Análisis de SCADA y HMI",
        "desc": "Evalúa pantallas, arquitectura, tags, alarmas y plataformas SCADA.",
        "color": "blue",
    },
    "control": {
        "icon": "⚙️",
        "title": "Desarrollo Ingeniería de Control",
        "desc": "Genera alcances, filosofía de control, arquitectura y documentación.",
        "color": "yellow",
    },
}


def set_module(module_key):
    st.session_state.active_module = module_key
    st.rerun()


def module_button(module_key):
    item = MODULES[module_key]

    if st.button(
        f"{item['icon']}  {item['title']}",
        key=f"btn_{module_key}",
        use_container_width=True,
    ):
        set_module(module_key)

    st.markdown(
        f"""
        <div class="module-card {item['color']}">
            <div class="module-icon">{item['icon']}</div>
            <h3>{item['title']}</h3>
            <p>{item['desc']}</p>
            <div class="module-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_item(module_key, label=None):
    item = MODULES[module_key]
    active = "active" if st.session_state.active_module == module_key else ""

    if st.button(
        f"{item['icon']}  {label or item['title']}",
        key=f"side_{module_key}",
        use_container_width=True,
    ):
        set_module(module_key)

    st.markdown(f"<div class='side-marker {active}'></div>", unsafe_allow_html=True)


def section_title(title, subtitle=""):
    st.markdown(
        f"""
        <div class="section-head">
            <h2>{title}</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def ai_work_area(module_key, prompt_template, input_label="Describe el requerimiento"):
    module = MODULES[module_key]

    section_title(module["title"], module["desc"])

    user_text = st.text_area(
        input_label,
        height=170,
        placeholder=prompt_template,
        key=f"text_{module_key}",
    )

    col_a, col_b = st.columns([1, 1])

    with col_a:
        generate = st.button(
            f"🚀 Ejecutar {module['title']}",
            key=f"run_{module_key}",
            use_container_width=True,
        )

    with col_b:
        clear = st.button(
            "🧹 Limpiar",
            key=f"clear_{module_key}",
            use_container_width=True,
        )

    if clear:
        st.session_state[f"text_{module_key}"] = ""
        st.rerun()

    if generate:
        if not user_text.strip():
            st.warning("Ingresa información del proyecto para generar el análisis.")
        else:
            with st.spinner("Procesando con SCA AI Engineering Assistant..."):
                result = ai_response(user_text, module["title"])

            st.markdown("### Resultado")
            st.markdown(result)


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-logo">
            {logo_html(175)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-section">MÓDULOS PRINCIPALES</div>', unsafe_allow_html=True)

    if st.button("🏠  Inicio", use_container_width=True):
        set_module("home")

    for key in MODULES:
        sidebar_item(key)

    st.markdown('<div class="side-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-section">SUBCATEGORÍAS INDUSTRIALES</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="platform-list">
            <div><b class="green">SIEMENS</b><span>TIA Portal · WinCC</span></div>
            <div><b class="red">ROCKWELL</b><span>Studio 5000 · FTView</span></div>
            <div><b class="purple">AVEVA</b><span>System Platform · InTouch</span></div>
            <div><b class="orange">IGNITION</b><span>Perspective · Vision</span></div>
            <div><b class="blue">SCHNEIDER</b><span>EcoStruxure</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="version-card">
            <div class="pulse-icon">⌁</div>
            <div>
                <b>SCA AI Engineering Assistant</b><br>
                <span>Industrial AI · V1 Final Base</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================
# HEADER
# =====================================================

st.markdown(
    """
    <div class="top-status">
        <span></span> Online
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-header">
        <div class="welcome">Bienvenido a</div>
        <h1>SCA <span>AI</span> Engineering Assistant</h1>
        <p>Plataforma industrial IA para ingeniería, licitaciones, PLC, SCADA, cotizaciones y automatización.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# HOME
# =====================================================

if st.session_state.active_module == "home":
    row1 = st.columns(4, gap="medium")
    row2 = st.columns(4, gap="medium")

    keys = list(MODULES.keys())

    for col, key in zip(row1, keys[:4]):
        with col:
            module_button(key)

    for col, key in zip(row2, keys[4:]):
        with col:
            module_button(key)

    st.markdown(
        """
        <div class="bottom-status">
            <div>
                <span class="status-icon purple">▣</span>
                <p>Modelos IA</p>
                <b>OpenAI conectado si existe API Key</b>
            </div>
            <div>
                <span class="status-icon cyan">◎</span>
                <p>Base de Conocimiento</p>
                <b>RAG preparado</b>
            </div>
            <div>
                <span class="status-icon green">盾</span>
                <p>Entorno</p>
                <b>Industrial / OT</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================
# MODULOS FUNCIONALES
# =====================================================

elif st.session_state.active_module == "cotizaciones":
    ai_work_area(
        "cotizaciones",
        "Ejemplo: migración de SCADA FactoryTalk a Ignition, 120 señales IO, 6 pantallas, PLC Allen-Bradley, FAT/SAT y puesta en marcha.",
        "Describe el proyecto a cotizar",
    )

elif st.session_state.active_module == "licitaciones":
    ai_work_area(
        "licitaciones",
        "Pega aquí el texto de las bases técnicas, alcance, requisitos, visita a terreno, plazos, multas y criterios de evaluación.",
        "Pega o resume la licitación",
    )

elif st.session_state.active_module == "siemens":
    ai_work_area(
        "siemens",
        "Ejemplo: necesito generar estructura Siemens TIA Portal para 4 motores, 6 válvulas, secuencia automática, alarmas y DB global.",
        "Describe la lógica Siemens a generar",
    )

elif st.session_state.active_module == "rockwell":
    ai_work_area(
        "rockwell",
        "Ejemplo: necesito generar lógica Rockwell Studio 5000 para motores, AOI, tags, secuencia, alarmas y estructura base.",
        "Describe la lógica Rockwell a generar",
    )

elif st.session_state.active_module == "io":
    ai_work_area(
        "io",
        "Pega aquí el listado IO o describe señales digitales, analógicas, instrumentos, válvulas, motores y tableros.",
        "Pega o describe el listado IO",
    )

elif st.session_state.active_module == "scada":
    ai_work_area(
        "scada",
        "Describe pantallas, tags, alarmas, históricos, tendencias, usuarios, arquitectura servidor/cliente y plataforma: AVEVA, Ignition, WinCC o FactoryTalk.",
        "Describe el sistema SCADA/HMI",
    )

elif st.session_state.active_module == "control":
    ai_work_area(
        "control",
        "Describe el proceso, equipos, modos de operación, enclavamientos, alarmas, arquitectura PLC/HMI y documentación requerida.",
        "Describe la ingeniería de control requerida",
    )

elif st.session_state.active_module == "chat":
    section_title("Chat Técnico Industrial", "Consulta directa con IA industrial y contexto RAG.")

    chat_col, memory_col = st.columns([0.68, 0.32], gap="large")

    with chat_col:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Consulta técnica sobre PLC, SCADA, licitaciones, IO o cotizaciones...")

        if prompt:
            st.session_state.chat_messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analizando..."):
                    answer = ai_response(prompt, "Chat Técnico Industrial")
                st.markdown(answer)

            st.session_state.chat_messages.append({"role": "assistant", "content": answer})

    with memory_col:
        st.markdown("### 🧠 Memoria del Proyecto")

        st.session_state.project_memory["cliente"] = st.text_input(
            "Cliente",
            st.session_state.project_memory["cliente"],
        )

        st.session_state.project_memory["planta"] = st.text_input(
            "Planta / Área",
            st.session_state.project_memory["planta"],
        )

        st.session_state.project_memory["sistema_actual"] = st.text_input(
            "Sistema actual",
            st.session_state.project_memory["sistema_actual"],
        )

        st.session_state.project_memory["sistema_objetivo"] = st.text_input(
            "Sistema objetivo",
            st.session_state.project_memory["sistema_objetivo"],
        )

        st.session_state.project_memory["alcance"] = st.text_area(
            "Alcance",
            st.session_state.project_memory["alcance"],
            height=90,
        )

        st.session_state.project_memory["exclusiones"] = st.text_area(
            "Exclusiones",
            st.session_state.project_memory["exclusiones"],
            height=90,
        )

        if st.button("🧹 Limpiar chat", use_container_width=True):
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": "Chat reiniciado. ¿Qué proyecto industrial revisamos ahora?",
                }
            ]
            st.rerun()