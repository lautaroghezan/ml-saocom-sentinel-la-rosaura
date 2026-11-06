from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

base = Path.cwd()

csv = base / "data/processed/piloto_saocom_L02_HH_20241009.csv"
geojson = base / "data/raw/vectores/potreros_la_rosaura.geojson"
salida = base / "reports/figures/piloto_saocom_L02_HH_20241009.png"

df = pd.read_csv(csv)

gdf = gpd.read_file(geojson).to_crs("EPSG:32721")
lote = gdf[gdf["lote_id"] == "L02"]

if len(lote) != 1:
    raise ValueError("No se encontro exactamente un lote L02.")

if df.empty:
    raise ValueError("El CSV no contiene observaciones.")

fig, ax = plt.subplots(figsize=(8, 7))

# Cada marcador representa el centro de un pixel SAOCOM real.
grafico = ax.scatter(
    df["x_utm"],
    df["y_utm"],
    c=df["sigma0_db"],
    cmap="viridis",
    marker="s",
    s=95,
    linewidths=0
)

lote.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.5
)

barra = fig.colorbar(grafico, ax=ax, shrink=0.8)
barra.set_label("Retrodispersion HH (dB, conversion provisional)")

ax.set_aspect("equal")
ax.set_xlabel("Coordenada Este UTM (m)")
ax.set_ylabel("Coordenada Norte UTM (m)")

ax.set_title(
    "La Rosaura - L02\n"
    "SAOCOM HH | 09/10/2024"
)

ax.grid(alpha=0.15)

salida.parent.mkdir(parents=True, exist_ok=True)

plt.tight_layout()
plt.savefig(salida, dpi=220, bbox_inches="tight")
plt.close(fig)

print("=== MAPA PILOTO GENERADO ===")
print("Lote: L02")
print("Fecha: 2024-10-09")
print("Polarizacion: HH")
print("Observaciones representadas:", len(df))
print("Archivo:", salida)
