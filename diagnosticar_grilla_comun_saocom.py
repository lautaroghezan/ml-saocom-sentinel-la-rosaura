from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_saocom_intralote.csv"
)

FECHAS = ["2025-01-29", "2025-02-14"]
LOTES = ["L15", "L16"]
PASO = 44.0

seleccion = datos.loc[
    datos["fecha"].isin(FECHAS)
    & datos["lote_id"].isin(LOTES)
].copy()

# Grilla anclada a coordenadas UTM absolutas.
# Es un diagnostico de centros, no una reproyeccion raster.
seleccion["grid_x"] = np.floor(
    seleccion["x_utm"] / PASO
).astype(int)

seleccion["grid_y"] = np.floor(
    seleccion["y_utm"] / PASO
).astype(int)

resultados = []

for lote in LOTES:

    grupo = seleccion.loc[
        seleccion["lote_id"] == lote
    ]

    a = grupo.loc[
        grupo["fecha"] == FECHAS[0]
    ]

    b = grupo.loc[
        grupo["fecha"] == FECHAS[1]
    ]

    claves = ["grid_x", "grid_y"]

    celdas_a = set(map(tuple, a[claves].to_numpy()))
    celdas_b = set(map(tuple, b[claves].to_numpy()))

    comunes = celdas_a & celdas_b

    duplicados_a = int(a.duplicated(claves).sum())
    duplicados_b = int(b.duplicated(claves).sum())

    resultados.append({
        "lote_id": lote,
        "centros_enero": len(a),
        "centros_febrero": len(b),
        "celdas_enero": len(celdas_a),
        "celdas_febrero": len(celdas_b),
        "celdas_comunes": len(comunes),
        "pct_comunes_sobre_enero": round(
            100 * len(comunes) / len(celdas_a), 2
        ),
        "pct_comunes_sobre_febrero": round(
            100 * len(comunes) / len(celdas_b), 2
        ),
        "duplicados_enero": duplicados_a,
        "duplicados_febrero": duplicados_b
    })

resultado = pd.DataFrame(resultados)

SALIDA = (
    BASE / "reports/tables"
    / "diagnostico_grilla_comun_saocom_44m.csv"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)
resultado.to_csv(SALIDA, index=False)

print("\n=== GRILLA COMUN SAOCOM 44 m ===")
print(resultado.to_string(index=False))

print("\nIMPORTANTE:")
print("Esta prueba asigna centros a celdas de 44 m.")
print("No realiza remuestreo ni alineacion radiometrica.")
print("El resultado depende del origen de la grilla.")
print("No debe usarse aun para calcular diferencias radar.")

print("\nArchivo:", SALIDA)
print("Diagnostico finalizado.")
