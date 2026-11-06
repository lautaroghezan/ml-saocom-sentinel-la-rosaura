from pathlib import Path
import math
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

BASE = Path.cwd()

INICIO = "2024-12-01"
FIN = "2025-04-30"

datos = pd.read_csv(
    BASE / "data/processed/dataset_sentinel2_intralote.csv"
)

lotes = gpd.read_file(
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

periodo = datos.loc[
    (datos["fecha"] >= INICIO)
    & (datos["fecha"] <= FIN)
].copy()

# Disponibilidad por fecha
cobertura = (
    periodo.groupby("fecha")
    .agg(
        total=("NDVI", "size"),
        validos=("NDVI", "count")
    )
    .reset_index()
)

cobertura["pct_validos"] = (
    100 * cobertura["validos"] / cobertura["total"]
)

fechas = cobertura.loc[
    cobertura["pct_validos"] >= 80, "fecha"
].tolist()

if not fechas:
    raise ValueError("No hay fechas con cobertura >=80%")

print("\n=== FECHAS SELECCIONADAS ===")
print(cobertura.loc[
    cobertura["fecha"].isin(fechas),
    ["fecha", "pct_validos"]
].to_string(index=False))

# Resumen de NDVI por lote y fecha
resumen = (
    periodo.groupby(["fecha", "lote_id"])
    .agg(
        pixeles=("NDVI", "size"),
        validos=("NDVI", "count"),
        ndvi_mediana=("NDVI", "median")
    )
    .reset_index()
)

resumen["pct_validos"] = (
    100 * resumen["validos"] / resumen["pixeles"]
)

salida_tablas = BASE / "reports/tables"
salida_tablas.mkdir(parents=True, exist_ok=True)

resumen.to_csv(
    salida_tablas / "ndvi_temporal_lotes_dic2024_abr2025.csv",
    index=False
)

# Mapas comparables
columnas = 3
filas = math.ceil(len(fechas) / columnas)

fig, ejes = plt.subplots(
    filas,
    columnas,
    figsize=(17, 5.5 * filas),
    sharex=True,
    sharey=True
)

ejes = list(ejes.flat)

for ax, fecha in zip(ejes, fechas):

    muestra = periodo.loc[
        (periodo["fecha"] == fecha)
        & periodo["NDVI"].notna()
    ]

    ax.scatter(
        muestra["x_utm"],
        muestra["y_utm"],
        c=muestra["NDVI"],
        cmap="RdYlGn",
        norm=Normalize(vmin=0, vmax=1),
        marker="s",
        s=12,
        linewidths=0
    )

    lotes.boundary.plot(
        ax=ax,
        color="black",
        linewidth=0.6
    )

    ax.set_title(fecha, fontsize=11)
    ax.set_aspect("equal")
    ax.grid(alpha=0.1)

for ax in ejes[len(fechas):]:
    ax.axis("off")

barra = ScalarMappable(
    norm=Normalize(vmin=0, vmax=1),
    cmap="RdYlGn"
)
barra.set_array([])

fig.colorbar(
    barra,
    ax=ejes[:len(fechas)],
    shrink=0.6,
    label="NDVI"
)

fig.suptitle(
    "La Rosaura - Evolucion NDVI - Dic 2024 a Abr 2025",
    fontsize=16
)

salida_figuras = BASE / "reports/figures"
salida_figuras.mkdir(parents=True, exist_ok=True)

archivo = (
    salida_figuras /
    "secuencia_ndvi_16_lotes_dic2024_abr2025.png"
)

plt.savefig(
    archivo,
    dpi=200,
    bbox_inches="tight"
)

plt.show()

print("\n=== RESUMEN ===")
print("Fechas seleccionadas:", len(fechas))
print("Lotes:", periodo["lote_id"].nunique())
print("Figura:", archivo)
print("Tabla:", salida_tablas / "ndvi_temporal_lotes_dic2024_abr2025.csv")
print("\nDiagnostico finalizado.")
