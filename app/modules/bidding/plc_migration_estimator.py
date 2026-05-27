import os
import re
import json
import shutil
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data", "bids", "plc_migration")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


CONTROL_KEYWORDS = {
    "tags": [
        "tag", "tags", "bool", "real", "int", "dint", "word", "input", "output",
        "di", "do", "ai", "ao", "entrada", "salida", "senal", "señal"
    ],
    "motors": [
        "motor", "mot", "bomba", "pump", "fan", "blower", "ventilador",
        "agitador", "mixer", "conveyor", "transportador", "correa"
    ],
    "valves": [
        "valve", "valvula", "válvula", "solenoid", "solenoide",
        "damper", "actuator", "actuador", "open", "close"
    ],
    "drives": [
        "vfd", "drive", "variador", "inverter", "powerflex", "danfoss",
        "sinamics", "altivar", "abb drive", "acs", "speed"
    ],
    "heaters": [
        "heater", "calefactor", "resistencia", "heating", "temperatura",
        "temperature", "heat", "horno", "furnace"
    ],
    "sensors": [
        "sensor", "switch", "transmitter", "transmisor", "level", "nivel",
        "pressure", "presion", "presión", "temperature", "temperatura",
        "flow", "caudal", "proximity", "proximidad", "encoder", "photoeye"
    ],
    "alarms": [
        "alarm", "alarma", "fault", "falla", "trip", "warning",
        "error", "fail", "interlock", "permissive"
    ],
    "pid": [
        "pid", "setpoint", "sp", "pv", "cv", "controlador",
        "loop", "lazo", "regulador"
    ],
    "networks": [
        "profinet", "profibus", "modbus", "ethernet/ip", "ethernet ip",
        "opc", "opc ua", "tcp", "ip address", "scanner", "adapter"
    ],
    "routines_blocks": [
        "routine", "program", "task", "aoi", "add-on instruction",
        "function_block", "function block", "fb_", "fc_", "db_", "ladder"
    ],
    "screens": [
        "screen", "pantalla", "hmi", "scada", "display", "window",
        "faceplate", "popup", "overview"
    ],
}


def save_plc_file(uploaded_file):
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, uploaded_file.name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(uploaded_file, f)

    return file_path


def read_text_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_binary_as_text(path):
    with open(path, "rb") as f:
        raw = f.read()

    decoded = raw.decode("latin-1", errors="ignore")
    printable = "".join(ch if ch.isprintable() or ch in "\n\r\t" else " " for ch in decoded)

    return printable


def read_excel_file(path):
    text = ""
    sheets = pd.read_excel(path, sheet_name=None)

    for sheet_name, df in sheets.items():
        text += f"\n=== HOJA: {sheet_name} ===\n"
        text += df.head(1500).to_string(index=False)
        text += "\n"

    return text


def extract_text_from_plc_file(path):
    ext = os.path.splitext(path)[1].lower()
    filename = os.path.basename(path)

    if ext in [".txt", ".scl", ".awl", ".st", ".xml", ".l5x", ".csv", ".json"]:
        return read_text_file(path)

    if ext in [".xlsx", ".xls"]:
        return read_excel_file(path)

    if ext == ".acd":
        binary_text = read_binary_as_text(path)

        return f"""
ARCHIVO ROCKWELL ACD DETECTADO:
{filename}

El archivo .ACD es binario. Se intentó extraer texto interno básico para detectar palabras clave,
pero para análisis exacto se requiere export .L5X desde Studio 5000.

IMPORTANTE:
Esta estimación será preliminar.

TEXTO INTERNO EXTRAÍDO:
{binary_text[:60000]}
"""

    if ext in [".zap", ".ap13", ".ap14", ".ap15", ".ap16", ".ap17", ".ap18", ".ap19"]:
        binary_text = read_binary_as_text(path)

        return f"""
ARCHIVO SIEMENS TIA PORTAL DETECTADO:
{filename}

Archivo binario/propietario. Para análisis exacto solicitar export XML, SCL, lista de tags o documentación.

TEXTO INTERNO EXTRAÍDO:
{binary_text[:60000]}
"""

    return f"""
ARCHIVO NO LEGIBLE DIRECTAMENTE:
{filename}

Extensión detectada: {ext}

Solicitar export legible:
- Rockwell: L5X, CSV tags, export routines
- Siemens: XML, SCL, AWL, lista tags Excel/CSV
- Schneider: XML, ST, CSV tags
- SCADA: export tags, pantallas, JSON, CSV
"""


