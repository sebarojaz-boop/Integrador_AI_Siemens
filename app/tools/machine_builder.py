import os
import zipfile
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)

PACKAGE_DIR = os.path.join(
    OUTPUT_DIR,
    "TIA_Architecture_Package"
)


# =========================
# WRITE FILE
# =========================
def write_file(path, content):

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)


# =========================
# GENERAR PDF
# =========================
def generate_tia_manual_pdf(project_name):

    pdf_path = os.path.join(
        PACKAGE_DIR,
        "00_GUIA_TIA_PORTAL.pdf"
    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph(
        f"<b>GUIA IMPLEMENTACION TIA PORTAL</b><br/>{project_name}",
        styles['Title']
    )

    elements.append(title)
    elements.append(Spacer(1, 20))

    sections = [

        (
            "1. Crear Proyecto",
            """
Abrir TIA Portal â†’ Create new project â†’ asignar nombre â†’
Create.
"""
        ),

        (
            "2. Agregar PLC",
            """
Devices & Networks â†’ Add new device â†’
Controller â†’ seleccionar S7-1200 o S7-1500 â†’
Add.
"""
        ),

        (
            "3. Crear UDTs",
            """
PLC data types â†’ Add new data type.

Crear:
- UDT_Motor
- UDT_Valve
- UDT_Alarm

Copiar estructuras desde:
05_DB_UDT_Structure.txt
"""
        ),

        (
            "4. Crear DB Global",
            """
Program blocks â†’ Add new block â†’
Data block â†’ DB_Global_IO â†’
Optimized block access.
"""
        ),

        (
            "5. Crear FB_MotorControl",
            """
Program blocks â†’ Add new block â†’
Function Block â†’
Language: SCL â†’
Pegar contenido de:
02_FB_MotorControl_ST.txt
"""
        ),

        (
            "6. Crear FB_ValveControl",
            """
Crear Function Block SCL â†’
Pegar contenido:
03_FB_ValveControl_ST.txt
"""
        ),

        (
            "7. Crear FB_SequenceManager",
            """
Crear Function Block SCL â†’
Pegar contenido:
04_FB_SequenceManager_ST.txt
"""
        ),

        (
            "8. Editar OB1",
            """
Abrir Main [OB1] â†’
usar estructura:
06_OB1_MainCycle_ST.txt
"""
        ),

        (
            "9. PLC Tags",
            """
Abrir PLC Tags â†’
crear tabla â†’
usar:
PLC_Tags_TIA.xlsx
"""
        ),

        (
            "10. Compilar",
            """
Click derecho PLC â†’
Compile â†’ Software.
"""
        ),

        (
            "11. Descargar al PLC",
            """
Download to device â†’
seleccionar Ethernet â†’
Load.
"""
        ),

        (
            "12. Seguridad",
            """
Validar:
- E-Stop
- interlocks
- feedbacks
- simulaciÃ³n
antes de terreno.
"""
        )
    ]

    for title_text, body in sections:

        elements.append(
            Paragraph(
                f"<b>{title_text}</b>",
                styles['Heading2']
            )
        )

        elements.append(
            Spacer(1, 8)
        )

        elements.append(
            Paragraph(
                body,
                styles['BodyText']
            )
        )

        elements.append(
            Spacer(1, 18)
        )

    elements.append(PageBreak())

    footer = Paragraph(
        """
<b>IMPORTANTE:</b><br/>
Este paquete fue generado automÃ¡ticamente por SCA AI Engineering Assistant.<br/>
Todo proyecto debe validarse por un ingeniero calificado antes de puesta en marcha.
""",
        styles['BodyText']
    )

    elements.append(footer)

    doc.build(elements)

    return pdf_path


# =========================
# BUILD PACKAGE
# =========================
def build_machine_architecture(
    project_name="Proyecto_Industrial_Siemens"
):

    os.makedirs(
        PACKAGE_DIR,
        exist_ok=True
    )

    files = []

    pdf_manual = generate_tia_manual_pdf(
        project_name
    )

    files.append(pdf_manual)

    architecture = f"""
Arquitectura TIA Portal

OBs:
- OB1_MainCycle
- OB100_Startup

FBs:
- FB_MotorControl
- FB_ValveControl
- FB_SequenceManager

DBs:
- DB_Global_IO
- DB_Alarms
- DB_HMI

UDTs:
- UDT_Motor
- UDT_Valve
- UDT_Alarm
"""

    path = os.path.join(
        PACKAGE_DIR,
        "01_Arquitectura_TIA.txt"
    )

    write_file(path, architecture)

    files.append(path)

    fb_motor = """
FUNCTION_BLOCK FB_MotorControl
{ S7_Optimized_Access := 'TRUE' }

VAR_INPUT
    StartCmd : Bool;
    StopCmd : Bool;
    SafetyOK : Bool;
END_VAR

VAR_OUTPUT
    RunCmd : Bool;
END_VAR

BEGIN

    IF SafetyOK THEN

        IF StartCmd THEN
            RunCmd := TRUE;
        END_IF;

        IF StopCmd THEN
            RunCmd := FALSE;
        END_IF;

    ELSE
        RunCmd := FALSE;
    END_IF;

END_FUNCTION_BLOCK
"""

    path = os.path.join(
        PACKAGE_DIR,
        "02_FB_MotorControl_ST.txt"
    )

    write_file(path, fb_motor)

    files.append(path)

    ob1 = """
// OB1

REGION Inputs
END_REGION

REGION Safety
END_REGION

REGION Equipment
END_REGION

REGION Outputs
END_REGION
"""

    path = os.path.join(
        PACKAGE_DIR,
        "03_OB1_ST.txt"
    )

    write_file(path, ob1)

    files.append(path)

    zip_path = os.path.join(
        OUTPUT_DIR,
        "TIA_Architecture_Package.zip"
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for file in files:

            zipf.write(
                file,
                os.path.basename(file)
            )

    return zip_path, files



