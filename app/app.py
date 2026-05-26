import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from rag_engine import load_knowledge, search

from tools.io_analyzer import analyze_io_list
from tools.tia_generator import generate_tia_tags, generate_base_st_program
from tools.engineering_package import generate_engineering_package
from tools.machine_builder import build_machine_architecture
from tools.document_loader import process_uploaded_files

from tools.project_wizard import (
    load_project,
    save_project,
    reset_project,
    project_completion,
    missing_questions,
    next_question,
    generate_project_context_text,
    generate_project_brief_file,
    auto_fill_project_from_text
)

from memory_store import (
    load_chat_history,
    save_chat_history,
    clear_chat_history
)

# =========================
# OPENAI
# =========================
load_dotenv()

api_key = None

try:
    api_key = st.secrets.get("OPENAI_API_KEY", None)
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Falta configurar OPENAI_API_KEY.")
    st.stop()

client = OpenAI(api_key=api_key)

# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = """
Eres un Ingeniero Senior Siemens experto en crear proyectos desde cero en TIA Portal.

Debes ayudar paso a paso al usuario con:
- levantamiento de información
- lista IO
- instrumentación
- actuadores
- arquitectura PLC/HMI
- filosofía de control
- comunicación industrial
- seguridad
- alarmas
- programación Siemens
- estructura OB FB FC DB UDT
- TIA Portal

Reglas:
- Responde siempre en español.
- Si falta información, pregunta SOLO la siguiente información más importante.
- Explica por qué necesitas esa información.
- Explica cómo se usará después en TIA Portal.
- Guía al usuario como si NO supiera TIA Portal.
- Explica dónde hacer click.
- Explica qué bloque crear.
- Explica dónde pegar código.
- Prioriza seguridad industrial.
"""


# =========================
# RAG
# =========================
@st.cache_resource
def init_rag():
    return load_knowledge()


def ask_ai(user_input, extra_context=""):

    context = search(
        user_input,
        index,
        chunks,
        k=5
    )

    context_text = "\n\n".join(context)

    history_text = "\n".join(
        [
            f'{m["role"]}: {m["content"]}'
            for m in st.session_state.messages[-6:]
        ]
    )

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=
        SYSTEM_PROMPT
        + "\n\n=== MANUALES SIEMENS ===\n"
        + context_text
        + "\n\n=== CONTEXTO PROYECTO ===\n"
        + extra_context
        + "\n\n=== HISTORIAL ===\n"
        + history_text
        + "\n\n=== CONSULTA ===\n"
        + user_input
    )

    return response.output_text, context_text


# =========================
# PAGE
# =========================
st.set_page_config(
    page_title="Siemens AI Engineer",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>

.stChatInput {
    position: fixed !important;
    bottom: 20px;
    left: 320px;
    right: 30px;
    background-color: #0e1117;
    padding-top: 10px;
    z-index: 999999;
}

.main .block-container {
    padding-bottom: 150px;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

[data-testid="stChatMessage"] {
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
}

</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================
st.title("🧠 Siemens AI Engineering Assistant")

st.write(
    """
Asistente guiado para crear proyectos Siemens desde cero en TIA Portal.
"""
)

# =========================
# LOAD KB
# =========================
with st.spinner("Cargando base Siemens..."):

    index, chunks = init_rag()

if index is None or chunks is None:

    st.error("No se pudo cargar la base Siemens.")
    st.stop()

# =========================
# SESSION
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

if "prefill" not in st.session_state:
    st.session_state.prefill = ""

# =========================
# PROJECT
# =========================
project = load_project()

# =========================
# SIDEBAR
# =========================
with st.sidebar:

    st.header("⚙️ Panel Industrial")

    mostrar_contexto = st.checkbox(
        "Mostrar contexto usado",
        value=False
    )

    modo = st.radio(
        "Modo de trabajo",
        [
            "Asistente Proyecto desde Cero",
            "Chat técnico",
            "Arquitectura PLC/HMI",
            "Generador Tags TIA",
            "Generador Programa TIA",
            "Paquete Ingeniería TIA",
            "Arquitecto TIA Portal",
            "Diagnóstico PLC",
            "Diagnóstico Profinet",
            "Análisis Lista IO"
        ]
    )

    st.divider()

    avance = project_completion(project)

    st.metric(
        "Avance proyecto",
        f"{avance}%"
    )

    st.progress(avance / 100)

    st.caption("Siguiente información requerida:")

    st.warning(
        next_question(project)
    )

    if st.button("🧹 Limpiar conversación"):

        st.session_state.messages = []

        clear_chat_history()

        st.rerun()

    if st.button("♻️ Reiniciar proyecto guiado"):

        reset_project()

        st.rerun()

    st.info("PDFs Siemens → knowledge_base")
    st.info("Documentos → data/uploaded_docs")
    st.info("Output → output")

# =========================
# TABS
# =========================
tab_chat, tab_project, tab_tools = st.tabs(
    [
        "💬 Chat",
        "🏭 Proyecto Guiado",
        "🧰 Herramientas"
    ]
)

# =========================================================
# TAB PROJECT
# =========================================================
with tab_project:

    st.subheader("🏭 Proyecto Siemens desde Cero")

    st.write(
        """
