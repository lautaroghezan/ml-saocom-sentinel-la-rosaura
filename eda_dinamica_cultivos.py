from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data/processed/dataset_sentinel2_potreros.csv")
df["fecha"] = pd.to_datetime(df["fecha"])

d = df.loc[
    df["NDVI_mediana"].notna()
    & (df["pct_validos_scl"] >= 80)
].copy()

d = d.sort_values(["lote_id", "fecha"])

figuras = Path("reports/figures")
tablas = Path("reports/tables")
figuras.mkdir(parents=True, exist_ok=True)
tablas.mkdir(parents=True, exist_ok=True)

# Un panel para cada uno de los 16 lotes.
lotes = sorted(df["lote_id"].unique())
fig, axes = plt.subplots(
    4, 4, figsize=(16, 11), sharex=True, sharey=True
)

for ax, lote in zip(axes.flat, lotes):
    grupo = d[d["lote_id"] == lote]

    ax.plot(
        grupo["fecha"],
        grupo["NDVI_mediana"],
        color="#16865D",
        marker="o",
        markersize=3,
        linewidth=1.4
    )

    ax.set_title(lote)
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.2)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

fig.suptitle(
    "La Rosaura — Evolución temporal del NDVI por lote (2024/25)",
    fontsize=15
)
fig.supxlabel("Fecha de adquisición")
fig.supylabel("NDVI mediano")
fig.tight_layout()

archivo = figuras / "eda_ndvi_paneles_por_lote.png"
fig.savefig(archivo, dpi=220, bbox_inches="tight")
plt.close(fig)

# Resumen estadístico de la dinámica temporal.
resumen = (
    d.groupby("lote_id")["NDVI_mediana"]
    .agg(
        n_observaciones="count",
        minimo="min",
        maximo="max",
        mediana="median",
        desviacion="std"
    )
)

resumen["amplitud"] = resumen["maximo"] - resumen["minimo"]

resumen.to_csv(
    tablas / "eda_ndvi_dinamica_por_lote.csv"
)

print("\n=== EDA TEMPORAL NDVI ===")
print("Observaciones:", len(d))
print("Fechas:", d["fecha"].nunique())
print("Lotes:", d["lote_id"].nunique())
print("\nResumen por lote:")
print(resumen.round(3).to_string())
print("\nGrafico guardado en:", archivo)
