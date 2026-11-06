from pathlib import Path
import pandas as pd
import numpy as np

base = Path.cwd() / "data/processed"

nuevo = pd.read_csv(
    base / "dataset_sentinel2_intralote.csv"
)

original = pd.read_csv(
    base / "dataset_sentinel2_potreros.csv"
)

print("\n=== ESTRUCTURA DEL DATASET ORIGINAL ===")
print("Registros:", len(original))
print("Columnas:")
for columna in original.columns:
    print(" ", columna)

print("\n=== VALIDACION DE COBERTURA ===")

agrupado = nuevo.groupby(
    ["fecha", "lote_id"]
).agg(
    n_pixeles_nuevo=("fila", "size"),
    n_validos_nuevo=("valido_scl", "sum"),
    ndvi_media_nueva=("NDVI", "mean"),
    ndre_media_nueva=("NDRE", "mean"),
    ndmi_media_nueva=("NDMI", "mean")
).reset_index()

comparacion = original.merge(
    agrupado,
    on=["fecha", "lote_id"],
    how="outer",
    indicator=True
)

print("Combinaciones nuevo:", len(agrupado))
print("Combinaciones original:", len(original))
print("Combinaciones comparadas:", len(comparacion))
print("Estado de coincidencias:")
print(comparacion["_merge"].value_counts().to_string())

print("\n=== COMPARACION DE PIXELES ===")

for anterior, actual in [
    ("n_pixeles", "n_pixeles_nuevo"),
    ("n_validos_scl", "n_validos_nuevo")
]:
    if anterior in comparacion.columns:
        pares = comparacion[
            [anterior, actual]
        ].dropna()

        diferencias = (
            pares[anterior] - pares[actual]
        ).abs()

        print(f"\n{anterior}:")
        print("Pares:", len(pares))
        print("Coincidencias exactas:",
              int((diferencias == 0).sum()))
        print("Diferencia maxima:",
              diferencias.max() if len(diferencias) else "N/D")

print("\n=== COLUMNAS DE INDICES EN ORIGINAL ===")
for nombre in ["ndvi", "ndre", "ndmi"]:
    print(
        nombre,
        [
            c for c in original.columns
            if nombre in c.lower()
        ]
    )

print("\nDiagnostico finalizado.")
