import os
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def estimate_hh_from_text(text):
    t = text.lower()

    hh = {
        "Ingeniería y levantamiento": 24,
        "Programación PLC": 40,
        "Programación HMI/SCADA": 40,
        "Comunicaciones industriales": 16,
        "Pruebas FAT": 16,
        "Puesta en marcha SAT": 24,
        "Documentación": 16,
        "Gestión de proyecto": 12
    }

    if any(x in t for x in ["rockwell", "allen bradley", "compactlogix", "controllogix"]):
        hh["Programación PLC"] += 24

    if any(x in t for x in ["siemens", "s7-1200", "s7-1500", "tia portal"]):
        hh["Programación PLC"] += 20

    if any(x in t for x in ["schneider", "modicon", "ecostruxure"]):
        hh["Programación PLC"] += 20

    if any(x in t for x in ["ignition"]):
        hh["Programación HMI/SCADA"] += 40

    if any(x in t for x in ["aveva", "wonderware", "system platform"]):
        hh["Programación HMI/SCADA"] += 48

    if any(x in t for x in ["wincc", "factorytalk"]):
        hh["Programación HMI/SCADA"] += 32

    if any(x in t for x in ["variador", "vdf", "vfd", "danfoss", "powerflex", "sinamics", "altivar"]):
        hh["Comunicaciones industriales"] += 24
        hh["Puesta en marcha SAT"] += 16

    if any(x in t for x in ["profinet", "ethernet/ip", "modbus", "profibus", "opc"]):
        hh["Comunicaciones industriales"] += 24

    if any(x in t for x in ["pid", "receta", "batch", "historiador", "historian"]):
        hh["Programación PLC"] += 24
        hh["Programación HMI/SCADA"] += 24

    if any(x in t for x in ["urgente", "plazo reducido", "turno", "24/7"]):
        hh["Gestión de proyecto"] += 16
        hh["Puesta en marcha SAT"] += 16

    return hh


def detect_brands(text):
    t = text.lower()
    brands = []

    mapping = {
        "Siemens": ["siemens", "tia portal", "s7-1200", "s7-1500", "wincc", "sinamics"],
        "Rockwell / Allen-Bradley": ["rockwell", "allen bradley", "compactlogix", "controllogix", "factorytalk", "powerflex"],
        "Schneider Electric": ["schneider", "modicon", "ecostruxure", "altivar"],
        "Danfoss": ["danfoss", "vlt", "fc-302", "fc302"],
        "ABB": ["abb", "acs580", "acs880"],
        "Ignition": ["ignition", "inductive automation"],
        "AVEVA / Wonderware": ["aveva", "wonderware", "system platform", "intouch"],
        "OPC / Kepware": ["opc", "kepware", "kepserver"]
    }

    for brand, words in mapping.items():
        if any(w in t for w in words):
            brands.append(brand)

    return brands or ["No identificado claramente"]


def generate_bid_outputs(text, hourly_rate=35000):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    brands = detect_brands(text)
    hh = estimate_hh_from_text(text)

    total_hh = sum(hh.values())
    subtotal = total_hh * hourly_rate
    contingencia = int(subtotal * 0.15)
    total = subtotal + contingencia

    rows = []
    for item, hours in hh.items():
        rows.append({
            "Item": item,
            "HH estimadas": hours,
            "Valor HH": hourly_rate,
            "Subtotal": hours * hourly_rate
        })

    df = pd.DataFrame(rows)

    quote_path = os.path.join(OUTPUT_DIR, "Cotizacion_Tecnica_Industrial.xlsx")
    df.to_excel(quote_path, index=False)

    proposal = f"""
PROPUESTA TÉCNICA INDUSTRIAL - BORRADOR

Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}

1. Marcas / plataformas detectadas
{chr(10).join(["- " + b for b in brands])}

2. Alcance preliminar
- Ingeniería de automatización y control.
- Revisión de documentación técnica.
- Desarrollo de lógica PLC.
- Desarrollo HMI/SCADA según requerimiento.
- Integración de comunicaciones industriales.
- Pruebas FAT.
- Apoyo en puesta en marcha SAT.
- Documentación final.

3. Estimación HH
{chr(10).join([f"- {k}: {v} HH" for k, v in hh.items()])}

Total HH estimadas: {total_hh}

4. Valorización preliminar
Valor HH: ${hourly_rate:,} CLP
Subtotal: ${subtotal:,} CLP
Contingencia técnica 15%: ${contingencia:,} CLP
TOTAL ESTIMADO: ${total:,} CLP

5. Riesgos detectados
- Alcance técnico puede estar incompleto si faltan planos, lista IO o filosofía de control.
- Riesgo de integración si no están claros protocolos de comunicación.
- Riesgo de plazo si se requiere puesta en marcha en producción.
- Riesgo de compatibilidad entre marcas/plataformas.
- Riesgo de cambios de alcance durante implementación.

6. Exclusiones recomendadas
- Suministro de hardware, salvo que se indique explícitamente.
- Montaje eléctrico.
- Canalizaciones y cableado de terreno.
- Licencias SCADA/HMI.
- Obras civiles.
- Instrumentación no especificada.
- Soporte fuera de horario normal, salvo acuerdo.

7. Información faltante para cotización final
- Lista IO definitiva.
- Arquitectura de control.
- Marca/modelo PLC.
- Marca/modelo HMI o SCADA.
- Cantidad de pantallas.
- Cantidad de variadores.
- Protocolos de comunicación.
- Filosofía de control.
- Requerimientos FAT/SAT.
- Plazo requerido.
"""

    proposal_path = os.path.join(OUTPUT_DIR, "Propuesta_Tecnica_Industrial.txt")

    with open(proposal_path, "w", encoding="utf-8") as f:
        f.write(proposal)

    summary = f"""
Cotización técnica generada.

Marcas detectadas:
{chr(10).join(["- " + b for b in brands])}

Total HH estimadas: {total_hh}
Valor HH: ${hourly_rate:,} CLP
Total estimado con contingencia: ${total:,} CLP

Archivos generados:
- {quote_path}
- {proposal_path}
"""

    return quote_path, proposal_path, summary


