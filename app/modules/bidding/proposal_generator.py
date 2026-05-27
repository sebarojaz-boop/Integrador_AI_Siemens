import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def generate_bid_summary_text(extraction):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    alcance = extraction.get("alcance_detectado", {})
    risks = extraction.get("riesgos_iniciales", [])
    questions = extraction.get("preguntas_faltantes", [])
    io_count = extraction.get("io_count_estimado", "No detectado")
    complexity = extraction.get("complejidad_estimada", "media")

    text = f"""
ANÁLISIS TÉCNICO PRELIMINAR DE LICITACIÓN
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}

====================================
1. RESUMEN EJECUTIVO
====================================

El sistema analizó las bases/documentos cargados y generó una primera lectura técnica.
Este análisis sirve para preparar preguntas, estimar alcance y evitar subcotizaciones.

Complejidad estimada: {complexity}
Cantidad IO estimada: {io_count}

====================================
2. ALCANCE DETECTADO
====================================

PLC / Controladores:
{format_list(alcance.get("plc", []))}

SCADA / HMI:
{format_list(alcance.get("scada", []))}

Protocolos / Redes:
{format_list(alcance.get("protocolos", []))}

Variadores:
{format_list(alcance.get("variadores", []))}

IO / Señales:
{format_list(alcance.get("io", []))}

FAT / SAT / Capacitación:
{format_list(alcance.get("fat_sat_capacitacion", []))}

Ciberseguridad:
{format_list(alcance.get("ciberseguridad", []))}

Garantías / Soporte:
{format_list(alcance.get("garantias_soporte", []))}

====================================
3. RIESGOS DETECTADOS
====================================

{format_list(risks)}

====================================
4. PREGUNTAS PARA ACLARAR
====================================

{format_list(questions)}

====================================
5. RECOMENDACIÓN INICIAL
====================================

Antes de valorizar formalmente, se recomienda confirmar:
- Lista IO definitiva.
- Plataforma PLC/SCADA.
- Cantidad de pantallas.
- Protocolos de comunicación.
- Licencias requeridas.
- Alcance FAT/SAT.
- Plazo de ejecución.
- Responsabilidad sobre suministros, tableros, cableado y terreno.
"""

    output_path = os.path.join(OUTPUT_DIR, "Resumen_Tecnico_Licitacion.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    return output_path, text


def format_list(items):
    if not items:
        return "- No detectado claramente.\n"

    return "\n".join([f"- {item}" for item in items]) + "\n"