Sube documentos o completa la información del proyecto.
El asistente irá preguntando automáticamente lo que falta.
"""
    )

    # =========================
    # UPLOAD
    # =========================
    st.divider()

    st.subheader("📎 Subir documentos")

    uploaded_files = st.file_uploader(
        """
Sube:
- Excel Lista IO
- Filosofía de control
- PDF ingeniería
- Instrumentación
- Arquitectura
- Memorias
- Word
- CSV
""",
        type=["pdf", "xlsx", "xls", "docx", "txt", "csv"],
        accept_multiple_files=True
    )

    if st.button("📥 Procesar documentos subidos"):

        if uploaded_files:

            docs_context = process_uploaded_files(
                uploaded_files
            )

            updated_project = auto_fill_project_from_text(
                docs_context
            )

            prompt = """
Analiza los documentos y el proyecto auto-rellenado.

Entrega:
1. Qué información identificaste.
2. Qué información quedó clara.
3. Qué información falta.
4. Haz SOLO la siguiente pregunta más importante.
5. Explica cómo esa información se usará en TIA Portal.
"""

            project_context = generate_project_context_text(
                updated_project
            )

            with st.spinner(
                "Analizando documentos..."
            ):

                answer, context_text = ask_ai(
                    prompt,
                    project_context
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            save_chat_history(
                st.session_state.messages
            )

            st.success(
                "Documentos procesados y proyecto auto-rellenado."
            )

            st.rerun()

        else:

            st.warning(
                "Primero sube uno o más documentos."
            )

    # =========================
    # FORM
    # =========================
    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        project["project_name"] = st.text_input(
            "Nombre proyecto",
            value=project.get("project_name", "")
        )

        project["plant_description"] = st.text_area(
            "Descripción planta",
            value=project.get("plant_description", ""),
            height=120
        )

        project["process_type"] = st.text_input(
            "Tipo proceso",
            value=project.get("process_type", "")
        )

        project["control_objective"] = st.text_area(
            "Objetivo control",
            value=project.get("control_objective", ""),
            height=100
        )

        project["io_available"] = st.text_area(
            "Lista IO",
            value=project.get("io_available", ""),
            height=120
        )

    with col2:

        project["instruments"] = st.text_area(
            "Instrumentos",
            value=project.get("instruments", ""),
            height=120
        )

        project["motors_actuators"] = st.text_area(
            "Motores / actuadores",
            value=project.get("motors_actuators", ""),
            height=120
        )

        project["communication"] = st.text_area(
            "Comunicación",
            value=project.get("communication", ""),
            height=120
        )

        project["hmi_requirements"] = st.text_area(
            "HMI",
            value=project.get("hmi_requirements", ""),
            height=120
        )

        project["safety_requirements"] = st.text_area(
            "Seguridad",
            value=project.get("safety_requirements", ""),
            height=120
        )

    project["control_philosophy"] = st.text_area(
        "Filosofía control",
        value=project.get("control_philosophy", ""),
        height=140
    )

    if st.button("💾 Guardar proyecto"):

        save_project(project)

        st.success("Proyecto guardado.")

        st.rerun()

    # =========================
    # QUESTIONS
    # =========================
    st.divider()

    st.subheader("❓ Información faltante")

    questions = missing_questions(
        load_project()
    )

    if questions:

        for q in questions:
            st.warning(q)

    else:

        st.success(
            "Información mínima completa."
        )

    # =========================
    # BRIEF
    # =========================
    if st.button("📄 Generar Brief Proyecto"):

        path, content = generate_project_brief_file()

        st.success("Brief generado.")

        with open(path, "rb") as f:

            st.download_button(
                label="⬇️ Descargar Brief",
                data=f,
                file_name="Brief_Proyecto_Siemens.txt",
                mime="text/plain"
            )

    # =========================
    # NEXT STEPS
    # =========================
    if st.button("🧠 Preguntar siguiente información necesaria"):

        context_project = generate_project_context_text(
            load_project()
        )

        prompt = """
