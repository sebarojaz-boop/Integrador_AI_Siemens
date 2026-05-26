import re


KEYWORDS = {
    "plc": [
        "plc", "s7-1200", "s7-1500", "s7-300", "s7-400",
        "compactlogix", "controllogix", "allen bradley", "rockwell",
        "modicon", "schneider", "cpu"
    ],
    "scada": [
        "scada", "hmi", "wincc", "ignition", "aveva", "wonderware",
        "factorytalk", "intouch", "supervision", "supervisorio"
    ],
    "protocols": [
        "profinet", "profibus", "modbus", "modbus tcp", "ethernet/ip",
        "opc", "opc ua", "mqtt", "serial", "rs485"
    ],
    "drives": [
        "variador", "vfd", "drive", "danfoss", "abb", "sinamics",
        "powerflex", "altivar"
    ],
    "io": [
        "entrada", "salida", "di", "do", "ai", "ao",
        "input", "output", "señal", "senal", "i/o", "io"
    ],
    "fat_sat": [
        "fat", "sat", "puesta en marcha", "comisionamiento",
        "commissioning", "pruebas", "capacitación", "capacitacion"
    ],
    "cybersecurity": [
        "ciberseguridad", "cybersecurity", "firewall", "vpn",
        "vlan", "dmz", "hardening", "usuarios", "roles"
    ],
    "warranty": [
        "garantía", "garantia", "warranty", "soporte", "mantención",
        "mantencion"
    ]
}


def find_lines(text, keywords, limit=30):
    results = []
    lines = text.splitlines()

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        low = clean.lower()

        if any(k.lower() in low for k in keywords):
            results.append(clean)

        if len(results) >= limit:
            break

    return results


def count_possible_io(text):
    low = text.lower()

    patterns = [
        r"(\d+)\s*(di|do|ai|ao)",
        r"(\d+)\s*(entradas|salidas)",
        r"(\d+)\s*(señales|senales)",
        r"(\d+)\s*(inputs|outputs)"
    ]

    values = []

    for pattern in patterns:
        matches = re.findall(pattern, low)
        for match in matches:
            try:
                values.append(int(match[0]))
            except Exception:
                pass

    if values:
        return sum(values)

    return None


def detect_complexity(text):
    low = text.lower()

    score = 0

    complexity_terms = [
        "redundancia", "redundant", "historian", "sql", "opc ua",
        "migración", "migracion", "virtualización", "virtualizacion",
        "ciberseguridad", "dmz", "recetas", "batch", "mes",
        "sap", "alta disponibilidad"
    ]

    for term in complexity_terms:
        if term in low:
            score += 1

    if score >= 5:
        return "alta"

    if score >= 2:
        return "media"

    return "baja"


def extract_bid_requirements(text):
    detected = {}

    for category, keywords in KEYWORDS.items():
        detected[category] = find_lines(text, keywords)

    io_count = count_possible_io(text)
    complexity = detect_complexity(text)

    summary = {
        "alcance_detectado": {
            "plc": detected["plc"],
            "scada": detected["scada"],
            "protocolos": detected["protocols"],
            "variadores": detected["drives"],
            "io": detected["io"],
            "fat_sat_capacitacion": detected["fat_sat"],
            "ciberseguridad": detected["cybersecurity"],
            "garantias_soporte": detected["warranty"],
        },
        "io_count_estimado": io_count,
        "complejidad_estimada": complexity,
        "riesgos_iniciales": generate_initial_risks(text, detected),
        "preguntas_faltantes": generate_missing_questions(detected, io_count)
    }

    return summary


def generate_initial_risks(text, detected):
    risks = []

    low = text.lower()

    if not detected["io"]:
        risks.append("No se detectó una lista IO clara. Riesgo alto de subestimar ingeniería y materiales.")

    if not detected["scada"]:
        risks.append("No se detectó plataforma SCADA/HMI definida. Confirmar si aplica Ignition, WinCC, AVEVA, FactoryTalk u otra.")

    if not detected["protocols"]:
        risks.append("No se detectaron protocolos de comunicación. Confirmar Profinet, Modbus TCP, Ethernet/IP, OPC UA, etc.")

    if "migración" in low or "migracion" in low:
        risks.append("Se detecta posible migración. Validar respaldo histórico, compatibilidad, tags, pantallas y drivers.")

    if "puesta en marcha" not in low and "commissioning" not in low:
        risks.append("No está claro el alcance de puesta en marcha.")

    if "garant" not in low:
        risks.append("No se detectaron condiciones de garantía o soporte.")

    return risks


def generate_missing_questions(detected, io_count):
    questions = []

    if io_count is None:
        questions.append("¿Existe una lista IO formal con cantidad de DI, DO, AI y AO?")

    if not detected["plc"]:
        questions.append("¿Qué marca/modelo de PLC existe o se requiere?")

    if not detected["scada"]:
        questions.append("¿Qué plataforma SCADA/HMI se requiere o existe actualmente?")

    if not detected["protocols"]:
        questions.append("¿Qué protocolos de comunicación se usarán?")

    if not detected["fat_sat"]:
        questions.append("¿La oferta debe incluir FAT, SAT, capacitación y puesta en marcha?")

    if not detected["cybersecurity"]:
        questions.append("¿Existen requerimientos de ciberseguridad, usuarios, VPN, VLAN o DMZ?")

    return questions