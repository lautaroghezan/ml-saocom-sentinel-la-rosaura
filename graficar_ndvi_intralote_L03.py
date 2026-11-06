from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_sentinel2_intralote.csv"
)

lotes = gpd.read_file(
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

LOTE = "L03"
FECHA = "2024-12-03"

muestra = datos.loc[
    (datos["lote_id"] == LOTE)
    & (datos["fecha"] == FECHA)
].copy()

poligono = lotes.loc[
    lotes["lote_id"] == LOTE
]

if muestra.empty or poligono.empty:
    raise ValueError("No se encontraron datos para el lote y fecha")

validos = muestra.loc[
    muestra["NDVI"].notna()
].copy()

fig, ax = plt.subplots(figsize=(9, 8))

grafico = ax.scatter(
    validos["x_utm"],
    validos["y_utm"],
    c=validos["NDVI"],
    cmap="RdYlGn",
    vmin=0,
    vmax=1,
    marker="s",
    s=115,
    linewidths=0
)

poligono.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.5
)

ax.set_aspect("equal")
ax.set_xlabel("Coordenada Este UTM (m)")
ax.set_ylabel("Coordenada Norte UTM (m)")
ax.set_title(
    f"NDVI intralote - {LOTE} - {FECHA}"
)

barra = plt.colorbar(grafico, ax=ax, shrink=0.8)
barra.set_label("NDVI")

ax.grid(alpha=0.15)

SALIDA = (
    BASE / "reports/figures"
    / "mapa_ndvi_L03_20241203.png"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)

plt.tight_layout()
plt.savefig(SALIDA, dpi=200)
plt.show()

print("\n=== MAPA NDVI ===")
print("Lote:", LOTE)
print("Fecha:", FECHA)
print("Pixeles:", len(muestra))
print("Validos:", len(validos))
print("NDVI minimo:", round(validos["NDVI"].min(), 4))
print("NDVI maximo:", round(validos["NDVI"].max(), 4))
print("NDVI mediana:", round(validos["NDVI"].median(), 4))
print("NDVI IQR:", round(
    validos["NDVI"].quantile(0.75)
    - validos["NDVI"].quantile(0.25),
    4
))
print("Figura:", SALIDA)
