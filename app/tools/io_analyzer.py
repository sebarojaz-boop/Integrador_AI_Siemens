import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IO_FOLDER = os.path.join(BASE_DIR, "data", "io")


def find_io_file():
    if not os.path.exists(IO_FOLDER):
        return None

    for file in os.listdir(IO_FOLDER):
        if file.lower().endswith(".xlsx"):
            return os.path.join(IO_FOLDER, file)

    return None


def analyze_io_list():
    file_path = find_io_file()

    if file_path is None:
        return "No encontré archivo Excel en data/io."

    df = pd.read_excel(file_path)

    resumen = []
    resumen.append(f"Archivo analizado: {os.path.basename(file_path)}")
    resumen.append(f"Total de filas: {len(df)}")
    resumen.append(f"Columnas detectadas: {list(df.columns)}")

    text = df.head(50).to_string(index=False)

    return "\n".join(resumen) + "\n\nPrimeras señales detectadas:\n" + text