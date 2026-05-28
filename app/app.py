import os
import base64
import streamlit as st


st.set_page_config(
    page_title="SCA AI Engineering Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(__file__)

css_path = os.path.join(BASE_DIR, "styles", "sca_theme.css")
logo_path = os.path.join(BASE_DIR, "assets", "sca_logo.svg")

if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

logo_base64 = ""

if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()


def logo_html(width=210):
    if not logo_base64:
        return ""
    return f'<img src="data:image/svg+xml;base64,{logo_base64}" width="{width}">'


def sidebar_item(icon, label, active=False):
    active_class = "active" if active else ""
    st.markdown(
        f"""
        <div class="side-item {active_class}">
            <span class="side-icon">{icon}</span>
            <span>{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def module_card(icon, title, desc, color="cyan", page=None):
    if page:
        st.page_link(page, label=f"{icon} {title}")
    st.markdown(
        f"""
        <div class="module-card {color}">
            <div class="module-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{desc}</p>
            <div class="module-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-logo">
            {logo_html(215)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-section">MÓDULOS PRINCIPALES</div>', unsafe_allow_html=True)

    sidebar_item("🏠", "Inicio", active=True)
    sidebar_item("📄", "Generación de Cotizaciones")
    sidebar_item("📋", "Evaluación de Licitaciones")
    sidebar_item("SIEMENS", "Generar Programa Siemens")
    sidebar_item("AB", "Generar Programa Rockwell")
    sidebar_item("💬", "Chat Técnico")
    sidebar_item("I/O", "Análisis Listado IO")
    sidebar_item("🖥️", "Análisis de SCADA y HMI")
    sidebar_item("⚙️", "Desarrollo Ingeniería de Control")

    st.markdown('<div class="side-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-section">PLATAFORMAS SOPORTADAS</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="platform-list">
            <div><b class="green">SIEMENS</b><span>›</span></div>
            <div><b class="red">AB</b> Rockwell Automation<span>›</span></div>
            <div><b class="purple">AVEVA</b> | <b class="orange">Ignition</b><span>›</span></div>
            <div><b class="blue">WinCC</b> | FactoryTalk<span>›</span></div>
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
                <span>Versión 1.0.0</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

row1 = st.columns(4, gap="large")

with row1[0]:
    module_card(
        "📄",
        "Generación de Cotizaciones",
        "Genera cotizaciones técnicas y económicas de manera automática.",
        "cyan",
    )

with row1[1]:
    module_card(
        "📋",
        "Evaluación de Licitaciones",
        "Analiza bases técnicas, riesgos y alcance para licitaciones industriales.",
        "purple",
    )

with row1[2]:
    module_card(
        "SIEMENS",
        "Generar Programa Siemens",
        "Genera código optimizado para PLC Siemens TIA Portal.",
        "green",
    )

with row1[3]:
    module_card(
        "AB",
        "Generar Programa Rockwell",
        "Genera lógica para PLC Rockwell Automation Studio 5000.",
        "red",
    )

row2 = st.columns(4, gap="large")

with row2[0]:
    module_card(
        "💬",
        "Chat Técnico",
        "Asistente IA especializado en PLC, SCADA, redes OT y automatización.",
        "blue",
    )

with row2[1]:
    module_card(
        "I/O",
        "Análisis Listado IO",
        "Revisión inteligente de señales, tags y arquitectura de control.",
        "cyan",
    )

with row2[2]:
    module_card(
        "🖥️",
        "Análisis de SCADA y HMI",
        "Análisis y recomendaciones para sistemas SCADA y HMI industriales.",
        "blue",
    )

with row2[3]:
    module_card(
        "⚙️",
        "Desarrollo Ingeniería de Control",
        "Soporte en arquitectura, filosofía de control y documentación.",
        "yellow",
    )

st.markdown(
    """
    <div class="bottom-status">
        <div>
            <span class="status-icon purple">▣</span>
            <p>Modelos IA</p>
            <b>OpenAI GPT-4o</b>
        </div>
        <div>
            <span class="status-icon cyan">◎</span>
            <p>Base de Conocimiento</p>
            <b>Activa</b>
        </div>
        <div>
            <span class="status-icon green">盾</span>
            <p>Seguridad</p>
            <b>Entorno Industrial</b>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)