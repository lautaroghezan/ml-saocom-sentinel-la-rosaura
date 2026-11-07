import pandas as pd
import numpy as np

ruta = "data/processed/dataset_sentinel2_intralote.csv"
df = pd.read_csv(ruta, parse_dates=["fecha"])

# Mantener solamente observaciones ópticas válidas.
df = df.loc[
    df["valido_scl"].eq(True)
    & df["NDVI"].notna()
    & np.isfinite(df["NDVI"])
].copy()

# Mediana intralote por fecha.
serie = (
    df.groupby(["lote_id", "fecha"], as_index=False)
      .agg(
          ndvi_mediana=("NDVI", "median"),
          pixeles_validos=("NDVI", "size")
      )
      .sort_values(["lote_id", "fecha"])
)

# El total de píxeles se obtiene de todas las observaciones,
# incluidas las que no superaron el control de calidad.
original = pd.read_csv(ruta, usecols=["lote_id", "fila", "columna"])
totales = (
    original.groupby("lote_id")[["fila", "columna"]]
    .apply(lambda x: len(x.drop_duplicates()))
    .rename("pixeles_totales")
    .reset_index()
)

serie = serie.merge(totales, on="lote_id", how="left")
serie["cobertura"] = serie["pixeles_validos"] / serie["pixeles_totales"]

# Exigir al menos 70 % de cobertura para comparar fechas.
serie = serie.loc[serie["cobertura"] >= 0.70].copy()

resultados = []

for lote, g in serie.groupby("lote_id"):
    g = g.sort_values("fecha").reset_index(drop=True)

    # Descensos consecutivos entre observaciones separadas
    # como máximo 25 días.
    dias = g["fecha"].diff().dt.days
    delta = g["ndvi_mediana"].diff()

    candidatos = delta.where((dias > 0) & (dias <= 25))
    idx = candidatos.idxmin() if candidatos.notna().any() else None

    resultados.append({
        "lote_id": lote,
        "fechas_con_cobertura_70pct": len(g),
        "ndvi_maximo": round(g["ndvi_mediana"].max(), 3),
        "fecha_maximo": g.loc[g["ndvi_mediana"].idxmax(), "fecha"].date(),
        "mayor_caida_ndvi": (
            round(float(candidatos.loc[idx]), 3)
            if idx is not None else np.nan
        ),
        "inicio_caida": (
            g.loc[idx - 1, "fecha"].date()
            if idx is not None else None
        ),
        "fin_caida": (
            g.loc[idx, "fecha"].date()
            if idx is not None else None
        )
    })

tabla = pd.DataFrame(resultados).sort_values(
    "mayor_caida_ndvi"
)

print("\n=== ANALISIS FENOLOGICO DE LOS 16 LOTES ===")
print(tabla.to_string(index=False))

print("\nNOTA: las caidas de NDVI no identifican por si solas")
print("el cultivo ni confirman una cosecha.")
