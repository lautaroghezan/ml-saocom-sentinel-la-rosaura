from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_sentinel2_intralote.csv"
)

lotes = gpd.read_file(
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

LOTE = "L03"

FECHAS = [
    "2024-11-03",
    "2024-12-03",
    "2024-12-28",
    "2025-01-22"
]

poligono = lotes.loc[lotes["lote_id"] == LOTE]

fig, ejes = plt.subplots(
    2, 2, figsize=(12, 10),
    sharex=True, sharey=True
)

for ax, fecha in zip(ejes.flat, FECHAS):

    muestra = datos.loc[
        (datos["lote_id"] == LOTE)
        & (datos["fecha"] == fecha)
        & datos["NDVI"].notna()
    ]

    grafico = ax.scatter(
        muestra["x_utm"],
        muestra["y_utm"],
        c=muestra["NDVI"],
        cmap="RdYlGn",
        vmin=0,
        vmax=1,
        marker="s",
        s=70,
        linewidths=0
    )

    poligono.boundary.plot(
        ax=ax,
        color="black",
        linewidth=1.2
    )

    ax.set_title(
        f"{fecha} | validos: {len(muestra)}"
    )
    ax.set_aspect("equal")
    ax.grid(alpha=0.15)

fig.colorbar(
    grafico,
    ax=ejes.ravel().tolist(),
    label="NDVI",
    shrink=0.75
)

fig.suptitle(
    "Evolucion espacial del NDVI - L03",
    fontsize=15
)

SALIDA = (
    BASE / "reports/figures"
    / "evolucion_espacial_ndvi_L03.png"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)

plt.savefig(
    SALIDA,
    dpi=200,
    bbox_inches="tight"
)

plt.show()

print("\nFigura generada:", SALIDA)
print("Diagnostico finalizado.")
