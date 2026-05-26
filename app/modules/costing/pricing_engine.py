import os
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def generate_commercial_estimate(
    hh_dict,
    hourly_rate=35000,
    margin_percent=25,
    project_name="Licitación Industrial"
):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    rows = []

    for item, hh in hh_dict.items():
        if item == "TOTAL HH":
            continue

        subtotal = hh * hourly_rate

        rows.append({
            "Item": item,
            "HH": hh,
            "Valor HH CLP": hourly_rate,
            "Subtotal CLP": round(subtotal, 0)
        })

    df = pd.DataFrame(rows)

    direct_cost = float(df["Subtotal CLP"].sum()) if not df.empty else 0
    margin_value = direct_cost * (margin_percent / 100)
    final_price = direct_cost + margin_value

    summary_rows = pd.DataFrame([
        {"Item": "Costo directo", "HH": "", "Valor HH CLP": "", "Subtotal CLP": round(direct_cost, 0)},
        {"Item": f"Margen {margin_percent}%", "HH": "", "Valor HH CLP": "", "Subtotal CLP": round(margin_value, 0)},
        {"Item": "Precio venta estimado", "HH": "", "Valor HH CLP": "", "Subtotal CLP": round(final_price, 0)}
    ])

    output_path = os.path.join(OUTPUT_DIR, "Estimacion_Economica_Licitacion.xlsx")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="HH", index=False)
        summary_rows.to_excel(writer, sheet_name="Resumen", index=False)

    text = f"""
ESTIMACIÓN ECONÓMICA PRELIMINAR
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Proyecto:
{project_name}

TOTAL HH:
{hh_dict.get("TOTAL HH", 0)} HH

Valor HH:
${hourly_rate:,.0f} CLP

Costo directo:
${direct_cost:,.0f} CLP

Margen:
{margin_percent}%

Precio venta estimado:
${final_price:,.0f} CLP
"""

    txt_path = os.path.join(OUTPUT_DIR, "Resumen_Economico_Licitacion.txt")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "excel_path": output_path,
        "txt_path": txt_path,
        "summary_text": text,
        "direct_cost": direct_cost,
        "final_price": final_price
    }