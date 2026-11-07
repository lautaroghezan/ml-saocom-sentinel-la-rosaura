from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ruta = Path("data/processed/dataset_sentinel2_intralote.csv")
salida = Path("reports/figures/eda_ndvi_temporal_16_lotes.png")
salida.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ruta, parse_dates=["fecha"])

# Total de pixeles espaciales de cada lote.
totales = (
    df[["lote_id", "fila", "columna"]]
    .drop_duplicates()
    .groupby("lote_id")
    .size()
)

# Solo observaciones validas.
df = df.loc[
    df["valido_scl"].eq(True)
    & np.isfinite(df["NDVI"])
].copy()

# Mediana y cobertura por lote y fecha.
serie = (
    df.groupby(["lote_id", "fecha"], as_index=False)
    .agg(
        ndvi=("NDVI", "median"),
        n=("NDVI", "size")
    )
)

serie["total"] = serie["lote_id"].map(totales)
serie["cobertura"] = serie["n"] / serie["total"]
serie = serie.loc[serie["cobertura"] >= 0.70].copy()

lotes = sorted(totales.index.tolist())

fig, axes = plt.subplots(
    4, 4,
    figsize=(17, 12),
    sharex=True,
    sharey=True
)

for ax, lote in zip(axes.flat, lotes):
    g = (
        serie.loc[serie["lote_id"] == lote]
        .sort_values("fecha")
    )

    destacado = lote in ("L15", "L16")

    ax.plot(
        g["fecha"],
        g["ndvi"],
        marker="o",
        markersize=3.5,
        linewidth=2 if destacado else 1.3,
        color="#D97706" if destacado else "#2563EB"
    )

    ax.set_title(
        lote,
        fontsize=11,
        fontweight="bold"
    )

    ax.set_ylim(0, 1)
    ax.grid(alpha=0.25)

    if destacado:
        ax.axvspan(
            pd.Timestamp("2025-02-01"),
            pd.Timestamp("2025-02-16"),
            color="#F59E0B",
            alpha=0.18
        )

    ax.xaxis.set_major_locator(
        mdates.MonthLocator(interval=2)
    )
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%b %Y")
    )
    ax.tick_params(
        axis="x",
        labelrotation=45,
        labelsize=8
    )

fig.suptitle(
    "Evolucion temporal del NDVI por lote | La Rosaura",
    fontsize=16,
    fontweight="bold"
)

fig.supxlabel("Fecha")
fig.supylabel("NDVI mediano intralote")

fig.tight_layout(rect=[0.02, 0.02, 1, 0.96])

fig.savefig(
    salida,
    dpi=200,
    bbox_inches="tight"
)

plt.close(fig)

print("\nPASO 15C COMPLETADO")
print("Grafico:", salida.resolve())
print("Lotes representados:", len(lotes))
print("Fechas con cobertura >= 70 %:", serie["fecha"].nunique())
print("Observaciones lote-fecha:", len(serie))
