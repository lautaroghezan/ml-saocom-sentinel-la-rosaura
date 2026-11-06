from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path.cwd()

ENTRADA = BASE / (
    "data/processed/"
    "piloto_saocom_L02_multipolarizacion_20241009.csv"
)

FIGURA = BASE / (
    "reports/figures/"
    "correlaciones_saocom_L02_20241009.png"
)

TABLA = BASE / (
    "reports/tables/"
    "correlaciones_saocom_L02_20241009.csv"
)

df = pd.read_csv(ENTRADA)

variables = ["HH_db", "HV_db", "VH_db", "VV_db"]

completos = df.dropna(subset=variables).copy()
incompletos = df[df[variables].isna().any(axis=1)]

print("\n=== CONTROL DE CALIDAD ===")
print("Observaciones totales:", len(df))
print("Observaciones completas:", len(completos))
print("Observaciones incompletas:", len(incompletos))

if not incompletos.empty:
    print("\n=== PIXELES INCOMPLETOS ===")
    print(
        incompletos[
            ["fila", "columna", "x_utm", "y_utm"] + variables
        ].to_string(index=False)
    )

if len(completos) < 3:
    raise ValueError("No hay suficientes registros completos.")

pearson = completos[variables].corr(method="pearson")
spearman = completos[variables].corr(method="spearman")

print("\n=== CORRELACION PEARSON ===")
print(pearson.round(3).to_string())

print("\n=== CORRELACION SPEARMAN ===")
print(spearman.round(3).to_string())

FIGURA.parent.mkdir(parents=True, exist_ok=True)
TABLA.parent.mkdir(parents=True, exist_ok=True)

pearson.to_csv(TABLA, encoding="utf-8-sig")

fig, ax = plt.subplots(figsize=(7, 6))

imagen = ax.imshow(
    pearson.values,
    cmap="coolwarm",
    vmin=-1,
    vmax=1
)

ax.set_xticks(range(len(variables)))
ax.set_yticks(range(len(variables)))

ax.set_xticklabels(variables)
ax.set_yticklabels(variables)

for i in range(len(variables)):
    for j in range(len(variables)):
        valor = pearson.iloc[i, j]
        color = "white" if abs(valor) > 0.6 else "black"

        ax.text(
            j, i,
            f"{valor:.2f}",
            ha="center",
            va="center",
            color=color,
            fontsize=12
        )

barra = fig.colorbar(imagen, ax=ax, shrink=0.8)
barra.set_label("Correlacion de Pearson")

ax.set_title(
    "La Rosaura - L02\n"
    "Correlaciones SAOCOM | 09/10/2024"
)

plt.tight_layout()
plt.savefig(FIGURA, dpi=220, bbox_inches="tight")
plt.close(fig)

print("\n=== ARCHIVOS GENERADOS ===")
print("Tabla:", TABLA)
print("Figura:", FIGURA)
