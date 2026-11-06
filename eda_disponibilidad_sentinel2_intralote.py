from pathlib import Path
import pandas as pd

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_sentinel2_intralote.csv"
)

salida = BASE / "reports/tables"
salida.mkdir(parents=True, exist_ok=True)

por_fecha = datos.groupby("fecha").agg(
    pixeles=("valido_scl", "size"),
    validos=("valido_scl", "sum")
).reset_index()

por_fecha["pct_validos"] = (
    100 * por_fecha["validos"] / por_fecha["pixeles"]
)

por_lote = datos.groupby("lote_id").agg(
    observaciones=("valido_scl", "size"),
    validas=("valido_scl", "sum"),
    celdas=("fila", "nunique")
).reset_index()

# Reemplazamos el conteo de filas por el de pares
# espaciales unicos (fila, columna).
celdas = (
    datos[["lote_id", "fila", "columna"]]
    .drop_duplicates()
    .groupby("lote_id")
    .size()
)

por_lote["celdas"] = (
    por_lote["lote_id"].map(celdas)
)

por_lote["pct_validos"] = (
    100 * por_lote["validas"] / por_lote["observaciones"]
)

por_fecha.to_csv(
    salida / "disponibilidad_sentinel2_intralote_por_fecha.csv",
    index=False
)

por_lote.to_csv(
    salida / "disponibilidad_sentinel2_intralote_por_lote.csv",
    index=False
)

print("\n=== DISPONIBILIDAD POR FECHA ===")
print(
    por_fecha[
        ["fecha", "pct_validos"]
    ].to_string(index=False, float_format="%.2f")
)

print("\n=== DISPONIBILIDAD POR LOTE ===")
print(
    por_lote[
        ["lote_id", "celdas", "pct_validos"]
    ].to_string(index=False, float_format="%.2f")
)

print("\n=== RESUMEN ===")
print(
    "Fechas con >=80% de pixeles validos:",
    int((por_fecha["pct_validos"] >= 80).sum())
)
print(
    "Fechas con 0% de pixeles validos:",
    int((por_fecha["pct_validos"] == 0).sum())
)
print(
    "Disponibilidad media:",
    round(por_fecha["pct_validos"].mean(), 2)
)

print("\nDiagnostico finalizado.")
