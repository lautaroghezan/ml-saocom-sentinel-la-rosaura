import pandas as pd
from pathlib import Path

ruta = Path(
    "data/processed/clusters_intralote_L15_L16.csv"
)

df = pd.read_csv(ruta)

print("\n=== PASO 19A: AUDITORIA PARA ML SUPERVISADO ===")

print("\nDimensiones:")
print(df.shape)

print("\nColumnas:")
for columna in df.columns:
    print(" -", columna)

print("\nValores faltantes:")
faltantes = df.isna().sum()
print(faltantes[faltantes > 0].to_string()
      if faltantes.sum() else "Ninguno")

print("\nDistribucion de pseudoetiquetas:")
for columna in [
    "cluster_optico_intralote",
    "cluster_multi_intralote"
]:
    if columna in df.columns:
        print(f"\n{columna}:")
        print(
            pd.crosstab(
                df["lote_id"],
                df[columna]
            ).to_string()
        )

print("\nDuplicados por lote y celda:")
print(
    df.duplicated(["lote_id", "celda_id"]).sum()
)

print("\n=== AUDITORIA FINALIZADA ===")
