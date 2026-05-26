import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
PROJECT_FILE = os.path.join(MEMORY_DIR, "project_wizard.json")

DEFAULT_PROJECT = {
    "project_name": "",
    "plant_description": "",
    "process_type": "",
    "control_objective": "",
    "io_available": "",
    "instruments": "",
    "motors_actuators": "",
    "communication": "",
    "hmi_requirements": "",
    "safety_requirements": "",
    "control_philosophy": "",
    "documents_summary": "",
    "last_question": "",
    "created_at": "",
    "updated_at": ""
}


def load_project():
    os.makedirs(MEMORY_DIR, exist_ok=True)

    if not os.path.exists(PROJECT_FILE):
        data = DEFAULT_PROJECT.copy()
        data["created_at"] = datetime.now().isoformat()
        save_project(data)
        return data

    with open(PROJECT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for key, value in DEFAULT_PROJECT.items():
        data.setdefault(key, value)

    return data


def save_project(data):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()

    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def reset_project():
    data = DEFAULT_PROJECT.copy()
    data["created_at"] = datetime.now().isoformat()
    save_project(data)
    return data


def project_completion(data):
    keys = [
        "project_name",
        "plant_description",
        "process_type",
        "control_objective",
        "io_available",
        "instruments",
        "motors_actuators",
        "communication",
        "hmi_requirements",
        "safety_requirements",
        "control_philosophy"
    ]

    done = sum(1 for key in keys if str(data.get(key, "")).strip())
    return int((done / len(keys)) * 100)


def missing_questions(data):
    questions = []

    if not data.get("project_name"):
        questions.append("¿Cómo se llama el proyecto o planta?")

    if not data.get("plant_description"):
        questions.append("Describe la planta: ¿qué proceso controla y qué equipos principales tiene?")

    if not data.get("process_type"):
        questions.append("¿Qué tipo de proceso es? Ej: bombeo, transportadores, tratamiento de agua, dosificación, HVAC.")

    if not data.get("control_objective"):
        questions.append("¿Cuál es el objetivo de control? Ej: controlar bombas, mantener nivel, secuencia automática, alarmas.")

    if not data.get("io_available"):
        questions.append("¿Tienes lista IO? Si sí, sube el Excel o describe entradas/salidas.")

    if not data.get("instruments"):
        questions.append("¿Qué instrumentos instalarás? Ej: nivel, presión, temperatura, caudal, finales de carrera.")

    if not data.get("motors_actuators"):
        questions.append("¿Qué actuadores habrá? Ej: motores, bombas, válvulas, variadores, contactores.")

    if not data.get("communication"):
        questions.append("¿Cómo se comunicarán los equipos? Ej: Profinet, Modbus TCP, Ethernet/IP, señales cableadas.")

    if not data.get("hmi_requirements"):
        questions.append("¿Qué necesita ver/controlar el operador en HMI? Pantallas, alarmas, tendencias, manual/auto.")

    if not data.get("safety_requirements"):
        questions.append("¿Qué seguridad tendrá? Parada emergencia, enclavamientos, puertas, relé de seguridad, Safety PLC.")

    if not data.get("control_philosophy"):
        questions.append("Describe la filosofía de control: manual, automático, secuencia, permisos, interlocks y fallas.")

    return questions


def next_question(data):
    q = missing_questions(data)
    if q:
        return q[0]

    return "Ya tengo la información mínima. Puedo generar arquitectura TIA, tags, filosofía de control y programa base."


def extract_relevant_lines(text, keywords, max_lines=50):
    selected = []

    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue

        low = line_clean.lower()

        if any(k.lower() in low for k in keywords):
            selected.append(line_clean)

        if len(selected) >= max_lines:
            break

    if selected:
        return "\n".join(selected)

    return text[:1500]


def auto_fill_project_from_text(text):
    data = load_project()
    lower = text.lower()

    data["documents_summary"] = text[:7000]

    if not data["plant_description"]:
        data["plant_description"] = text[:1500]

    if not data["io_available"] and any(x in lower for x in ["entrada", "salida", "input", "output", "di", "do", "ai", "ao", "io", "i/o"]):
        data["io_available"] = extract_relevant_lines(text, ["entrada", "salida", "input", "output", "di", "do", "ai", "ao", "señal", "senal"])

    if not data["instruments"] and any(x in lower for x in ["sensor", "transmisor", "nivel", "presión", "presion", "temperatura", "caudal", "switch"]):
        data["instruments"] = extract_relevant_lines(text, ["sensor", "transmisor", "nivel", "presión", "presion", "temperatura", "caudal", "switch"])

    if not data["motors_actuators"] and any(x in lower for x in ["motor", "bomba", "válvula", "valvula", "actuador", "variador", "vfd"]):
        data["motors_actuators"] = extract_relevant_lines(text, ["motor", "bomba", "válvula", "valvula", "actuador", "variador", "vfd"])

    if not data["communication"] and any(x in lower for x in ["profinet", "modbus", "ethernet", "profibus", "opc", "hmi", "scada"]):
        data["communication"] = extract_relevant_lines(text, ["profinet", "modbus", "ethernet", "profibus", "opc", "hmi", "scada"])

    if not data["hmi_requirements"] and any(x in lower for x in ["hmi", "pantalla", "operador", "alarma", "tendencia", "scada"]):
        data["hmi_requirements"] = extract_relevant_lines(text, ["hmi", "pantalla", "operador", "alarma", "tendencia", "scada"])

    if not data["safety_requirements"] and any(x in lower for x in ["seguridad", "emergencia", "e-stop", "parada", "interlock", "enclavamiento"]):
        data["safety_requirements"] = extract_relevant_lines(text, ["seguridad", "emergencia", "e-stop", "parada", "interlock", "enclavamiento"])

    if not data["control_philosophy"] and any(x in lower for x in ["filosofía", "filosofia", "manual", "automático", "automatico", "secuencia", "control"]):
        data["control_philosophy"] = extract_relevant_lines(text, ["filosofía", "filosofia", "manual", "automático", "automatico", "secuencia", "control"])

    data["last_question"] = next_question(data)

    save_project(data)
    return data


def generate_project_context_text(data):
    return f"""
=== DATOS ACTUALES DEL PROYECTO ===

Nombre proyecto:
{data.get("project_name", "")}

Descripción planta:
{data.get("plant_description", "")}

Tipo proceso:
{data.get("process_type", "")}

Objetivo control:
{data.get("control_objective", "")}

Lista IO:
{data.get("io_available", "")}

Instrumentos:
{data.get("instruments", "")}

Motores / actuadores:
{data.get("motors_actuators", "")}

Comunicación:
{data.get("communication", "")}

HMI:
{data.get("hmi_requirements", "")}

Seguridad:
{data.get("safety_requirements", "")}

Filosofía control:
{data.get("control_philosophy", "")}

Resumen documentos:
{data.get("documents_summary", "")}
"""


def generate_project_brief_file():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = load_project()

    path = os.path.join(OUTPUT_DIR, "Brief_Proyecto_Siemens.txt")
    content = generate_project_context_text(data)

    content += "\n\n=== INFORMACIÓN FALTANTE ===\n"

    for q in missing_questions(data):
        content += f"- {q}\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return path, content