from pathlib import Path
import zipfile
import io
import tempfile
import shutil

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from rasterio.features import geometry_mask
from rasterio.windows import from_bounds, Window
from rasterio.windows import transform as window_transform
from rasterio.transform import xy

BASE = Path.cwd()

CARPETA_SAOCOM = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

PRODUCTO = CARPETA_SAOCOM / "EOL1DSARSAO1A14056208.zip"

GEOJSON = BASE / "data/raw/vectores/potreros_la_rosaura.geojson"

SALIDA = BASE / "data/processed/piloto_saocom_L02_HH_20241009.csv"

gdf = gpd.read_file(GEOJSON)

if gdf.crs is None:
    raise ValueError("El GeoJSON no tiene CRS.")

lote = gdf.loc[gdf["lote_id"] == "L02"]

if len(lote) != 1:
    raise ValueError("Debe existir exactamente un lote L02.")

with zipfile.ZipFile(PRODUCTO) as z1:

    internos = [
        n for n in z1.namelist()
        if n.lower().endswith(".zip")
    ]

    if len(internos) != 1:
        raise ValueError("No se encontro un unico ZIP interno.")

    with zipfile.ZipFile(io.BytesIO(z1.read(internos[0]))) as z2:

        rasters = [
            n for n in z2.namelist()
            if n.startswith("Data/")
            and n.lower().endswith("-hh-m")
        ]

        if len(rasters) != 1:
            raise ValueError("No se encontro un unico raster HH.")

        with tempfile.TemporaryDirectory() as temporal:

            destino = Path(temporal) / "saocom_hh.tif"

            with z2.open(rasters[0]) as origen:
                with destino.open("wb") as salida_temporal:
                    shutil.copyfileobj(origen, salida_temporal)

            with rasterio.open(destino) as src:

                lote_utm = lote.to_crs(src.crs)
                geometria = lote_utm.geometry.iloc[0]

                ventana = from_bounds(
                    *geometria.bounds,
                    transform=src.transform
                )

                ventana = ventana.round_offsets().round_lengths()

                ventana = ventana.intersection(
                    Window(0, 0, src.width, src.height)
                )

                datos = src.read(
                    1,
                    window=ventana,
                    masked=True
                )

                transformacion = window_transform(
                    ventana,
                    src.transform
                )

                mascara_lote = geometry_mask(
                    [geometria],
                    out_shape=datos.shape,
                    transform=transformacion,
                    invert=True,
                    all_touched=False
                )

                amplitud = np.asarray(datos.data, dtype=float)

                validos = (
                    mascara_lote
                    & ~np.ma.getmaskarray(datos)
                    & np.isfinite(amplitud)
                    & (amplitud > 0)
                )

                filas, columnas = np.where(validos)

                xs, ys = xy(
                    transformacion,
                    filas,
                    columnas,
                    offset="center"
                )

                valores = amplitud[filas, columnas]

                resultado = pd.DataFrame({
                    "producto": PRODUCTO.stem,
                    "fecha": "2024-10-09",
                    "lote_id": "L02",
                    "polarizacion": "HH",
                    "fila": filas + int(ventana.row_off),
                    "columna": columnas + int(ventana.col_off),
                    "x_utm": xs,
                    "y_utm": ys,
                    "amplitud": valores,
                    "sigma0_db": 20 * np.log10(valores)
                })

                print("\n=== PILOTO SAOCOM INTRALOTE ===")
                print("Lote: L02")
                print("Fecha: 2024-10-09")
                print("Polarizacion: HH")
                print("CRS:", src.crs)
                print("Pixeles geometricos dentro del lote:", mascara_lote.sum())
                print("Pixeles validos:", len(resultado))

                if len(resultado) == 0:
                    raise ValueError("No se encontraron pixeles validos.")

                print("\n=== ESTADISTICAS ===")
                print(resultado["sigma0_db"].describe().round(3))

                print("\n=== PRIMERAS OBSERVACIONES ===")
                print(resultado.head(10).round(3).to_string(index=False))

                SALIDA.parent.mkdir(parents=True, exist_ok=True)
                resultado.to_csv(
                    SALIDA,
                    index=False,
                    encoding="utf-8-sig"
                )

                print("\nArchivo generado:", SALIDA)
