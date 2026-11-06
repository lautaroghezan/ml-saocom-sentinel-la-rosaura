from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path.cwd()
ENTRADA = BASE / "data/processed/dataset_sentinel2_intralote.csv"
SALIDA = BASE / "reports/tables/eda_variabilidad_ndvi_intralote.csv"

datos = pd.read_csv(ENTRADA)

resumen = (
    datos.groupby(["fecha", "lote_id"])
    .agg(
        n_pixeles=("fila", "size"),
        n_validos=("NDVI", "count"),
        ndvi_mediana=("NDVI", "median"),
        ndvi_p25=("NDVI", lambda x: x.quantile(0.25)),
        ndvi_p75=("NDVI", lambda x: x.quantile(0.75)),
        ndvi_std=("NDVI", "std")
    )
    .reset_index()
)

resumen["ndvi_iqr"] = (
    resumen["ndvi_p75"] - resumen["ndvi_p25"]
)

resumen["pct_validos"] = (
    100 * resumen["n_validos"] / resumen["n_pixeles"]
)

# Umbral exploratorio para comparar dispersiones
# con suficiente cobertura espacial.
elegibles = resumen.loc[
    (resumen["pct_validos"] >= 80)
    & (resumen["n_validos"] >= 2)
].copy()

SALIDA.parent.mkdir(parents=True, exist_ok=True)
resumen.to_csv(SALIDA, index=False)

print("\n=== VARIABILIDAD ESPACIAL NDVI ===")
print("Combinaciones fecha-lote:", len(resumen))
print("Combinaciones con >=80% cobertura:", len(elegibles))

print("\n=== DISTRIBUCION DEL IQR INTRALOTE ===")
print(
    elegibles["ndvi_iqr"].describe(
        percentiles=[0.10, 0.25, 0.50, 0.75, 0.90]
    ).to_string()
)

print("\n=== DIEZ MAYORES IQR ===")
print(
    elegibles.nlargest(10, "ndvi_iqr")[
        [
            "fecha", "lote_id", "n_validos",
            "pct_validos", "ndvi_mediana", "ndvi_iqr"
        ]
    ].to_string(index=False, float_format="%.4f")
)

print("\n=== MEDIANA DEL IQR POR LOTE ===")
por_lote = (
    elegibles.groupby("lote_id")["ndvi_iqr"]
    .median()
    .sort_values(ascending=False)
)
print(por_lote.to_string(float_format="%.4f"))

print("\nArchivo generado:", SALIDA)
print("Diagnostico finalizado.")