def detect_platform(text, filename=""):
    low_text = text.lower()
    low_file = filename.lower()

    if ".acd" in low_file or ".l5x" in low_file:
        return "Rockwell / Allen-Bradley"

    if ".zap" in low_file or ".ap13" in low_file or ".ap14" in low_file or ".ap15" in low_file or ".ap16" in low_file or ".ap17" in low_file or ".ap18" in low_file or ".ap19" in low_file:
        return "Siemens"

    rockwell = [
        "rslogix", "studio 5000", "compactlogix", "controllogix",
        "micrologix", "slc500", "allen-bradley", "allen bradley",
        "rockwell", "l5x", "aoi", "add-on instruction",
        "controller tags", "ethernet/ip", "powerflex"
    ]

    siemens = [
        "tia portal", "s7-1200", "s7-1500", "s7-300", "s7-400",
        "simatic", "sinamics", "profinet", "profibus",
        "optimized block access", "function_block", "data_block"
    ]

    schneider = [
        "modicon", "schneider", "ecostruxure", "control expert",
        "unity pro", "m580", "m340", "altivar"
    ]

    ignition = [
        "ignition", "inductive automation", "gateway",
        "perspective", "vision module", "tag provider"
    ]

    aveva = [
        "wonderware", "intouch", "aveva", "system platform", "galaxy"
    ]

    if any(k in low_text for k in rockwell):
        return "Rockwell / Allen-Bradley"

    if any(k in low_text for k in siemens):
        return "Siemens"

    if any(k in low_text for k in schneider):
        return "Schneider"

    if any(k in low_text for k in ignition):
        return "Ignition SCADA"

    if any(k in low_text for k in aveva):
        return "AVEVA / Wonderware"

    return "No identificado"


def keyword_count(text, words):
    low = text.lower()
    total = 0

    for word in words:
        pattern = r"\b" + re.escape(word.lower()) + r"\b"
        total += len(re.findall(pattern, low))

    return total


def count_patterns(text, platform, filenames):
    counts = {}

    for category, words in CONTROL_KEYWORDS.items():
        counts[category] = keyword_count(text, words)

    # Si es ACD binario, los conteos reales pueden salir muy bajos.
    # No mostrar 0 falso: usar mínimos preliminares razonables.
    is_acd = any(name.lower().endswith(".acd") for name in filenames)

    if is_acd:
        counts["tags"] = max(counts["tags"], 120)
        counts["routines_blocks"] = max(counts["routines_blocks"], 10)
        counts["screens"] = max(counts["screens"], 5)
        counts["alarms"] = max(counts["alarms"], 20)
        counts["networks"] = max(counts["networks"], 1)

    # Si hay SCADA pero pocas pantallas detectadas
    if counts["screens"] == 0 and keyword_count(text, ["hmi", "scada", "factorytalk", "ignition", "wonderware", "wincc"]) > 0:
        counts["screens"] = 5

    return counts


def estimate_migration_complexity(counts, platform, is_binary=False):
    score = 0

    score += min(counts["tags"] / 200, 5)
    score += min(counts["motors"] / 10, 3)
    score += min(counts["valves"] / 15, 3)
    score += min(counts["drives"] / 6, 3)
    score += min(counts["heaters"] / 8, 2)
    score += min(counts["sensors"] / 20, 3)
    score += min(counts["alarms"] / 30, 3)
    score += min(counts["pid"] / 5, 3)
    score += min(counts["networks"] / 3, 3)
    score += min(counts["routines_blocks"] / 20, 4)
    score += min(counts["screens"] / 10, 3)

    if platform == "No identificado":
        score += 2

    if is_binary:
        score += 2

    if score >= 12:
        return "alta"

    if score >= 6:
        return "media"

    return "baja"


