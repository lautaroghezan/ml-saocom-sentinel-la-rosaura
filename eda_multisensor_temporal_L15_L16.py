from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

entrada = Path("data/processed/dataset_multisensor_L15_L16.csv")
salida = Path("reports/figures/eda_multisensor_temporal_L15_L16.png")
salida.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(entrada, parse_dates=["fecha"])

variables = ["NDVI", "HH_db", "HV_db", "VH_db", "VV_db"]
lotes = ["L15", "L16"]

fig, axes = plt.subplots(
    5, 2, figsize=(14, 15),
    sharex=True
)

for j, lote in enumerate(lotes):
    d = df[df["lote_id"] == lote]

    resumen = (
        d.groupby("fecha")
        .agg(
            total=("lote_id", "size"),
            con_ndvi=("NDVI", "count"),
            **{
                v: (v, "median")
                for v in variables
            }
        )
        .sort_index()
    )

    resumen["cobertura"] = (
        resumen["con_ndvi"] / resumen["total"]
    )

    for i, variable in enumerate(variables):
        ax = axes[i, j]

        valores = resumen[variable].copy()

        # Para NDVI, no graficar medianas basadas
        # en menos del 70 % de las celdas.
        if variable == "NDVI":
            valores = valores.where(
                resumen["cobertura"] >= 0.70
            )

        ax.plot(
            resumen.index,
            valores,
            marker="o",
            linewidth=1.8,
            markersize=4,
            color="#D97706" if j == 0 else "#2563EB"
        )

        ax.axvspan(
            pd.Timestamp("2025-01-29"),
            pd.Timestamp("2025-02-16"),
            color="#F59E0B",
            alpha=0.12
        )

        ax.set_ylabel(variable)
        ax.grid(alpha=0.25)

        if i == 0:
            ax.set_title(
                f"{lote} | NDVI y radar",
                fontsize=12,
                fontweight="bold"
            )
            ax.set_ylim(0, 1)

        ax.tick_params(
            axis="x",
            rotation=35,
            labelsize=9
        )

fig.suptitle(
    "EDA multisensor temporal | La Rosaura | 2024-2025",
    fontsize=15,
    fontweight="bold"
)

fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(salida, dpi=200, bbox_inches="tight")
plt.close(fig)

print("\nPASO 16B COMPLETADO")
print("Figura:", salida.resolve())
print("Observaciones:", len(df))
print("Fechas radar:", df["fecha"].nunique())
print("Variables:", ", ".join(variables))
print("El NDVI se omite si su cobertura es menor al 70 %.")
print("Las series radar usan todas las celdas disponibles.")
