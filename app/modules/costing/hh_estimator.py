def estimate_hh(
    io_count=100,
    scada_screens=8,
    plc_count=1,
    drives_count=0,
    complexity="media",
    includes_fat=True,
    includes_sat=True,
    includes_training=True
):
    factor = {
        "baja": 0.8,
        "media": 1.0,
        "alta": 1.35
    }.get(str(complexity).lower(), 1.0)

    engineering = 32 * factor
    plc_programming = (40 + io_count * 0.45 + plc_count * 16) * factor
    scada_programming = (24 + scada_screens * 10) * factor
    drives = drives_count * 6 * factor
    fat = (24 + io_count * 0.12) * factor if includes_fat else 0
    sat = (32 + io_count * 0.18) * factor if includes_sat else 0
    training = 16 * factor if includes_training else 0
    documentation = 24 * factor
    management = 24 * factor

    total = (
        engineering
        + plc_programming
        + scada_programming
        + drives
        + fat
        + sat
        + training
        + documentation
        + management
    )

    return {
        "Ingeniería y levantamiento": round(engineering, 1),
        "Programación PLC": round(plc_programming, 1),
        "Desarrollo HMI/SCADA": round(scada_programming, 1),
        "Configuración variadores": round(drives, 1),
        "Pruebas FAT": round(fat, 1),
        "Puesta en marcha SAT": round(sat, 1),
        "Capacitación": round(training, 1),
        "Documentación": round(documentation, 1),
        "Gestión técnica": round(management, 1),
        "TOTAL HH": round(total, 1)
    }