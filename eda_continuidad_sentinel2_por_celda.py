from pathlib import Path
import pandas as pd

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_sentinel2_intralote.csv"
)

salida = BASE / "reports/tables"
salida.mkdir(parents=True, exist_ok=True)

celdas = (
    datos.groupby(["lote_id", "fila", "columna"])
    .agg(
        fechas=("fecha", "nunique"),
        fechas_validas=("valido_scl", "sum"),
        ndvi_validos=("NDVI", "count"),
        ndre_validos=("NDRE", "count"),
        ndmi_validos=("NDMI", "count")
    )
    .reset_index()
)

celdas["pct_disponibilidad"] = (
    100 * celdas["fechas_validas"] / celdas["fechas"]
)

celdas.to_csv(
    salida / "continuidad_temporal_sentinel2_por_celda.csv",
    index=False
)

print("\n=== CONTINUIDAD TEMPORAL POR CELDA ===")
print("Celdas:", len(celdas))
print("Fechas por celda (min):", celdas["fechas"].min())
print("Fechas por celda (max):", celdas["fechas"].max())

print("\n=== OBSERVACIONES VALIDAS POR CELDA ===")
print(
    celdas["fechas_validas"].describe(
        percentiles=[0.10, 0.25, 0.50, 0.75, 0.90]
    ).to_string()
)

print("\n=== UMBRALES DE DISPONIBILIDAD ===")

for umbral in [0, 10, 20, 25, 30, 35, 40]:
    cantidad = int(
        (celdas["fechas_validas"] >= umbral).sum()
    )
    print(
        f"Al menos {umbral:2d} fechas validas: "
        f"{cantidad:4d} celdas "
        f"({100*cantidad/len(celdas):.2f}%)"
    )

print("\n=== DISPONIBILIDAD DE INDICES ===")
for nombre in ["ndvi_validos", "ndre_validos", "ndmi_validos"]:
    print(
        nombre,
        "min:", celdas[nombre].min(),
        "mediana:", celdas[nombre].median(),
        "max:", celdas[nombre].max()
    )

print("\nDiagnostico finalizado.")
