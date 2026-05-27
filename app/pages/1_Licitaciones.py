import os
import streamlit as st

from modules.bidding.bid_reader import process_bid_documents
from modules.bidding.bid_extractor import extract_bid_requirements
from modules.bidding.proposal_generator import generate_bid_summary_text

st.set_page_config(
    page_title="Licitaciones Industriales",
    page_icon="📑",
    layout="wide"
)

st.title("📑 Licitaciones Industriales")
st.write("Analizador inteligente de bases técnicas para automatización, PLC, SCADA, redes industriales y cotizaciones.")

st.markdown("""
### Flujo de trabajo

1. Sube bases técnicas PDF, Word, Excel, TXT o CSV.
2. El agente extrae información técnica.
3. Detecta PLC, SCADA, protocolos, IO, FAT/SAT, garantías y riesgos.
4. Genera un resumen técnico preliminar.
""")

uploaded_files = st.file_uploader(
    "Sube documentos de licitación",
    type=["pdf", "docx", "xlsx", "xls", "csv", "txt"],
    accept_multiple_files=True,
    key="bid_upload_files"
)

if st.button("🧠 Analizar Licitación", key="btn_analyze_bid"):
    if not uploaded_files:
        st.warning("Primero sube uno o más documentos.")
        st.stop()

    with st.spinner("Leyendo documentos de licitación..."):
        bid_text = process_bid_documents(uploaded_files)

    if not bid_text.strip():
        st.error("No se pudo extraer texto útil de los documentos.")
        st.stop()

    with st.spinner("Extrayendo requerimientos técnicos..."):
        extraction = extract_bid_requirements(bid_text)

    with st.spinner("Generando resumen técnico..."):
        output_path, summary_text = generate_bid_summary_text(extraction)

    st.success("Análisis técnico generado correctamente.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "IO estimadas",
            extraction.get("io_count_estimado") or "No detectado"
        )

    with col2:
        st.metric(
            "Complejidad",
            extraction.get("complejidad_estimada", "media")
        )

    with col3:
        riesgos = extraction.get("riesgos_iniciales", [])
        st.metric(
            "Riesgos detectados",
            len(riesgos)
        )

    st.divider()

    st.subheader("📌 Resumen técnico")

    st.text_area(
        "Resultado",
        value=summary_text,
        height=600,
        key="bid_summary_text"
    )

    with open(output_path, "rb") as f:
        st.download_button(
            label="⬇️ Descargar Resumen Técnico",
            data=f,
            file_name=os.path.basename(output_path),
            mime="text/plain",
            key="download_bid_summary"
        )

    st.divider()

    st.subheader("⚠️ Riesgos detectados")

    for risk in extraction.get("riesgos_iniciales", []):
        st.warning(risk)

    st.subheader("❓ Preguntas para aclarar")

    for question in extraction.get("preguntas_faltantes", []):
        st.info(question)


