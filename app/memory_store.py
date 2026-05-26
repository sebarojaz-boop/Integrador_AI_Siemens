import os
import json

# =========================
# RUTAS
# =========================
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MEMORY_DIR = os.path.join(
    BASE_DIR,
    "memory"
)

CHAT_FILE = os.path.join(
    MEMORY_DIR,
    "chat_history.json"
)

# =========================
# CARGAR CHAT
# =========================
def load_chat_history():

    os.makedirs(
        MEMORY_DIR,
        exist_ok=True
    )

    if not os.path.exists(CHAT_FILE):
        return []

    try:

        with open(
            CHAT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(
            f"Error cargando memoria: {e}"
        )

        return []

# =========================
# GUARDAR CHAT
# =========================
def save_chat_history(messages):

    os.makedirs(
        MEMORY_DIR,
        exist_ok=True
    )

    try:

        with open(
            CHAT_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                messages,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print(
            f"Error guardando memoria: {e}"
        )

# =========================
# LIMPIAR CHAT
# =========================
def clear_chat_history():

    os.makedirs(
        MEMORY_DIR,
        exist_ok=True
    )

    try:

        with open(
            CHAT_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump([], f)

    except Exception as e:

        print(
            f"Error limpiando memoria: {e}"
        )