def estimate_migration_hh(counts, complexity, platform, is_binary=False):
    factor = {
        "baja": 0.85,
        "media": 1.0,
        "alta": 1.35
    }.get(complexity, 1.0)

    tags_est = max(counts["tags"], 120 if is_binary else 80)
    blocks_est = max(counts["routines_blocks"], 10 if is_binary else 5)
    alarms_est = max(counts["alarms"], 20 if is_binary else 10)
    screens_est = max(counts["screens"], 5)

    motors_est = counts["motors"]
    valves_est = counts["valves"]
    drives_est = counts["drives"]
    heaters_est = counts["heaters"]
    sensors_est = counts["sensors"]
    pid_est = counts["pid"]

    if platform == "Rockwell / Allen-Bradley":
        reverse_base = 40 if is_binary else 32
        plc_base = 64 if is_binary else 56
    elif platform == "Siemens":
        reverse_base = 32 if is_binary else 24
        plc_base = 56 if is_binary else 48
    else:
        reverse_base = 36 if is_binary else 28
        plc_base = 60 if is_binary else 52

    analysis = 28 * factor
    reverse_engineering = (reverse_base + blocks_est * 2.8) * factor

    plc_migration = (
        plc_base
        + tags_est * 0.20
        + blocks_est * 3.2
        + motors_est * 4.5
        + valves_est * 3.0
        + drives_est * 7.0
        + heaters_est * 3.0
        + sensors_est * 1.2
        + pid_est * 9.0
    ) * factor

    scada_development = (
        36
        + screens_est * 11
        + alarms_est * 0.7
        + tags_est * 0.09
    ) * factor

    communications = (18 + counts["networks"] * 8) * factor
    fat = (28 + tags_est * 0.055 + blocks_est * 1.4) * factor
    sat = (36 + tags_est * 0.08 + screens_est * 2.2) * factor
    documentation = 28 * factor
    pm = 28 * factor

    total = (
        analysis
        + reverse_engineering
        + plc_migration
        + scada_development
        + communications
        + fat
        + sat
        + documentation
        + pm
    )

    return {
        "Análisis programa existente": round(analysis, 1),
        "Ingeniería inversa": round(reverse_engineering, 1),
        "Migración / reprogramación PLC": round(plc_migration, 1),
        "Desarrollo SCADA/HMI": round(scada_development, 1),
        "Comunicaciones industriales": round(communications, 1),
        "Pruebas FAT": round(fat, 1),
        "Puesta en marcha SAT": round(sat, 1),
        "Documentación": round(documentation, 1),
        "Gestión técnica": round(pm, 1),
        "TOTAL HH": round(total, 1),
    }


def analyze_plc_migration(uploaded_files, hourly_rate=35000, margin_percent=25):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    full_text = ""
    file_names = []

    for uploaded_file in uploaded_files:
        path = save_plc_file(uploaded_file)
        file_names.append(uploaded_file.name)

        extracted = extract_text_from_plc_file(path)

        full_text += "\n\n==============================\n"
        full_text += f"ARCHIVO PLC/SCADA: {uploaded_file.name}\n"
        full_text += "==============================\n"
        full_text += extracted[:60000]

    is_binary = any(
        name.lower().endswith((".acd", ".zap", ".ap13", ".ap14", ".ap15", ".ap16", ".ap17", ".ap18", ".ap19"))
        for name in file_names
    )

    platform = detect_platform(full_text, " ".join(file_names))
    counts = count_patterns(full_text, platform, file_names)
    complexity = estimate_migration_complexity(counts, platform, is_binary=is_binary)
    hh = estimate_migration_hh(counts, complexity, platform, is_binary=is_binary)

    total_hh = hh["TOTAL HH"]
    direct_cost = total_hh * hourly_rate
    sale_price = direct_cost * (1 + margin_percent / 100)

    result = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "archivos": file_names,
        "plataforma_detectada": platform,
        "archivo_binario": is_binary,
        "conteos": counts,
        "complejidad": complexity,
        "hh": hh,
        "valor_hh": hourly_rate,
        "margen_percent": margin_percent,
        "costo_directo": round(direct_cost, 0),
        "precio_venta": round(sale_price, 0),
        "riesgos": generate_migration_risks(platform, counts, complexity, is_binary),
        "preguntas": generate_migration_questions(platform, counts, is_binary),
    }

    txt_path = os.path.join(OUTPUT_DIR, "Cotizacion_Migraciones_y_SCADA.txt")
    json_path = os.path.join(OUTPUT_DIR, "Cotizacion_Migraciones_y_SCADA.json")
    excel_path = os.path.join(OUTPUT_DIR, "Cotizacion_Migraciones_y_SCADA.xlsx")

    text_report = build_text_report(result)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text_report)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    rows = []

    for item, hours in hh.items():
        if item != "TOTAL HH":
            rows.append({
                "Item": item,
                "HH": hours,
                "Valor HH": hourly_rate,
                "Subtotal CLP": round(hours * hourly_rate, 0)
            })

    rows.append({
        "Item": "TOTAL HH",
        "HH": total_hh,
        "Valor HH": "",
        "Subtotal CLP": round(direct_cost, 0)
    })

    rows.append({
        "Item": f"Margen {margin_percent}%",
        "HH": "",
        "Valor HH": "",
        "Subtotal CLP": round(sale_price - direct_cost, 0)
    })

    rows.append({
        "Item": "PRECIO VENTA ESTIMADO",
        "HH": "",
        "Valor HH": "",
        "Subtotal CLP": round(sale_price, 0)
    })

    pd.DataFrame(rows).to_excel(excel_path, index=False)

    return {
        "result": result,
        "txt_path": txt_path,
        "json_path": json_path,
        "excel_path": excel_path,
        "text_report": text_report,
    }


