import os
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_IO_DIR = os.path.join(BASE_DIR, "data", "io")


def find_io_excel():
    if not os.path.exists(DATA_IO_DIR):
        return None

    for file in os.listdir(DATA_IO_DIR):
        if file.lower().endswith(".xlsx"):
            return os.path.join(DATA_IO_DIR, file)

    return None


def clean_tag(text):
    text = str(text)
    replacements = {
        "Ã¡": "a", "Ã©": "e", "Ã­": "i", "Ã³": "o", "Ãº": "u",
        "Ã": "A", "Ã‰": "E", "Ã": "I", "Ã“": "O", "Ãš": "U",
        "Ã±": "n", "Ã‘": "N"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = "".join(c if c.isalnum() else "_" for c in text)
    text = "_".join([x for x in text.split("_") if x])
    return text[:50] if text else "Signal"


def detect_class(text):
    t = str(text).lower()

    if any(x in t for x in ["emergencia", "e-stop", "safety", "seguridad"]):
        return "SAFETY", "SF"

    if any(x in t for x in ["motor", "bomba", "valvula", "vÃ¡lvula", "solenoide", "partida", "run"]):
        return "OUTPUT", "DO"

    if any(x in t for x in ["sensor", "switch", "boton", "botÃ³n", "pulsador", "nivel", "presostato", "fin de carrera"]):
        return "INPUT", "DI"

    if any(x in t for x in ["alarma", "fault", "falla", "error"]):
        return "ALARM", "ALM"

    return "GENERAL", "TAG"


def load_io_dataframe():
    excel = find_io_excel()

    if excel is None:
        return None, "No se encontrÃ³ Excel IO en data/io."

    df = pd.read_excel(excel)
    return df, excel


def generate_plc_tags():
    df, source = load_io_dataframe()

    if df is None:
        return None, source

    rows = []

    for idx, row in df.iterrows():
        row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
        signal_class, prefix = detect_class(row_text)

        tag_name = f"{prefix}_{clean_tag(row_text[:80])}"

        if signal_class == "INPUT":
            address_area = "I"
        elif signal_class == "OUTPUT":
            address_area = "Q"
        else:
            address_area = "M"

        rows.append({
            "Name": tag_name,
            "Data type": "Bool",
            "Logical address": "",
            "Address area": address_area,
            "Signal class": signal_class,
            "Comment": row_text[:250],
            "HMI visible": "Yes" if signal_class in ["INPUT", "OUTPUT", "ALARM", "SAFETY"] else "No",
            "Alarm recommended": "Yes" if signal_class in ["ALARM", "SAFETY"] else "No"
        })

    tags_df = pd.DataFrame(rows)
    output_path = os.path.join(OUTPUT_DIR, "PLC_Tags_TIA.xlsx")
    tags_df.to_excel(output_path, index=False)

    return output_path, tags_df


def generate_ob1_st():
    code = """// ==================================================
// OB1 - MAIN PROGRAM
// SCA AI Engineering Assistant
// ==================================================

REGION Read_Inputs
    // Llamar aquÃ­ FC_ReadInputs
    // FC_ReadInputs();
END_REGION

REGION Safety_And_Interlocks
    // Evaluar emergencia, permissivos y condiciones de seguridad
    // FC_Safety();
END_REGION

REGION Automatic_Sequence
    // Ejecutar secuencia automÃ¡tica principal
    // FB_MainSequence();
END_REGION

REGION Motor_Control
    // Ejemplo:
    // FB_MotorControl(
    //     StartCmd := Start_Auto,
    //     StopCmd := Stop_Cmd,
    //     SafetyOK := Safety_OK,
    //     Feedback := Motor_Feedback,
    //     MotorRun => Motor_Run,
    //     Fault => Motor_Fault
    // );
END_REGION

REGION Alarms
    // Generar alarmas para HMI
    // FC_Alarms();
END_REGION
"""

    path = os.path.join(OUTPUT_DIR, "Programa_OB1_ST.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    return path, code


def generate_fb_motor_st():
    code = """FUNCTION_BLOCK FB_MotorControl
{ S7_Optimized_Access := 'TRUE' }

VAR_INPUT
    StartCmd    : Bool;
    StopCmd     : Bool;
    SafetyOK    : Bool;
    Feedback    : Bool;
    ResetFault  : Bool;
END_VAR

VAR_OUTPUT
    MotorRun    : Bool;
    Fault       : Bool;
END_VAR

VAR
    StartMemory : Bool;
END_VAR

BEGIN

    // Reset falla
    IF ResetFault THEN
        Fault := FALSE;
    END_IF;

    // CondiciÃ³n de seguridad
    IF NOT SafetyOK THEN
        MotorRun := FALSE;
        StartMemory := FALSE;
        Fault := TRUE;
    END_IF;

    // Stop
    IF StopCmd THEN
        MotorRun := FALSE;
        StartMemory := FALSE;
    END_IF;

    // Start
    IF StartCmd AND SafetyOK AND NOT Fault THEN
        StartMemory := TRUE;
    END_IF;

    // Comando motor
    MotorRun := StartMemory AND SafetyOK AND NOT Fault;

    // SupervisiÃ³n bÃ¡sica feedback
    IF MotorRun AND NOT Feedback THEN
        // RecomendaciÃ³n: reemplazar por TON en TIA Portal
        // para evitar falla instantÃ¡nea
    END_IF;

END_FUNCTION_BLOCK
"""

    path = os.path.join(OUTPUT_DIR, "FB_MotorControl_ST.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    return path, code


def generate_db_structure():
    code = """// ==================================================
// DB_Global_Structure
// Estructura recomendada para TIA Portal
// ==================================================

TYPE UDT_Motor :
STRUCT
    StartCmd     : Bool;
    StopCmd      : Bool;
    RunCmd       : Bool;
    Feedback     : Bool;
    Fault        : Bool;
    ResetFault   : Bool;
    AutoMode     : Bool;
    ManualMode   : Bool;
END_STRUCT
END_TYPE


TYPE UDT_Alarm :
STRUCT
    Active       : Bool;
    Ack          : Bool;
    Text         : String[80];
END_STRUCT
END_TYPE


DATA_BLOCK DB_Global_IO
{ S7_Optimized_Access := 'TRUE' }

VAR
    Safety_OK       : Bool;
    Emergency_OK    : Bool;

    Motor_01        : UDT_Motor;
    Alarm_General   : UDT_Alarm;
END_VAR

BEGIN

END_DATA_BLOCK
"""

    path = os.path.join(OUTPUT_DIR, "DB_Global_Structure.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    return path, code


def generate_readme():
    text = f"""# Paquete de IngenierÃ­a Siemens generado

Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Archivos generados:

1. PLC_Tags_TIA.xlsx
   - Tabla base de tags para usar como referencia en TIA Portal.

2. Programa_OB1_ST.txt
   - Estructura base recomendada para OB1.

3. FB_MotorControl_ST.txt
   - Function Block base para control de motor.

4. DB_Global_Structure.txt
   - Propuesta de UDTs y DB global.

RecomendaciÃ³n de implementaciÃ³n:

1. Crear proyecto en TIA Portal.
2. Definir PLC S7-1200 o S7-1500.
3. Crear UDT_Motor y UDT_Alarm.
4. Crear DB_Global_IO.
5. Crear FB_MotorControl.
6. Llamar FB_MotorControl desde OB1.
7. Asociar tags reales desde lista IO.
8. Validar seguridad, emergencia e interlocks antes de probar en terreno.

Advertencia:
Este paquete es una base de ingenierÃ­a. Debe ser revisado por personal calificado antes de usarlo en una mÃ¡quina real.
"""

    path = os.path.join(OUTPUT_DIR, "README_Implementacion_TIA.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return path, text


def generate_engineering_package():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = []

    tags_path, tags_result = generate_plc_tags()
    if tags_path:
        files.append(tags_path)

    ob1_path, _ = generate_ob1_st()
    fb_path, _ = generate_fb_motor_st()
    db_path, _ = generate_db_structure()
    readme_path, _ = generate_readme()

    files.extend([ob1_path, fb_path, db_path, readme_path])

    summary = f"""
Paquete de ingenierÃ­a generado correctamente.

Archivos:
{chr(10).join(files)}
"""

    return files, summary



