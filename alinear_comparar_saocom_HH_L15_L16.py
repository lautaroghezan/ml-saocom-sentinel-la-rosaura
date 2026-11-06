from pathlib import Path
import zipfile
import tempfile
import shutil
import math

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds, transform as window_transform
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.features import geometry_mask

BASE = Path.cwd()

CARPETA_SAOCOM = (
    Path.home() / "OneDrive/Documentos/La_Rosaura_SAOCOM_2024_25"
)

PRODUCTOS = {
    "2025-01-29": "EOL1DSARSAO1A14065934",
    "2025-02-14": "EOL1DSARSAO1A14065630"
}

LOTES = ["L15", "L16"]
RES = 44.0

lotes = gpd.read_file(
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

lotes = lotes.loc[lotes["lote_id"].isin(LOTES)].copy()

if len(lotes) != 2:
    raise ValueError("No se encontraron L15 y L16")

xmin, ymin, xmax, ymax = lotes.total_bounds

izquierda = math.floor(xmin / RES) * RES
derecha = math.ceil(xmax / RES) * RES
abajo = math.floor(ymin / RES) * RES
arriba = math.ceil(ymax / RES) * RES

ancho = int(round((derecha - izquierda) / RES))
alto = int(round((arriba - abajo) / RES))

dest_transform = from_origin(
    izquierda, arriba, RES, RES
)

def leer_y_alinear(producto):

    archivos = list(
        CARPETA_SAOCOM.glob(f"*{producto}*.zip")
    )

    if len(archivos) != 1:
        raise FileNotFoundError(producto)

    with zipfile.ZipFile(archivos[0]) as externo:

        internos = [
            n for n in externo.namelist()
            if n.lower().endswith(".zip")
        ]

        if len(internos) != 1:
            raise ValueError("ZIP interno no identificado")

        with tempfile.TemporaryDirectory() as tmp:

            interno_path = Path(tmp) / "interno.zip"
            interno_path.write_bytes(
                externo.read(internos[0])
            )

            with zipfile.ZipFile(interno_path) as interno:

                candidatos = [
                    n for n in interno.namelist()
                    if n.lower().startswith("data/")
                    and n.lower().endswith("-hh-m")
                ]

                if len(candidatos) != 1:
                    raise ValueError("Raster HH no identificado")

                raster_path = Path(tmp) / "hh.tif"

                with interno.open(candidatos[0]) as origen:
                    with raster_path.open("wb") as destino:
                        shutil.copyfileobj(origen, destino)

            with rasterio.open(raster_path) as src:

                # Ventana con margen para el remuestreo.
                ventana = from_bounds(
                    izquierda - RES,
                    abajo - RES,
                    derecha + RES,
                    arriba + RES,
                    transform=src.transform
                )

                ventana = ventana.round_offsets().round_lengths()

                amplitud = src.read(
                    1,
                    window=ventana,
                    boundless=True,
                    fill_value=0
                )

                src_transform = window_transform(
                    ventana, src.transform
                )

                # Reproyectar amplitud, no valores en dB.
                destino = np.full(
                    (alto, ancho),
                    np.nan,
                    dtype=np.float32
                )

                amplitud = amplitud.astype(np.float32)

                amplitud[
                    ~np.isfinite(amplitud)
                    | (amplitud <= 0)
                ] = np.nan

                reproject(
                    source=amplitud,
                    destination=destino,
                    src_transform=src_transform,
                    src_crs=src.crs,
                    dst_transform=dest_transform,
                    dst_crs="EPSG:32721",
                    src_nodata=np.nan,
                    dst_nodata=np.nan,
                    resampling=Resampling.nearest
                )

                db = np.full(
                    destino.shape,
                    np.nan,
                    dtype=np.float32
                )

                validos = np.isfinite(destino) & (destino > 0)

                db[validos] = (
                    20 * np.log10(destino[validos])
                )

                return db

print("\nAlineando SAOCOM 2025-01-29...")
enero = leer_y_alinear(PRODUCTOS["2025-01-29"])

print("Alineando SAOCOM 2025-02-14...")
febrero = leer_y_alinear(PRODUCTOS["2025-02-14"])

delta = febrero - enero

resultados = []
mapa = np.full(delta.shape, np.nan, dtype=np.float32)

for _, lote in lotes.iterrows():

    mascara = geometry_mask(
        [lote.geometry],
        out_shape=(alto, ancho),
        transform=dest_transform,
        invert=True,
        all_touched=False
    )

    validos = mascara & np.isfinite(delta)

    valores = delta[validos]

    if len(valores) == 0:
        raise ValueError(
            f"Sin celdas comparables en {lote['lote_id']}"
        )

    mapa[validos] = delta[validos]

    resultados.append({
        "lote_id": lote["lote_id"],
        "celdas_geometricas": int(mascara.sum()),
        "celdas_comparables": len(valores),
        "pct_comparables": round(
            100 * len(valores) / mascara.sum(), 2
        ),
        "delta_HH_mediana_db": round(
            float(np.median(valores)), 3
        ),
        "delta_HH_media_db": round(
            float(np.mean(valores)), 3
        ),
        "pct_celdas_descenso": round(
            100 * np.mean(valores < 0), 2
        ),
        "pct_celdas_caida_3db": round(
            100 * np.mean(valores <= -3), 2
        )
    })

resultado = pd.DataFrame(resultados)

TABLA = (
    BASE / "reports/tables"
    / "cambio_espacial_HH_saocom_L15_L16.csv"
)

FIGURA = (
    BASE / "reports/figures"
    / "cambio_espacial_HH_saocom_L15_L16.png"
)

TABLA.parent.mkdir(parents=True, exist_ok=True)
FIGURA.parent.mkdir(parents=True, exist_ok=True)

resultado.to_csv(TABLA, index=False)

import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

fig, ax = plt.subplots(figsize=(9, 8))

imagen = ax.imshow(
    mapa,
    extent=[izquierda, derecha, abajo, arriba],
    origin="upper",
    cmap="RdBu",
    norm=TwoSlopeNorm(vmin=-10, vcenter=0, vmax=10),
    interpolation="nearest"
)

lotes.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.5
)

for _, lote in lotes.iterrows():
    centro = lote.geometry.representative_point()
    ax.text(
        centro.x,
        centro.y,
        lote["lote_id"],
        ha="center",
        va="center",
        fontweight="bold",
        bbox=dict(facecolor="white", alpha=0.8)
    )

plt.colorbar(
    imagen,
    ax=ax,
    label="Cambio HH (dB): febrero - enero"
)

ax.set_title(
    "Cambio espacial SAOCOM HH - L15 y L16\n"
    "29/01/2025 a 14/02/2025"
)

ax.set_xlabel("Este UTM (m)")
ax.set_ylabel("Norte UTM (m)")
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig(FIGURA, dpi=200)
plt.show()

print("\n=== CAMBIO ESPACIAL SAOCOM HH ===")
print(resultado.to_string(index=False))

print("\nTabla:", TABLA)
print("Figura:", FIGURA)
print("Diagnostico finalizado.")
