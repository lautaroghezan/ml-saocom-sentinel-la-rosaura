from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path.cwd()

ENTRADA = BASE / (
    "data/processed/"
    "piloto_saocom_L02_multipolarizacion_20241009.csv"
)

SALIDA_TABLA = BASE / (
    "reports/tables/"
    "diagnostico_HV_VH_L02_20241009.csv"
)

SALIDA_FIGURA = BASE / (
    "reports/figures/"
    "diagnostico_HV_VH_L02_20241009.png"
)

df = pd.read_csv(ENTRADA)

datos = df.dropna(subset=["HV_db", "VH_db"]).copy()

if len(datos) < 3:
    raise ValueError("No hay suficientes observaciones completas.")

datos["diferencia_HV_VH_db"] = (
    datos["HV_db"] - datos["VH_db"]
)

datos["diferencia_absoluta_db"] = (
    datos["diferencia_HV_VH_db"].abs()
)

print("\n=== DIAGNOSTICO HV-VH ===")
print("Observaciones completas:", len(datos))

print("\n=== DIFERENCIAS HV - VH ===")
print(
    datos["diferencia_HV_VH_db"]
    .describe()
    .round(3)
    .to_string()
)

print("\nDiferencia absoluta mediana (dB):",
      round(datos["diferencia_absoluta_db"].median(), 3))

print("Diferencia absoluta maxima (dB):",
      round(datos["diferencia_absoluta_db"].max(), 3))

print("\n=== CORRELACIONES ===")
print(
    "Pearson:",
    round(datos["HV_db"].corr(datos["VH_db"]), 3)
)
print(
    "Spearman:",
    round(
        datos["HV_db"].corr(datos["VH_db"], method="spearman"),
        3
    )
)

print("\n=== MAYORES DIFERENCIAS ABSOLUTAS ===")
print(
    datos.nlargest(10, "diferencia_absoluta_db")[
        [
            "fila", "columna", "x_utm", "y_utm",
            "HV_db", "VH_db",
            "diferencia_HV_VH_db"
        ]
    ].round(3).to_string(index=False)
)

SALIDA_TABLA.parent.mkdir(parents=True, exist_ok=True)
SALIDA_FIGURA.parent.mkdir(parents=True, exist_ok=True)

datos.to_csv(
    SALIDA_TABLA,
    index=False,
    encoding="utf-8-sig"
)

fig, ax = plt.subplots(figsize=(7, 6))

ax.scatter(
    datos["HV_db"],
    datos["VH_db"],
    alpha=0.75,
    s=35
)

limite_min = min(
    datos["HV_db"].min(),
    datos["VH_db"].min()
) - 1

limite_max = max(
    datos["HV_db"].max(),
    datos["VH_db"].max()
) + 1

ax.plot(
    [limite_min, limite_max],
    [limite_min, limite_max],
    linestyle="--",
    color="black",
    linewidth=1,
    label="Igualdad HV = VH"
)

ax.set_xlim(limite_min, limite_max)
ax.set_ylim(limite_min, limite_max)
ax.set_aspect("equal", adjustable="box")

ax.set_xlabel("HV (dB)")
ax.set_ylabel("VH (dB)")
ax.set_title("La Rosaura - L02 | SAOCOM 09/10/2024")
ax.legend()
ax.grid(alpha=0.2)

plt.tight_layout()
plt.savefig(
    SALIDA_FIGURA,
    dpi=220,
    bbox_inches="tight"
)
plt.close(fig)

print("\n=== ARCHIVOS GENERADOS ===")
print("Tabla:", SALIDA_TABLA)
print("Figura:", SALIDA_FIGURA)