def generate_migration_risks(platform, counts, complexity, is_binary):
    risks = []

    if is_binary:
        risks.append("El archivo subido es binario/propietario. La estimación usa mínimos técnicos preliminares. Para precisión se requiere export legible.")

    if platform == "Rockwell / Allen-Bradley":
        risks.append("Para Rockwell, solicitar export .L5X desde Studio 5000 y export CSV de tags para estimar con precisión.")

    if platform == "No identificado":
        risks.append("No se pudo identificar claramente la plataforma. Solicitar export legible del proyecto PLC/SCADA.")

    if counts["tags"] < 80:
        risks.append("Se detectaron pocos tags. Puede faltar export de tags o lista IO.")

    if counts["screens"] <= 5:
        risks.append("Pantallas SCADA estimadas preliminarmente. Confirmar cantidad real de pantallas, popups y faceplates.")

    if counts["alarms"] < 20:
        risks.append("Alarmas estimadas preliminarmente. Confirmar si se migran alarmas históricas, eventos y acknowledge.")

    if counts["networks"] <= 1:
        risks.append("Protocolos/redes poco definidos. Confirmar OPC UA, Ethernet/IP, Profinet, Modbus TCP, drivers y arquitectura.")

    if complexity == "alta":
        risks.append("Complejidad alta. Considerar visita técnica, revisión de respaldo original y fase formal de ingeniería inversa.")

    return risks


def generate_migration_questions(platform, counts, is_binary):
    questions = []

    questions.append("¿Cuál es la plataforma destino de migración? Ej: TIA Portal, Studio 5000, Ignition, AVEVA, WinCC.")

    if is_binary:
        questions.append("¿Puedes entregar export legible del proyecto? Rockwell .L5X, CSV tags, rutinas, pantallas SCADA o lista IO.")

    if platform == "Rockwell / Allen-Bradley":
        questions.append("¿El proyecto Rockwell tiene AOI, UDT, múltiples tasks, motion, safety o produced/consumed tags?")

    questions.append("¿Cuántas pantallas HMI/SCADA existen y cuántas deben migrarse?")

    questions.append("¿Existe lista oficial de tags o lista IO?")

    questions.append("¿Se debe migrar histórico, alarmas, usuarios, recetas o reportes?")

    questions.append("¿Incluye FAT, SAT, capacitación y puesta en marcha?")

    questions.append("¿La cotización debe incluir licencias SCADA, servidores, switches, tableros o solo ingeniería?")

    return questions


def build_text_report(result):
    text = f"""
COTIZACIÓN DE MIGRACIONES Y SCADA
Fecha: {result["fecha"]}

====================================
1. ARCHIVOS ANALIZADOS
====================================

{chr(10).join(["- " + f for f in result["archivos"]])}

Archivo binario/propietario: {"Sí" if result["archivo_binario"] else "No"}

====================================
2. PLATAFORMA DETECTADA
====================================

{result["plataforma_detectada"]}

Complejidad estimada: {result["complejidad"]}

====================================
3. ELEMENTOS DE CONTROL DETECTADOS / ESTIMADOS
====================================

"""

    labels = {
        "tags": "Tags / señales",
        "motors": "Motores / bombas / ventiladores",
        "valves": "Válvulas / actuadores",
        "drives": "Variadores / drives",
        "heaters": "Calefactores / resistencias",
        "sensors": "Sensores / transmisores",
        "alarms": "Alarmas / fallas / interlocks",
        "pid": "Lazos PID",
        "networks": "Redes / protocolos",
        "routines_blocks": "Rutinas / bloques",
        "screens": "Pantallas HMI/SCADA",
    }

    for key, value in result["conteos"].items():
        text += f"- {labels.get(key, key)}: {value}\n"

    text += """

====================================
4. ESTIMACIÓN HH
====================================

"""

    for item, hours in result["hh"].items():
        text += f"- {item}: {hours} HH\n"

    text += f"""

====================================
5. VALORIZACIÓN
====================================

Valor HH: ${result["valor_hh"]:,.0f} CLP
Margen: {result["margen_percent"]}%
Costo directo: ${result["costo_directo"]:,.0f} CLP
Precio venta estimado: ${result["precio_venta"]:,.0f} CLP

====================================
6. RIESGOS
====================================

"""

    for risk in result["riesgos"]:
        text += f"- {risk}\n"

    text += """

====================================
7. PREGUNTAS PARA ACLARAR
====================================

"""

    for question in result["preguntas"]:
        text += f"- {question}\n"

    text += """

====================================
8. RECOMENDACIÓN
====================================

Esta cotización es preliminar. Para una oferta formal se recomienda solicitar:
- Export legible del programa PLC.
- Export de tags.
- Backup o capturas SCADA/HMI.
- Lista IO.
- Filosofía de control.
- Alcance FAT/SAT.
- Plataforma destino.
- Confirmación de licencias, servidores, tableros y redes.
"""

    return text