Actúa como ingeniero Siemens senior guiando el levantamiento de información.

Debes:
1. Revisar información actual.
2. Identificar qué falta.
3. Preguntar SOLO el siguiente dato más importante.
4. Explicar por qué es importante.
5. Explicar cómo se usará en TIA Portal.
"""

        with st.spinner(
            "Analizando proyecto..."
        ):

            answer, context_text = ask_ai(
                prompt,
                context_project
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        save_chat_history(
            st.session_state.messages
        )

        st.rerun()

# =========================================================
# TAB TOOLS
# =========================================================
with tab_tools:

    st.subheader("🧰 Herramientas")

    if st.button("📊 Analizar Lista IO"):

        io_context = analyze_io_list()

        prompt = """
Analiza esta Lista IO.

Entrega:
1. Entradas
2. Salidas
3. Instrumentos
4. Arquitectura PLC
5. Alarmas
6. Riesgos
7. Próximos pasos
"""

        answer, context_text = ask_ai(
            prompt,
            io_context
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        save_chat_history(
            st.session_state.messages
        )

        st.rerun()

    if st.button("🏷️ Generar Tags TIA"):

        output_path, summary = generate_tia_tags()

        if output_path:

            st.success("Tags generados.")

            with open(output_path, "rb") as f:

                st.download_button(
                    label="⬇️ Descargar Tags",
                    data=f,
                    file_name="TIA_Tags_Generados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    if st.button("⚙️ Generar Programa ST"):

        output_path, st_code = generate_base_st_program()

        st.success("Programa generado.")

        st.code(
            st_code,
            language="pascal"
        )

    if st.button("📦 Generar Paquete Ingeniería"):

        files, summary = generate_engineering_package()

        st.success("Paquete generado.")

        for file_path in files:

            filename = os.path.basename(file_path)

            with open(file_path, "rb") as f:

                st.download_button(
                    label=f"⬇️ {filename}",
                    data=f,
                    file_name=filename,
                    mime="application/octet-stream"
                )

    if st.button("🏗️ Arquitecto TIA ZIP"):

        zip_path, files = build_machine_architecture()

        st.success("ZIP generado.")

        with open(zip_path, "rb") as f:

            st.download_button(
                label="⬇️ Descargar ZIP",
                data=f,
                file_name="TIA_Architecture_Package.zip",
                mime="application/zip"
            )

# =========================================================
# TAB CHAT
# =========================================================
with tab_chat:

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):

            st.write(msg["content"])

    user_input = st.chat_input(
        "Describe tu planta o consulta Siemens..."
    )

    if user_input:

        context_project = generate_project_context_text(
            load_project()
        )

        final_input = f"""
Modo seleccionado:
{modo}

Consulta:
{user_input}

Si faltan datos:
- pide SOLO el siguiente dato más importante
- explica por qué lo necesitas
- explica cómo se usará en TIA Portal
"""

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        save_chat_history(
            st.session_state.messages
        )

        with st.chat_message("user"):

            st.write(user_input)

        with st.chat_message("assistant"):

            with st.spinner(
                "Analizando ingeniería..."
            ):

                answer, context_text = ask_ai(
                    final_input,
                    context_project
                )

                st.write(answer)

                if mostrar_contexto:

                    with st.expander(
                        "📚 Contexto usado"
                    ):

                        st.write(context_text)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        save_chat_history(
            st.session_state.messages
        )