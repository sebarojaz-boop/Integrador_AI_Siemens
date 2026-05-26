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

load_dotenv()

api_key = None

try:
    api_key = st.secrets.get("OPENAI_API_KEY", None)
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("No se encontró OPENAI_API_KEY")
    st.stop()

client = OpenAI(api_key=api_key)

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


@st.cache_resource
def init_rag():
    return load_knowledge()


def ask_ai(user_input, extra_context=""):

    context = search(user_input, index, chunks, k=5)
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


st.set_page_config(
    page_title="Siemens AI Engineer",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at top left, rgba(0,245,255,0.18), transparent 35%),
        radial-gradient(circle at bottom right, rgba(37,99,235,0.16), transparent 40%),
        linear-gradient(135deg, #050B14 0%, #07111F 45%, #0F172A 100%);
    color: #F8FAFC;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0F172A 100%);
    border-right: 1px solid rgba(0,245,255,0.25);
}

h1 {
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    color: #F8FAFC;
    text-shadow: 0 0 18px rgba(0,245,255,0.35);
}

h2, h3 {
    color: #E2E8F0;
}

.stButton > button {
    width: 100%;
    border-radius: 14px;
    border: 1px solid rgba(0,245,255,0.45);
    background: linear-gradient(90deg, #0F172A, #1E293B);
    color: #F8FAFC;
    font-weight: 700;
    box-shadow: 0 0 12px rgba(0,245,255,0.10);
    transition: all 0.2s ease-in-out;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #00F5FF, #2563EB);
    color: #020617;
    transform: translateY(-2px);
    box-shadow: 0 0 22px rgba(0,245,255,0.45);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    border-bottom: 1px solid rgba(0,245,255,0.2);
}

.stTabs [data-baseweb="tab"] {
    background: rgba(15,23,42,0.85);
    border: 1px solid rgba(148,163,184,0.15);
    border-radius: 14px 14px 0 0;
    padding: 12px 20px;
    color: #CBD5E1;
    font-weight: 700;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #00F5FF, #38BDF8) !important;
    color: #020617 !important;
}

[data-testid="stChatMessage"] {
    background: rgba(15, 23, 42, 0.88);
    border: 1px solid rgba(0,245,255,0.18);
    border-radius: 20px;
    padding: 1.1rem;
    margin-bottom: 1rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}

.stChatInput {
    position: fixed !important;
    bottom: 20px;
    left: 320px;
    right: 30px;
    background: rgba(2,6,23,0.96);
    padding: 14px;
    z-index: 999999;
    border-top: 1px solid rgba(0,245,255,0.25);
    box-shadow: 0 -8px 24px rgba(0,0,0,0.35);
}

.main .block-container {
    padding-bottom: 160px;
}

div[data-testid="stMetric"] {
    background: rgba(15,23,42,0.9);
    border: 1px solid rgba(0,245,255,0.22);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 8px 22px rgba(0,0,0,0.25);
}

.stAlert {
    border-radius: 16px;
    border: 1px solid rgba(0,245,255,0.22);
}

input, textarea {
    border-radius: 14px !important;
}

hr {
    border-color: rgba(0,245,255,0.18);
}

#chat-bottom {
    height: 1px;
}

</style>
""", unsafe_allow_html=True)

st.title("🧠 Siemens AI Engineering Assistant")

st.write(
    """
Asistente guiado para crear proyectos Siemens desde cero en TIA Portal.
"""
)

with st.spinner("Cargando base Siemens..."):
    index, chunks = init_rag()

if index is None or chunks is None:
    st.error("No se pudo cargar la base Siemens.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

if "prefill" not in st.session_state:
    st.session_state.prefill = ""

project = load_project()

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

tab_chat, tab_project, tab_tools = st.tabs(
    [
        "💬 Chat",
        "🏭 Proyecto Guiado",
        "🧰 Herramientas"
    ]
)

with tab_project:

    st.subheader("🏭 Proyecto Siemens desde Cero")

    st.write(
        """
Sube documentos o completa la información del proyecto.
El asistente irá preguntando automáticamente lo que falta.
"""
    )

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

    st.markdown('<div id="chat-bottom"></div>', unsafe_allow_html=True)

    st.markdown("""
    <script>
    setTimeout(function() {
        const elements = window.parent.document.querySelectorAll('[id="chat-bottom"]');
        if (elements.length > 0) {
            elements[elements.length - 1].scrollIntoView({
                behavior: "smooth",
                block: "end"
            });
        }
    }, 500);
    </script>
    """, unsafe_allow_html=True)