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
CARPETA = Path.home() / "OneDrive/Documentos/La_Rosaura_SAOCOM_2024_25"

PRODUCTOS = {
    "2025-01-29": "EOL1DSARSAO1A14065934",
    "2025-02-14": "EOL1DSARSAO1A14065630"
}

POLARIZACIONES = ["HH", "HV", "VH", "VV"]
LOTES = ["L15", "L16"]
RES = 44.0

lotes = gpd.read_file(
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

lotes = lotes[lotes["lote_id"].isin(LOTES)].copy()

xmin, ymin, xmax, ymax = lotes.total_bounds
izq = math.floor(xmin / RES) * RES
der = math.ceil(xmax / RES) * RES
inf = math.floor(ymin / RES) * RES
sup = math.ceil(ymax / RES) * RES

ancho = int(round((der - izq) / RES))
alto = int(round((sup - inf) / RES))
transform_destino = from_origin(izq, sup, RES, RES)

def procesar_producto(producto):
    archivos = list(CARPETA.glob(f"*{producto}*.zip"))
    if len(archivos) != 1:
        raise FileNotFoundError(producto)

    salida = {}

    with zipfile.ZipFile(archivos[0]) as externo:
        internos = [
            n for n in externo.namelist()
            if n.lower().endswith(".zip")
        ]
        if len(internos) != 1:
            raise ValueError("ZIP interno inesperado")

        with tempfile.TemporaryDirectory() as tmp:
            ruta_interna = Path(tmp) / "interno.zip"
            ruta_interna.write_bytes(externo.read(internos[0]))

            with zipfile.ZipFile(ruta_interna) as interno:
                nombres = interno.namelist()

                for pol in POLARIZACIONES:
                    candidatos = [
                        n for n in nombres
                        if n.lower().startswith("data/")
                        and n.lower().endswith(f"-{pol.lower()}-m")
                    ]
                    if len(candidatos) != 1:
                        raise ValueError(f"Raster {pol} no identificado")

                    ruta_raster = Path(tmp) / f"{pol}.tif"

                    with interno.open(candidatos[0]) as origen:
                        with ruta_raster.open("wb") as destino:
                            shutil.copyfileobj(origen, destino)

                    with rasterio.open(ruta_raster) as src:
                        ventana = from_bounds(
                            izq - RES, inf - RES,
                            der + RES, sup + RES,
                            transform=src.transform
                        ).round_offsets().round_lengths()

                        amplitud = src.read(
                            1,
                            window=ventana,
                            boundless=True,
                            fill_value=0
                        ).astype(np.float32)

                        amplitud[
                            ~np.isfinite(amplitud) |
                            (amplitud <= 0)
                        ] = np.nan

                        destino = np.full(
                            (alto, ancho),
                            np.nan,
                            dtype=np.float32
                        )

                        reproject(
                            source=amplitud,
                            destination=destino,
                            src_transform=window_transform(
                                ventana, src.transform
                            ),
                            src_crs=src.crs,
                            dst_transform=transform_destino,
                            dst_crs="EPSG:32721",
                            src_nodata=np.nan,
                            dst_nodata=np.nan,
                            resampling=Resampling.nearest
                        )

                        db = np.full_like(destino, np.nan)
                        validos = np.isfinite(destino) & (destino > 0)
                        db[validos] = 20 * np.log10(destino[validos])
                        salida[pol] = db

                    ruta_raster.unlink()

    return salida

print("\nProcesando enero...")
enero = procesar_producto(PRODUCTOS["2025-01-29"])

print("Procesando febrero...")
febrero = procesar_producto(PRODUCTOS["2025-02-14"])

resultados = []

for _, lote in lotes.iterrows():
    mascara = geometry_mask(
        [lote.geometry],
        out_shape=(alto, ancho),
        transform=transform_destino,
        invert=True,
        all_touched=False
    )

    for pol in POLARIZACIONES:
        delta = febrero[pol] - enero[pol]
        valores = delta[mascara & np.isfinite(delta)]

        resultados.append({
            "lote_id": lote["lote_id"],
            "polarizacion": pol,
            "celdas_geometricas": int(mascara.sum()),
            "celdas_comparables": len(valores),
            "delta_mediana_db": (
                float(np.median(valores)) if len(valores) else np.nan
            ),
            "delta_media_db": (
                float(np.mean(valores)) if len(valores) else np.nan
            ),
            "pct_descenso": (
                float(100 * np.mean(valores < 0))
                if len(valores) else np.nan
            ),
            "pct_caida_3db": (
                float(100 * np.mean(valores <= -3))
                if len(valores) else np.nan
            )
        })

tabla = pd.DataFrame(resultados)

salida = (
    BASE / "reports/tables"
    / "cambios_saocom_multipolarizacion_L15_L16.csv"
)
salida.parent.mkdir(parents=True, exist_ok=True)
tabla.to_csv(salida, index=False)

print("\n=== CAMBIOS MULTIPOLARIZACION SAOCOM ===")
print(tabla.to_string(index=False, float_format="%.3f"))
print("\nArchivo:", salida)
print("Diagnostico finalizado.")
