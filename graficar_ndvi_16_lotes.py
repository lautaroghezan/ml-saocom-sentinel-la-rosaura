from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

BASE = Path.cwd()
FECHA = "2024-12-03"

datos = pd.read_csv(
    BASE / "data/processed/dataset_sentinel2_intralote.csv"
)

lotes = gpd.read_file(
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

muestra = datos.loc[
    datos["fecha"] == FECHA
].copy()

validos = muestra.loc[
    muestra["NDVI"].notna()
].copy()

if muestra.empty:
    raise ValueError("No hay datos para la fecha seleccionada")

fig, ax = plt.subplots(figsize=(13, 11))

# Pixeles Sentinel-2 en su grilla espacial
ax.scatter(
    validos["x_utm"],
    validos["y_utm"],
    c=validos["NDVI"],
    cmap="RdYlGn",
    norm=Normalize(vmin=0, vmax=1),
    marker="s",
    s=65,
    linewidths=0,
    zorder=2
)

# Limites de los 16 lotes
lotes.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.2,
    zorder=3
)

# Identificacion de cada lote
for _, lote in lotes.iterrows():
    centro = lote.geometry.representative_point()

    ax.text(
        centro.x,
        centro.y,
        lote["lote_id"],
        fontsize=8,
        fontweight="bold",
        ha="center",
        va="center",
        color="black",
        bbox=dict(
            facecolor="white",
            alpha=0.75,
            edgecolor="none",
            pad=1
        ),
        zorder=4
    )

barra = ScalarMappable(
    norm=Normalize(vmin=0, vmax=1),
    cmap="RdYlGn"
)
barra.set_array([])

fig.colorbar(
    barra,
    ax=ax,
    label="NDVI",
    shrink=0.75
)

ax.set_title(
    f"La Rosaura - NDVI intralote - {FECHA}",
    fontsize=15
)

ax.set_xlabel("Este UTM (m)")
ax.set_ylabel("Norte UTM (m)")
ax.set_aspect("equal")
ax.grid(alpha=0.12)

SALIDA = (
    BASE / "reports/figures"
    / "mapa_ndvi_16_lotes_20241203.png"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)

plt.savefig(
    SALIDA,
    dpi=250,
    bbox_inches="tight"
)

plt.show()

print("\n=== MAPA GENERAL NDVI ===")
print("Fecha:", FECHA)
print("Lotes representados:", muestra["lote_id"].nunique())
print("Pixeles totales:", len(muestra))
print("Pixeles validos:", len(validos))
print("Cobertura:", round(100 * len(validos) / len(muestra), 2), "%")
print("Figura guardada:", SALIDA)
print("\nDiagnostico finalizado.")
