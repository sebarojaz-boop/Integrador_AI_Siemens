from openai import OpenAI
from rag_engine import load_knowledge, search

# =========================
# CLIENTE OPENAI (CORRECTO)
# =========================
client = OpenAI()  # usa OPENAI_API_KEY del sistema


# =========================
# PROMPT INGENIERÃA
# =========================
SYSTEM_PROMPT = """
Eres un Ingeniero Senior Siemens experto en:

- TIA Portal
- PLC S7-1200 / S7-1500
- AutomatizaciÃ³n industrial
- Ladder / FBD / STL
- DiagnÃ³stico de fallas elÃ©ctricas

Responde con formato tÃ©cnico claro:
- DiagnÃ³stico
- Causa probable
- SoluciÃ³n
- RecomendaciÃ³n de mantenimiento
"""


# =========================
# MAIN LOOP
# =========================
def main():

    print("\nðŸ§  SCA AI Engineering Assistant")
    print("Inicializando sistema...\n")

    index, chunks = load_knowledge()

    if index is None or chunks is None:
        print("âš  Base de conocimiento no cargada.")
        return

    print("âœ” Sistema listo.\n")

    while True:

        q = input("Consulta ingeniero (o 'exit'): ")

        if q.lower() == "exit":
            break

        # =========================
        # RAG SEARCH
        # =========================
        context = search(q, index, chunks)

        context_text = "\n\n".join(context) if context else "Sin contexto tÃ©cnico disponible."

        # =========================
        # OPENAI RESPONSE (CORRECTO)
        # =========================
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=SYSTEM_PROMPT + "\n\nMANUALES:\n" + context_text + "\n\nCONSULTA:\n" + q
        )

        answer = response.output_text

        print("\nðŸ¤– RESPUESTA:\n")
        print(answer)
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()



