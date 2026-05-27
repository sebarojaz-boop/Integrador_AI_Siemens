import os
import streamlit as st

from modules.bidding.plc_migration_estimator import analyze_plc_migration

st.set_page_config(
    page_title="Cotización de Migraciones y SCADA",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Cotización de Migraciones y SCADA")

st.write("""
Sube programas PLC, respaldos, exportaciones de tags, archivos SCADA o documentación técnica.
El agente estimará complejidad, HH, riesgos y una cotización preliminar.
""")

st.warning("""
Nota:
Archivos como .ACD de Rockwell o .ZAP/.AP de Siemens son binarios.
El agente puede reconocerlos y estimar con mínimos técnicos preliminares,
pero para precisión se recomienda exportar:
- Rockwell: .L5X + CSV tags
- Siemens: XML / SCL / AWL + lista tags
- SCADA: export tags / pantallas / documentación
""")

uploaded_files = st.file_uploader(
    "Sube archivos PLC / SCADA",
    accept_multiple_files=True,
    type=[
        "txt", "csv", "json", "xml",
        "scl", "awl", "l5x", "acd",
        "zap", "ap13", "ap14", "ap15", "ap16", "ap17", "ap18", "ap19",
        "xlsx", "xls", "pdf", "docx"
    ],
    key="cotizacion_migracion_upload"
)

col1, col2, col3 = st.columns(3)

with col1:
    hourly_rate = st.number_input(
        "Valor HH CLP",
        min_value=10000,
        max_value=250000,
        value=35000,
        step=5000,
        key="cotizacion_migracion_hh"
    )

with col2:
    margin_percent = st.number_input(
        "Margen %",
        min_value=0,
        max_value=200,
        value=25,
        step=5,
        key="cotizacion_migracion_margen"
    )

with col3:
    include_scada = st.checkbox(
        "Considerar SCADA",
        value=True,
        key="cotizacion_migracion_scada"
    )

if st.button("🧠 Generar Cotización de Migración y SCADA", key="btn_cotizacion_migracion"):

    if not uploaded_files:
        st.warning("Primero sube archivos PLC o SCADA.")
        st.stop()

    with st.spinner("Analizando archivos y estimando migración..."):
        analysis = analyze_plc_migration(
            uploaded_files=uploaded_files,
            hourly_rate=hourly_rate,
            margin_percent=margin_percent
        )

    result = analysis["result"]

    st.success("Cotización preliminar generada correctamente.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Plataforma", result["plataforma_detectada"])

    with col2:
        st.metric("Complejidad", result["complejidad"])

    with col3:
        st.metric("TOTAL HH", result["hh"]["TOTAL HH"])

    with col4:
        st.metric("Precio estimado", f"${result['precio_venta']:,.0f}")

    st.divider()

    st.subheader("📊 Elementos de control detectados / estimados")

    pretty_counts = {
        "Tags / señales": result["conteos"].get("tags", 0),
        "Motores / bombas / ventiladores": result["conteos"].get("motors", 0),
        "Válvulas / actuadores": result["conteos"].get("valves", 0),
        "Variadores / drives": result["conteos"].get("drives", 0),
        "Calefactores / resistencias": result["conteos"].get("heaters", 0),
        "Sensores / transmisores": result["conteos"].get("sensors", 0),
        "Alarmas / fallas / interlocks": result["conteos"].get("alarms", 0),
        "Lazos PID": result["conteos"].get("pid", 0),
        "Redes / protocolos": result["conteos"].get("networks", 0),
        "Rutinas / bloques": result["conteos"].get("routines_blocks", 0),
        "Pantallas HMI/SCADA": result["conteos"].get("screens", 0),
    }

    st.json(pretty_counts)

    st.divider()

    st.subheader("⏱️ Estimación HH")

    st.json(result["hh"])

    st.divider()

    st.subheader("⚠️ Riesgos")

    for risk in result["riesgos"]:
        st.warning(risk)

    st.divider()

    st.subheader("❓ Preguntas faltantes")

    for question in result["preguntas"]:
        st.info(question)

    st.divider()

    st.subheader("📄 Resumen técnico y económico")

    st.text_area(
        "Resultado",
        value=analysis["text_report"],
        height=700,
        key="cotizacion_migracion_reporte"
    )

    with open(analysis["txt_path"], "rb") as f:
        st.download_button(
            label="⬇️ Descargar TXT",
            data=f,
            file_name=os.path.basename(analysis["txt_path"]),
            mime="text/plain",
            key="download_cotizacion_migracion_txt"
        )

    with open(analysis["excel_path"], "rb") as f:
        st.download_button(
            label="⬇️ Descargar Excel Cotización",
            data=f,
            file_name=os.path.basename(analysis["excel_path"]),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_cotizacion_migracion_excel"
        )


