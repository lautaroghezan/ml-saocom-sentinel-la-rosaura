from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path.cwd()

archivo = BASE / (
    "data/processed/"
    "piloto_saocom_L02_multipolarizacion_20241009.csv"
)

df = pd.read_csv(archivo)

datos = df.dropna(
    subset=["HV_db", "VH_db"]
).copy()

datos["diferencia_abs"] = (
    datos["HV_db"] - datos["VH_db"]
).abs()

def evaluar(nombre, muestra):
    n = len(muestra)

    if n < 3:
        print(f"{nombre}: observaciones insuficientes")
        return

    pearson = muestra["HV_db"].corr(
        muestra["VH_db"],
        method="pearson"
    )

    spearman = muestra["HV_db"].corr(
        muestra["VH_db"],
        method="spearman"
    )

    print(
        f"{nombre:30s} "
        f"n={n:3d} | "
        f"Pearson={pearson:7.3f} | "
        f"Spearman={spearman:7.3f}"
    )

print("\n=== SENSIBILIDAD CORRELACION HV-VH ===")

evaluar("Todas las observaciones", datos)

for umbral in [10, 8, 6, 4, 3, 2]:
    muestra = datos[
        datos["diferencia_abs"] <= umbral
    ]

    evaluar(
        f"Diferencia absoluta <= {umbral} dB",
        muestra
    )

print("\n=== VALORES EXTREMOS ===")

for pol in ["HV_db", "VH_db"]:
    print(
        f"{pol}: "
        f"min={datos[pol].min():.3f}, "
        f"mediana={datos[pol].median():.3f}, "
        f"max={datos[pol].max():.3f}"
    )

print("\nNota metodologica:")
print(
    "Los filtros son exploratorios y no modifican "
    "el dataset original."
)
print(
    "Filtrar por similitud HV-VH puede aumentar "
    "artificialmente la correlacion."
)
