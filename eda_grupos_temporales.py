from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data/processed/dataset_sentinel2_potreros.csv")
df["fecha"] = pd.to_datetime(df["fecha"])

df = df.loc[
    df["NDVI_mediana"].notna()
    & (df["pct_validos_scl"] >= 80)
].copy()

grupos = {
    "A - Recuperacion final": [
        "L01", "L02", "L04", "L06", "L07",
        "L08", "L09", "L10", "L11", "L13", "L14"
    ],
    "B - Oscilaciones sucesivas": ["L05", "L12"],
    "C - Cambios pronunciados": ["L03", "L15", "L16"]
}

colores = ["#16865D", "#2563A6", "#C58A32"]

fig, axes = plt.subplots(
    3, 1, figsize=(13, 12),
    sharex=True, sharey=True
)

for ax, ((nombre, lotes), color) in zip(
    axes, zip(grupos.items(), colores)
):
    datos = df[df["lote_id"].isin(lotes)]

    for lote in lotes:
        d = datos[datos["lote_id"] == lote].sort_values("fecha")

        ax.plot(
            d["fecha"],
            d["NDVI_mediana"],
            linewidth=1.3,
            alpha=0.65,
            label=lote
        )

    mediana = (
        datos.groupby("fecha")["NDVI_mediana"]
        .median()
        .sort_index()
    )

    ax.plot(
        mediana.index,
        mediana.values,
        color="black",
        linewidth=2.8,
        label="Mediana del grupo",
        zorder=10
    )

    ax.set_title(nombre)
    ax.set_ylabel("NDVI mediano")
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.2)
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        fontsize=8,
        ncol=1
    )

axes[-1].set_xlabel("Fecha de adquisición")
axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
axes[-1].xaxis.set_major_formatter(
    mdates.DateFormatter("%b %Y")
)

fig.suptitle(
    "La Rosaura - Comparacion exploratoria de patrones temporales NDVI",
    fontsize=15
)

fig.tight_layout(rect=[0, 0, 0.88, 0.97])

salida = Path("reports/figures")
salida.mkdir(parents=True, exist_ok=True)

archivo = salida / "eda_ndvi_grupos_exploratorios.png"

fig.savefig(archivo, dpi=220, bbox_inches="tight")
plt.close(fig)

print("Grafico generado:", archivo)
print("Grupos exploratorios:", len(grupos))
print("Lotes incluidos:", sum(len(x) for x in grupos.values()))
