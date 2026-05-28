from pathlib import Path
import pandas as pd
from pypdf import PdfReader
from docx import Document


SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".csv", ".xml", ".l5x", ".json", ".py",
    ".pdf", ".xlsx", ".xls", ".docx", ".acd"
}


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def read_pdf(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception as e:
        return f"ERROR LEYENDO PDF: {e}"


def read_excel(path: Path) -> str:
    try:
        sheets = pd.read_excel(path, sheet_name=None)
        output = []
        for name, df in sheets.items():
            output.append(f"\n--- HOJA: {name} ---\n")
            output.append(df.to_string(index=False))
        return "\n".join(output)
    except Exception:
        return ""


def read_docx(path: Path) -> str:
    try:
        doc = Document(str(path))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""


def read_acd_placeholder(path: Path) -> str:
    return f"""
ARCHIVO ROCKWELL ACD DETECTADO:
Nombre: {path.name}
Ruta: {path}

IMPORTANTE:
El archivo .ACD es binario y no puede leerse directamente como texto.
Para análisis real con IA, exportar desde Studio 5000 como archivo .L5X.

Instrucción:
Studio 5000 > File > Save As > tipo .L5X
Luego copiar el archivo .L5X en data/plc_rockwell.
"""


def read_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in [".txt", ".md", ".csv", ".xml", ".l5x", ".json", ".py"]:
        return read_text_file(path)

    if suffix == ".pdf":
        return read_pdf(path)

    if suffix in [".xlsx", ".xls"]:
        return read_excel(path)

    if suffix == ".docx":
        return read_docx(path)

    if suffix == ".acd":
        return read_acd_placeholder(path)

    return ""


def scan_project_files(base_path: str):
    base = Path(base_path)

    folders = [
        base / "data" / "cotizaciones_ejemplo",
        base / "data" / "plc_rockwell",
        base / "data" / "plc_siemens",
        base / "docs" / "proyectos_historicos",
    ]

    documents = []

    print("\n🔎 Buscando archivos en:")
    for folder in folders:
        print(f" - {folder}")

    for folder in folders:
        if not folder.exists():
            print(f"⚠️ Carpeta no existe: {folder}")
            continue

        for file in folder.rglob("*"):
            if not file.is_file():
                continue

            if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                print(f"⚠️ Extensión no soportada: {file.name}")
                continue

            content = read_file(file)

            if content.strip():
                documents.append({
                    "file_name": file.name,
                    "file_path": str(file),
                    "folder": str(folder),
                    "extension": file.suffix.lower(),
                    "content": content[:100000],
                })
                print(f"✅ Cargado: {file.name}")
            else:
                print(f"⚠️ Sin texto extraíble: {file.name}")

    print(f"\n📦 Total documentos detectados: {len(documents)}")
    return documents