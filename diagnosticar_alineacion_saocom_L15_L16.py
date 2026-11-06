from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_saocom_intralote.csv"
)

FECHA_1 = "2025-01-29"
FECHA_2 = "2025-02-14"
LOTES = ["L15", "L16"]

resultados = []

for lote in LOTES:

    a = datos.loc[
        (datos["lote_id"] == lote)
        & (datos["fecha"] == FECHA_1)
    ].copy()

    b = datos.loc[
        (datos["lote_id"] == lote)
        & (datos["fecha"] == FECHA_2)
    ].copy()

    if a.empty or b.empty:
        raise ValueError(f"Faltan datos para {lote}")

    coordenadas_a = a[["x_utm", "y_utm"]].to_numpy()
    coordenadas_b = b[["x_utm", "y_utm"]].to_numpy()

    arbol = cKDTree(coordenadas_a)

    distancias, indices = arbol.query(
        coordenadas_b,
        k=1
    )

    resultados.append({
        "lote_id": lote,
        "pixeles_fecha_1": len(a),
        "pixeles_fecha_2": len(b),
        "distancia_min_m": float(np.min(distancias)),
        "distancia_mediana_m": float(np.median(distancias)),
        "distancia_max_m": float(np.max(distancias)),
        "pct_distancia_20m": float(
            100 * np.mean(distancias <= 20)
        ),
        "pct_distancia_30m": float(
            100 * np.mean(distancias <= 30)
        ),
        "centros_unicos_asociados": int(
            len(np.unique(indices))
        )
    })

resultado = pd.DataFrame(resultados)

SALIDA = (
    BASE / "reports/tables"
    / "diagnostico_alineacion_saocom_L15_L16.csv"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)
resultado.to_csv(SALIDA, index=False)

print("\n=== ALINEACION ESPACIAL SAOCOM ===")
print(
    resultado.to_string(
        index=False,
        float_format="%.3f"
    )
)

print("\nArchivo:", SALIDA)
print("Diagnostico finalizado.")
