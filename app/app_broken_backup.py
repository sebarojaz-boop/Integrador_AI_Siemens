import os
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

# =========================================================
# CONFIG BASE
# =========================================================

APP_NAME = "SCA AI Engineering Assistant"
APP_VERSION = "V1.0 Multimarca"
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"

OUTPUT_DIR.mkdir(exist_ok=True)
KNOWLEDGE_DIR.mkdir(exist_ok=True)

sys.path.append(str(BASE_DIR))

# =========================================================
# IMPORTS SEGUROS
# =========================================================

rag_ready = False
memory_ready = False

try:
    from app.rag_engine import ask_rag
    rag_ready = True
except Exception as e:
    rag_error = str(e)

try:
    from app.memory_store import save_memory, load_memory
    memory_ready = True
except Exception as e:
    memory_error = str(e)

# =========================================================
# STREAMLIT CONFIG
# =========================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CSS INDUSTRIAL FUTURISTA
# =========================================================

st.markdown("""
<style>
:root {
    --bg-main: #020812;
    --bg-panel: #071827;
    --bg-panel-2: #0b2235;
    --cyan: #00e5ff;
    --cyan-soft: #00e5ff44;
    --text-main: #ffffff;
    --text-muted: #9fb7c9;
    --green: #00ff99;
    --yellow: #ffc857;
    --red: #ff4d6d;
}

html, body, [class*="css"] {
    background-color: var(--bg-main);
    color: var(--text-main);
    font-family: 'Segoe UI', sans-serif;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 6rem;
    max-width: 1450px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #031524 0%, #020812 100%);
    border-right: 1px solid var(--cyan-soft);
}

.main-title {
    font-size: 44px;
    font-weight: 900;
    color: white;
    text-shadow: 0 0 16px #00e5ff55;
    margin-bottom: 0px;
}

.subtitle {
    font-size: 17px;
    color: #8fdfff;
    margin-top: 6px;
    margin-bottom: 30px;
}

.glass-card {
    background: linear-gradient(145deg, #071827 0%, #07111f 100%);
    border: 1px solid #00e5ff33;
    border-radius: 18px;
    padding: 24px;
    box-shadow: 0 0 28px #00e5ff10;
    margin-bottom: 18px;
}

.metric-card {
    background: #061522;
    border: 1px solid #00e5ff30;
    border-radius: 16px;
    padding: 18px;
    min-height: 110px;
}

.metric-title {
    color: #9fb7c9;
    font-size: 13px;
}

.metric-value {
    color: white;
    font-size: 26px;
    font-weight: 800;
}

.status-ok {
    color: #00ff99;
    font-weight: 700;
}

.status-warn {
    color: #ffc857;
    font-weight: 700;
}

.status-error {
    color: #ff4d6d;
    font-weight: 700;
}

.stButton > button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 800;
    padding: 0.55rem 1rem;
}

.stButton > button:hover {
    box-shadow: 0 0 18px #00e5ff80;
    color: white;
}

textarea, input {
    background-color: #071827 !important;
    color: white !important;
    border: 1px solid #00e5ff44 !important;
    border-radius: 10px !important;
}

div[data-testid="stFileUploader"] {
    background-color: #061522;
    border: 1px dashed #00e5ff66;
    border-radius: 14px;
    padding: 12px;
}

hr {
    border-color: #00e5ff22;
}

.small-muted {
    color: #9fb7c9;
    font-size: 13px;
}

.mode-box {
    background: #061522;
    border: 1px solid #00e5ff22;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}

.footer-space {
    height: 80px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "project_memory" not in st.session_state:
    st.session_state.project_memory = {
        "project_name": "",
        "client": "",
        "plant": "",
        "process": "",
        "plc_brand": "",
        "scada": "",
        "network": "",
        "io_count": "",
        "documents": [],
        "missing": [
            "Nombre del proyecto o planta",
            "Cliente",
            "Proceso industrial",
            "Marca PLC preferida",
            "SCADA/HMI requerido",
            "Cantidad aproximada de señales IO",
            "Red industrial requerida"
        ]
    }

if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "Asistente Proyecto desde Cero"

# =========================================================
# FUNCIONES
# =========================================================

def get_api_key():
    try:
        return st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return os.getenv("OPENAI_API_KEY", "")


def save_uploaded_files(uploaded_files):
    saved = []

    if not uploaded_files:
        return saved

    upload_dir = OUTPUT_DIR / "uploaded_docs"
    upload_dir.mkdir(exist_ok=True)

    for file in uploaded_files:
        safe_name = file.name.replace(" ", "_")
        path = upload_dir / safe_name

        with open(path, "wb") as f:
            f.write(file.getbuffer())

        saved.append(str(path))
        st.session_state.project_memory["documents"].append(file.name)

    return saved


def calculate_progress():
    memory = st.session_state.project_memory
    fields = [
        "project_name",
        "client",
        "plant",
        "process",
        "plc_brand",
        "scada",
        "network",
        "io_count"
    ]

    completed = sum(1 for f in fields if str(memory.get(f, "")).strip())
    return int((completed / len(fields)) * 100)


def next_missing_info():
    memory = st.session_state.project_memory

    checks = [
        ("project_name", "¿Cómo se llama el proyecto o planta?"),
        ("client", "¿Quién es el cliente final?"),
        ("plant", "¿En qué planta o área se implementará?"),
        ("process", "¿Qué proceso industrial controla el sistema?"),
        ("plc_brand", "¿Qué marca de PLC se usará? Siemens, Rockwell, Schneider, ABB u otra."),
        ("scada", "¿Qué SCADA/HMI se requiere? Ignition, WinCC, FactoryTalk, AVEVA u otro."),
        ("io_count", "¿Cuántas señales IO aproximadas tiene el proyecto?"),
        ("network", "¿Qué red industrial se usará? Profinet, Ethernet/IP, Modbus TCP, Profibus, etc.")
    ]

    for key, question in checks:
        if not str(memory.get(key, "")).strip():
            return question

    return "El proyecto tiene información base suficiente para generar ingeniería inicial."


def simple_project_autofill(text):
    text_lower = text.lower()
    memory = st.session_state.project_memory

    brands = {
        "siemens": "Siemens",
        "tia": "Siemens TIA Portal",
        "rockwell": "Allen-Bradley / Rockwell",
        "allen": "Allen-Bradley / Rockwell",
        "studio 5000": "Allen-Bradley / Rockwell",
        "schneider": "Schneider Electric",
        "abb": "ABB",
        "danfoss": "Danfoss"
    }

    scadas = {
        "ignition": "Ignition",
        "wincc": "WinCC",
        "factorytalk": "FactoryTalk",
        "aveva": "AVEVA",
        "wonderware": "AVEVA / Wonderware"
    }

    networks = {
        "profinet": "Profinet",
        "ethernet/ip": "Ethernet/IP",
        "ethernet ip": "Ethernet/IP",
        "modbus": "Modbus TCP",
        "profibus": "Profibus"
    }

    for k, v in brands.items():
        if k in text_lower:
            memory["plc_brand"] = v

    for k, v in scadas.items():
        if k in text_lower:
            memory["scada"] = v

    for k, v in networks.items():
        if k in text_lower:
            memory["network"] = v

    if "planta" in text_lower and not memory["plant"]:
        memory["plant"] = text[:80]

    if "proyecto" in text_lower and not memory["project_name"]:
        memory["project_name"] = text[:80]

    if "bomba" in text_lower or "motor" in text_lower or "válvula" in text_lower or "valvula" in text_lower:
        memory["process"] = text[:160]


def generate_basic_engineering_package():
    memory = st.session_state.project_memory

    content = f"""
# PAQUETE DE INGENIERÍA INDUSTRIAL

Generado por: SCA AI Engineering Assistant  
Fecha: {datetime.now().strftime("%d-%m-%Y %H:%M")}

---

## 1. Datos Generales

Proyecto: {memory.get("project_name") or "Pendiente"}  
Cliente: {memory.get("client") or "Pendiente"}  
Planta / Área: {memory.get("plant") or "Pendiente"}  
Proceso: {memory.get("process") or "Pendiente"}  

---

## 2. Plataforma de Control

PLC / Marca sugerida: {memory.get("plc_brand") or "Pendiente"}  
SCADA / HMI: {memory.get("scada") or "Pendiente"}  
Red Industrial: {memory.get("network") or "Pendiente"}  
Cantidad IO aproximada: {memory.get("io_count") or "Pendiente"}  

---

## 3. Arquitectura Inicial Recomendada

- PLC principal para control de proceso.
- HMI/SCADA para operación, alarmas y tendencias.
- Red industrial dedicada para comunicación entre PLC, IO remoto, variadores e instrumentación.
- Separación entre red OT y red corporativa.
- Switches industriales administrables.
- UPS para PLC, red y servidores críticos.
- Gabinete de control con protecciones, borneras y reserva de expansión.

---

## 4. Filosofía de Control Inicial

- Operación Manual / Automática.
- Permisivos de partida.
- Interlocks de seguridad.
- Alarmas críticas y de advertencia.
- Secuencias por etapas.
- Registro de eventos operacionales.
- Tendencias de variables principales.
- Diagnóstico de comunicaciones.

---

## 5. Documentos a Generar

- Arquitectura PLC/HMI/SCADA.
- Lista IO.
- Lista de tags.
- Matriz de alarmas.
- Filosofía de control.
- Secuencias.
- FAT.
- SAT.
- Manual de operación.
- Estimación HH.
- Riesgos y exclusiones.
"""

    path = OUTPUT_DIR / "paquete_ingenieria_industrial.md"
    path.write_text(content, encoding="utf-8")
    return path


def build_prompt(user_text):
    memory = st.session_state.project_memory

    return f"""
Eres SCA AI Engineering Assistant, un experto industrial multimarca en:
Siemens TIA Portal, Allen-Bradley Studio 5000, Schneider, ABB, Danfoss,
Ignition, AVEVA, WinCC, FactoryTalk, redes industriales, SCADA, PLC,
instrumentación, variadores, licitaciones y cotizaciones técnicas.

Datos actuales del proyecto:
{memory}

Consulta del usuario:
{user_text}

Responde en español chileno profesional, claro y práctico.
Entrega pasos accionables.
Si falta información, pregunta solo la siguiente información crítica.
"""


def ask_ai(user_text):
    simple_project_autofill(user_text)

    prompt = build_prompt(user_text)

    if rag_ready:
        try:
            return ask_rag(prompt)
        except Exception as e:
            return f"⚠️ El motor RAG tuvo un problema, pero el sistema sigue operativo.\n\nDetalle: {e}"

    return f"""
Estoy funcionando en modo interfaz, pero el motor RAG no cargó.

Consulta recibida:
{user_text}

Siguiente dato recomendado:
{next_missing_info()}
"""


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🏭 Panel Industrial")

    show_context = st.checkbox("Mostrar contexto usado", value=False, key="ui_show_context_main_unique")

    st.markdown("### Modo de trabajo")

    modes = [
        "Asistente Proyecto desde Cero",
        "Chat Técnico Industrial",
        "Arquitectura PLC/HMI",
        "Generador Tags PLC",
        "Generador Programa PLC",
        "Paquete Ingeniería",
        "Arquitecto SCADA",
        "Diagnóstico PLC",
        "Diagnóstico Redes Industriales",
        "Análisis Lista IO",
        "Licitaciones Industriales",
        "Cotizador HH Industrial"
    ]

    st.session_state.selected_mode = st.radio(
        "Selecciona modo",
        modes,
        label_visibility="collapsed",
        key="radio_sidebar_selected_mode_unique"
    )

    st.markdown("---")

    progress = calculate_progress()
    st.markdown("### Avance proyecto")
    st.progress(progress)
    st.markdown(f"**{progress}% completado**")

    st.info(f"**Siguiente información requerida:**\n\n{next_missing_info()}")

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("🧹 Limpiar", key="btn_sidebar_clear_chat_unique"):
            st.session_state.messages = []
            st.rerun()

    with col_b:
        if st.button("🔄 Reiniciar", key="btn_sidebar_reset_project_unique"):
            st.session_state.project_memory = {
                "project_name": "",
                "client": "",
                "plant": "",
                "process": "",
                "plc_brand": "",
                "scada": "",
                "network": "",
                "io_count": "",
                "documents": [],
                "missing": []
            }
            st.session_state.messages = []
            st.rerun()

    st.markdown("---")

    api_key = get_api_key()

    if api_key:
        st.markdown('<span class="status-ok">● OpenAI conectado</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-error">● Falta OPENAI_API_KEY</span>', unsafe_allow_html=True)

    if rag_ready:
        st.markdown('<span class="status-ok">● RAG conectado</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-warn">● RAG no cargado</span>', unsafe_allow_html=True)

    if memory_ready:
        st.markdown('<span class="status-ok">● Memoria disponible</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-warn">● Memoria simple activa</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption(APP_VERSION)

# =========================================================
# HEADER
# =========================================================

st.markdown(f"""
<div class="main-title">🏭 {APP_NAME}</div>
<div class="subtitle">
Plataforma IA industrial multimarca para ingeniería, automatización, SCADA,
licitaciones, cotizaciones y generación automática de proyectos.
</div>
""", unsafe_allow_html=True)

# =========================================================
# MÉTRICAS
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">Motor IA</div>
        <div class="metric-value">ONLINE</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    status = "RAG OK" if rag_ready else "RAG OFF"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Knowledge Base</div>
        <div class="metric-value">{status}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    docs_count = len(st.session_state.project_memory.get("documents", []))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Documentos cargados</div>
        <div class="metric-value">{docs_count}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Avance Proyecto</div>
        <div class="metric-value">{progress}%</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================

tab_chat, tab_project, tab_docs, tab_tools, tab_bids = st.tabs([
    "💬 Chat Industrial",
    "📂 Proyecto Guiado",
    "📄 Documentos",
    "🛠 Herramientas",
    "📑 Licitaciones"
])

# =========================================================
# TAB CHAT
# =========================================================

with tab_chat:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.subheader("Asistente Industrial Multimarca")

    st.write("""
Especialista en Siemens, Rockwell, Schneider, ABB, Danfoss, Ignition,
AVEVA, WinCC, FactoryTalk, redes industriales, PLC, SCADA, variadores,
instrumentación y documentación técnica.
""")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_text = st.chat_input("Describe tu planta, consulta técnica, problema PLC/SCADA o licitación...", key="chat_input_main_unique")

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})

        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Analizando como ingeniero industrial IA..."):
                answer = ask_ai(user_text)
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

        if memory_ready:
            try:
                save_memory("industrial_project", st.session_state.project_memory)
            except Exception:
                pass

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB PROYECTO GUIADO
# =========================================================

with tab_project:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.subheader("Proyecto Guiado Industrial")

    st.write("Completa la información base del proyecto. El agente usará esto para generar ingeniería.")

    c1, c2 = st.columns(2)

    with c1:
        st.session_state.project_memory["project_name"] = st.text_input(
            "Nombre del proyecto",
            value=st.session_state.project_memory.get("project_name", ""),
            key="input_project_name_unique"
        )

        st.session_state.project_memory["client"] = st.text_input(
            "Cliente",
            value=st.session_state.project_memory.get("client", ""),
            key="input_client_unique"
        )

        st.session_state.project_memory["plant"] = st.text_input(
            "Planta / Área",
            value=st.session_state.project_memory.get("plant", ""),
            key="input_plant_unique"
        )

        st.session_state.project_memory["process"] = st.text_area(
            "Proceso industrial",
            value=st.session_state.project_memory.get("process", ""),
            key="textarea_process_unique"
        )

    with c2:
        st.session_state.project_memory["plc_brand"] = st.selectbox(
            "PLC / Plataforma",
            [
                "",
                "Siemens TIA Portal",
                "Allen-Bradley / Rockwell Studio 5000",
                "Schneider Electric",
                "ABB",
                "Otro / Por definir"
            ],
            index=0,
            key="select_plc_brand_unique"
        )

        st.session_state.project_memory["scada"] = st.selectbox(
            "SCADA / HMI",
            [
                "",
                "Ignition",
                "WinCC",
                "FactoryTalk View",
                "AVEVA / Wonderware",
                "HMI Local",
                "Otro / Por definir"
            ],
            index=0,
            key="select_scada_unique"
        )

        st.session_state.project_memory["network"] = st.selectbox(
            "Red Industrial",
            [
                "",
                "Profinet",
                "Ethernet/IP",
                "Modbus TCP",
                "Profibus",
                "Modbus RTU",
                "OPC UA",
                "Otro / Por definir"
            ],
            index=0,
            key="select_network_unique"
        )

        st.session_state.project_memory["io_count"] = st.text_input(
            "Cantidad IO aproximada",
            value=st.session_state.project_memory.get("io_count", ""),
            key="input_io_count_unique"
        )

    if st.button("🧠 Generar Proyecto Base", key="btn_generate_project_base_unique"):
        path = generate_basic_engineering_package()
        st.success("Paquete base generado correctamente.")
        st.download_button(
            "Descargar paquete ingeniería .md",
            data=path.read_text(encoding="utf-8"),
            file_name="paquete_ingenieria_industrial.md",
            mime="text/markdown",
            key="download_engineering_md_unique"
        )

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB DOCUMENTOS
# =========================================================

with tab_docs:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.subheader("Carga de Documentación Técnica")

    uploaded_files = st.file_uploader(
        "Sube PDFs, Word, Excel, TXT, bases técnicas o documentos del proyecto",
        accept_multiple_files=True,
        type=["pdf", "docx", "xlsx", "xls", "txt", "csv"],
        key="uploader_project_documents_unique"
    )

    if uploaded_files:
        saved = save_uploaded_files(uploaded_files)
        st.success(f"{len(saved)} archivo(s) guardado(s) en output/uploaded_docs")

        for s in saved:
            st.write(f"📄 {Path(s).name}")

    st.markdown("### Documentos registrados en memoria")

    docs = st.session_state.project_memory.get("documents", [])

    if docs:
        for d in docs:
            st.write(f"✅ {d}")
    else:
        st.info("Aún no hay documentos cargados.")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB HERRAMIENTAS
# =========================================================

with tab_tools:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.subheader("Herramientas Industriales IA")

    tool = st.selectbox(
        "Selecciona herramienta",
        [
            "Generador Arquitectura PLC/HMI/SCADA",
            "Generador Filosofía de Control",
            "Generador Lista de Alarmas",
            "Generador Lista de Tags",
            "Estimador HH",
            "Generador FAT/SAT",
            "Diagnóstico PLC",
            "Diagnóstico Red Industrial",
            "Generador Documento Técnico"
        ],
        key="select_tool_unique"
    )

    tool_context = st.text_area(
        "Describe el requerimiento",
        height=180,
        placeholder="Ejemplo: sistema con 3 bombas, 2 estanques, medición de nivel, control automático, SCADA Ignition...",
        key="textarea_tool_context_unique"
    )

    if st.button("⚙️ Ejecutar herramienta IA", key="btn_execute_ai_tool_unique"):
        if not tool_context.strip():
            st.warning("Escribe primero el requerimiento.")
        else:
            prompt = f"""
Herramienta seleccionada: {tool}

Contexto:
{tool_context}

Genera una respuesta técnica estructurada, profesional y accionable.
"""
            with st.spinner("Generando resultado técnico..."):
                result = ask_ai(prompt)
                st.markdown(result)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# TAB LICITACIONES
# =========================================================

with tab_bids:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.subheader("Análisis de Licitaciones Industriales")

    st.write("""
Este módulo permite analizar bases técnicas, detectar alcance, riesgos,
estimación HH, exclusiones y recomendación de postulación.
""")

    bid_files = st.file_uploader(
        "Sube bases administrativas/técnicas de licitación",
        accept_multiple_files=True,
        type=["pdf", "docx", "xlsx", "xls", "txt"],
        key="uploader_bid_files_unique"
    )

    bid_context = st.text_area(
        "Pega aquí el resumen o alcance de la licitación",
        height=220,
        placeholder="Ejemplo: suministro e implementación de sistema SCADA, PLC, tableros, redes industriales, FAT/SAT...",
        key="textarea_bid_context_unique"
    )

    colb1, colb2, colb3 = st.columns(3)

    with colb1:
        generate_bid_analysis = st.button("📑 Analizar Licitación", key="btn_bid_analysis_unique")

    with colb2:
        generate_hh = st.button("⏱ Estimar HH", key="btn_estimate_hh_unique")

    with colb3:
        generate_proposal = st.button("📝 Generar Propuesta Técnica", key="btn_generate_proposal_unique")

    if bid_files:
        saved_bid_files = save_uploaded_files(bid_files)
        st.success(f"{len(saved_bid_files)} archivo(s) de licitación cargado(s).")

    if generate_bid_analysis:
        prompt = f"""
Analiza esta licitación industrial:

{bid_context}

Entrega:
1. Resumen ejecutivo
2. Alcance técnico probable
3. Especialidades involucradas
4. Riesgos
5. Exclusiones recomendadas
6. Preguntas al mandante
7. Recomendación: postular / revisar / descartar
8. Puntaje de atractivo del 1 al 100
"""
        with st.spinner("Analizando licitación..."):
            st.markdown(ask_ai(prompt))

    if generate_hh:
        prompt = f"""
Estima horas hombre para esta licitación industrial:

{bid_context}

Separar HH por:
- Jefe de proyecto
- Ingeniero automatización
- Programador PLC
- Programador SCADA/HMI
- Ingeniero redes
- Dibujante eléctrico
- Comisionamiento
- FAT
- SAT
- Puesta en marcha
- Documentación

Entregar tabla y supuestos.
"""
        with st.spinner("Estimando HH..."):
            st.markdown(ask_ai(prompt))

    if generate_proposal:
        prompt = f"""
Genera una propuesta técnica industrial para esta licitación:

{bid_context}

Debe incluir:
1. Carta técnica inicial
2. Entendimiento del requerimiento
3. Alcance ofertado
4. Metodología
5. Entregables
6. Exclusiones
7. Supuestos
8. Cronograma referencial
9. Equipo de trabajo
10. Valor agregado técnico
"""
        with st.spinner("Generando propuesta técnica..."):
            st.markdown(ask_ai(prompt))

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# CONTEXTO DEBUG
# =========================================================

if show_context:
    st.markdown("---")
    st.subheader("Contexto interno del proyecto")
    st.json(st.session_state.project_memory)

    if not rag_ready:
        st.warning(f"RAG no cargado: {rag_error if 'rag_error' in globals() else 'sin detalle'}")

    if not memory_ready:
        st.warning(f"Memoria no cargada: {memory_error if 'memory_error' in globals() else 'sin detalle'}")

st.markdown('<div class="footer-space"></div>', unsafe_allow_html=True)


