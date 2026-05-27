import os
import shutil
import pandas as pd
from pypdf import PdfReader
from docx import Document

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploaded_docs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def save_uploaded_file(uploaded_file):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(uploaded_file, f)

    return file_path


def read_pdf(path):
    text = ""
    reader = PdfReader(path)

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def read_docx(path):
    doc = Document(path)
    text = ""

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text + "\n"

    return text


def read_excel(path):
    text = ""
    sheets = pd.read_excel(path, sheet_name=None)

    for sheet_name, df in sheets.items():
        text += f"\n=== HOJA: {sheet_name} ===\n"
        text += df.head(300).to_string(index=False)
        text += "\n"

    return text


def read_csv(path):
    df = pd.read_csv(path)
    return df.head(300).to_string(index=False)


def read_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_document_text(path):
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return read_pdf(path)

    if ext == ".docx":
        return read_docx(path)

    if ext in [".xlsx", ".xls"]:
        return read_excel(path)

    if ext == ".csv":
        return read_csv(path)

    if ext == ".txt":
        return read_txt(path)

    return "Formato no soportado."


def process_uploaded_files(uploaded_files):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not uploaded_files:
        return "No se subieron documentos."

    all_text = ""

    for uploaded_file in uploaded_files:
        file_path = save_uploaded_file(uploaded_file)
        text = extract_document_text(file_path)

        all_text += "\n\n==============================\n"
        all_text += f"DOCUMENTO: {uploaded_file.name}\n"
        all_text += "==============================\n"
        all_text += text[:15000]

    output_path = os.path.join(OUTPUT_DIR, "Resumen_Documentos_Subidos.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(all_text)

    return all_text


