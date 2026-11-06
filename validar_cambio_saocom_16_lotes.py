from pathlib import Path
import pandas as pd

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_saocom_intralote.csv"
)

FECHA_ANTES = "2025-01-29"
FECHA_DESPUES = "2025-02-14"

POL = ["HH_db", "HV_db", "VH_db", "VV_db"]

seleccion = datos.loc[
    datos["fecha"].isin([FECHA_ANTES, FECHA_DESPUES])
].copy()

resumen = (
    seleccion.groupby(["lote_id", "fecha"])[POL]
    .median()
    .reset_index()
)

antes = resumen.loc[
    resumen["fecha"] == FECHA_ANTES
].set_index("lote_id")[POL]

despues = resumen.loc[
    resumen["fecha"] == FECHA_DESPUES
].set_index("lote_id")[POL]

diferencias = (
    despues - antes
).rename(columns={
    p: p.replace("_db", "_delta_db") for p in POL
})

diferencias = diferencias.reset_index()

SALIDA = (
    BASE / "reports/tables"
    / "cambios_saocom_20250129_20250214.csv"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)
diferencias.to_csv(SALIDA, index=False)

print("\n=== CAMBIOS SAOCOM EN LOS 16 LOTES ===")
print(
    diferencias.to_string(
        index=False,
        float_format="%.3f"
    )
)

print("\n=== LOTES CON DESCENSO POR POLARIZACION ===")
for columna in diferencias.columns:
    if columna.endswith("_delta_db"):
        validos = diferencias[columna].dropna()
        print(
            columna,
            "descensos:", int((validos < 0).sum()),
            "de", len(validos),
            "mediana del cambio:",
            round(validos.median(), 3)
        )

print("\nArchivo:", SALIDA)
print("Diagnostico finalizado.")
