from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data/processed/dataset_saocom_potreros.csv")

matriz = df.pivot(
    index=["fecha", "lote_id"],
    columns="polarizacion",
    values="mediana_db"
)

polarizaciones = ["HH", "HV", "VH", "VV"]
matriz = matriz[polarizaciones]

# Correlaciones generales
corr_general = matriz.corr()

# Correlaciones por lote
resultados = []

for lote, datos in matriz.groupby(level="lote_id"):
    corr = datos.corr()

    resultados.append({
        "lote_id": lote,
        "HH_VV": corr.loc["HH", "VV"],
        "HV_VH": corr.loc["HV", "VH"],
        "HH_HV": corr.loc["HH", "HV"],
        "VV_VH": corr.loc["VV", "VH"]
    })

resumen = pd.DataFrame(resultados).sort_values("lote_id")

figuras = Path("reports/figures")
tablas = Path("reports/tables")
figuras.mkdir(parents=True, exist_ok=True)
tablas.mkdir(parents=True, exist_ok=True)

resumen.to_csv(
    tablas / "eda_saocom_correlaciones_por_lote.csv",
    index=False
)

corr_general.to_csv(
    tablas / "eda_saocom_correlaciones_generales.csv"
)

# Mapa de calor de correlaciones por lote
valores = resumen[["HH_VV", "HV_VH", "HH_HV", "VV_VH"]].values

fig, ax = plt.subplots(figsize=(9, 7))

im = ax.imshow(
    valores,
    cmap="coolwarm",
    vmin=-1,
    vmax=1,
    aspect="auto"
)

ax.set_xticks(range(4))
ax.set_xticklabels(["HH–VV", "HV–VH", "HH–HV", "VV–VH"])

ax.set_yticks(range(len(resumen)))
ax.set_yticklabels(resumen["lote_id"])

for i in range(valores.shape[0]):
    for j in range(valores.shape[1]):
        ax.text(
            j, i,
            f"{valores[i, j]:.2f}",
            ha="center",
            va="center",
            fontsize=8
        )

fig.colorbar(im, ax=ax, label="Correlación de Pearson")
ax.set_title("SAOCOM — Correlaciones entre polarizaciones por lote")
fig.tight_layout()

archivo = figuras / "eda_saocom_correlaciones_por_lote.png"
fig.savefig(archivo, dpi=220, bbox_inches="tight")
plt.close(fig)

print("\n=== CORRELACIONES GENERALES ===")
print(corr_general.round(3).to_string())

print("\n=== CORRELACIONES POR LOTE ===")
print(resumen.round(3).to_string())

print("\nGrafico:", archivo)
