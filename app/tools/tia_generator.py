import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IO_FILE_DIR = os.path.join(BASE_DIR, "data", "io")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def find_io_excel():
    if not os.path.exists(IO_FILE_DIR):
        return None

    for file in os.listdir(IO_FILE_DIR):
        if file.lower().endswith(".xlsx"):
            return os.path.join(IO_FILE_DIR, file)

    return None


def normalize_col(name):
    return str(name).strip().lower().replace(" ", "_")


def detect_signal_type(row_text):
    text = row_text.lower()

    if any(x in text for x in ["emergencia", "e-stop", "parada emergencia", "safety"]):
        return "SAFETY"

    if any(x in text for x in ["motor", "bomba", "valvula", "vÃ¡lvula", "partida", "run"]):
        return "OUTPUT"

    if any(x in text for x in ["sensor", "switch", "pulsador", "boton", "botÃ³n", "nivel", "presostato", "fin de carrera"]):
        return "INPUT"

    if any(x in text for x in ["alarma", "fault", "falla"]):
        return "ALARM"

    return "GENERAL"


def siemens_tag_name(text, prefix):
    clean = str(text)
    clean = clean.replace("Ã¡", "a").replace("Ã©", "e").replace("Ã­", "i").replace("Ã³", "o").replace("Ãº", "u")
    clean = clean.replace("Ã", "A").replace("Ã‰", "E").replace("Ã", "I").replace("Ã“", "O").replace("Ãš", "U")
    clean = "".join(c if c.isalnum() else "_" for c in clean)
    clean = "_".join([x for x in clean.split("_") if x])
    clean = clean[:45]

    if not clean:
        clean = "Signal"

    return f"{prefix}_{clean}"


def generate_tia_tags():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    excel_path = find_io_excel()

    if excel_path is None:
        return None, "No encontrÃ© archivo Excel en data/io."

    df = pd.read_excel(excel_path)
    df.columns = [normalize_col(c) for c in df.columns]

    generated_rows = []

    for idx, row in df.iterrows():
        row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
        signal_type = detect_signal_type(row_text)

        if signal_type == "INPUT":
            prefix = "DI"
            data_type = "Bool"
            area = "Input"
        elif signal_type == "OUTPUT":
            prefix = "DO"
            data_type = "Bool"
            area = "Output"
        elif signal_type == "SAFETY":
            prefix = "SF"
            data_type = "Bool"
            area = "Safety"
        elif signal_type == "ALARM":
            prefix = "ALM"
            data_type = "Bool"
            area = "Memory"
        else:
            prefix = "TAG"
            data_type = "Bool"
            area = "Memory"

        tag_name = siemens_tag_name(row_text[:80], prefix)

        generated_rows.append({
            "Original_Row": idx + 1,
            "Tag_Name": tag_name,
            "Data_Type": data_type,
            "Area": area,
            "Signal_Class": signal_type,
            "Description": row_text[:250],
            "Suggested_DB": "DB_Global_IO",
            "HMI_Visible": "Yes" if signal_type in ["INPUT", "OUTPUT", "ALARM", "SAFETY"] else "No",
            "Alarm_Recommended": "Yes" if signal_type in ["ALARM", "SAFETY"] else "No"
        })

    out_df = pd.DataFrame(generated_rows)

    output_path = os.path.join(OUTPUT_DIR, "TIA_Tags_Generados.xlsx")
    out_df.to_excel(output_path, index=False)

    summary = f"""
Archivo leÃ­do: {os.path.basename(excel_path)}
Total seÃ±ales procesadas: {len(out_df)}

Resumen:
- Entradas detectadas: {len(out_df[out_df["Signal_Class"] == "INPUT"])}
- Salidas detectadas: {len(out_df[out_df["Signal_Class"] == "OUTPUT"])}
- Safety detectadas: {len(out_df[out_df["Signal_Class"] == "SAFETY"])}
- Alarmas detectadas: {len(out_df[out_df["Signal_Class"] == "ALARM"])}
- Generales: {len(out_df[out_df["Signal_Class"] == "GENERAL"])}

Archivo generado:
{output_path}
"""

    return output_path, summary


def generate_base_st_program():
    st_code = """
// ==================================================
// PROGRAMA BASE PROPUESTO PARA TIA PORTAL - S7-1200/S7-1500
// Generado por SCA AI Engineering Assistant
// ==================================================

// OB1 - Main Cycle
// RecomendaciÃ³n:
// 1. Leer entradas
// 2. Procesar seguridad e interlocks
// 3. Ejecutar secuencia automÃ¡tica
// 4. Comandar salidas
// 5. Generar alarmas para HMI

// =====================
// VARIABLES SUGERIDAS
// =====================
// Start_PB       : Bool
// Stop_PB        : Bool
// Emergency_OK   : Bool
// Auto_Mode      : Bool
// Manual_Mode    : Bool
// Motor_Run_Cmd  : Bool
// Motor_Feedback : Bool
// Motor_Fault    : Bool
// Alarm_General  : Bool

// =====================
// LOGICA BASE
// =====================

IF NOT Emergency_OK THEN
    Motor_Run_Cmd := FALSE;
    Alarm_General := TRUE;

ELSIF Stop_PB THEN
    Motor_Run_Cmd := FALSE;

ELSIF Start_PB AND Auto_Mode AND NOT Motor_Fault THEN
    Motor_Run_Cmd := TRUE;

END_IF;


// =====================
// SUPERVISION DE MOTOR
// =====================

IF Motor_Run_Cmd AND NOT Motor_Feedback THEN
    // Agregar TON en TIA Portal para retardo de falla
    Motor_Fault := TRUE;
END_IF;


// =====================
// RESET DE FALLA
// =====================

IF NOT Start_PB AND NOT Stop_PB THEN
    // CondiciÃ³n referencial, ajustar segÃºn criterio de planta
END_IF;
"""

    output_path = os.path.join(OUTPUT_DIR, "Programa_Base_TIA_ST.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(st_code)

    return output_path, st_code



