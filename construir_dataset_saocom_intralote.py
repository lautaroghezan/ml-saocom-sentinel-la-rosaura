from pathlib import Path
from contextlib import ExitStack
import zipfile
import tempfile
import io
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds, transform as window_transform
from rasterio.windows import Window

BASE = Path.cwd()
ORIGEN = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

SALIDA = BASE / "data/processed/dataset_saocom_intralote.csv"
SALIDA.parent.mkdir(parents=True, exist_ok=True)

FECHAS = {
    "EOL1DSARSAO1A14948973": "2024-08-06",
    "EOL1DSARSAO1A14948810": "2024-09-07",
    "EOL1DSARSAO1A14948841": "2024-09-23",
    "EOL1DSARSAO1A14056208": "2024-10-09",
    "EOL1DSARSAO1A14948886": "2024-10-25",
    "EOL1DSARSAO1A14948797": "2024-11-10",
    "EOL1DSARSAO1A15392623": "2024-12-12",
    "EOL1DSARSAO1A14948812": "2024-12-28",
    "EOL1DSARSAO1A14065611": "2025-01-13",
    "EOL1DSARSAO1A14065934": "2025-01-29",
    "EOL1DSARSAO1A14065630": "2025-02-14",
    "EOL1DSARSAO1A14065953": "2025-03-02",
    "EOL1DSARSAO1A14065706": "2025-03-18",
}

POLS = ["HH", "HV", "VH", "VV"]

inventario = pd.read_csv(
    BASE / "data/metadata/inventario_saocom.csv"
)

lotes = gpd.read_file(
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

assert len(lotes) == 16
assert lotes["lote_id"].is_unique
assert len(inventario) == 13
assert set(inventario["producto_id"]) == set(FECHAS)

columnas = [
    "producto", "fecha", "lote_id", "fila", "columna",
    "x_utm", "y_utm", "HH_db", "HV_db", "VH_db", "VV_db"
]

registros = []

for numero, (_, item) in enumerate(
    inventario.sort_values("producto_id").iterrows(), 1
):
    producto = item["producto_id"]
    fecha = FECHAS[producto]
    ruta_zip = ORIGEN / item["archivo"]

    print(
        f"\n[{numero}/13] {fecha} - {producto}",
        flush=True
    )

    with zipfile.ZipFile(ruta_zip) as exterior:

        internos = [
            n for n in exterior.namelist()
            if n.lower().endswith(".zip")
        ]

        if len(internos) != 1:
            raise ValueError(
                f"{producto}: ZIP interno inesperado"
            )

        with zipfile.ZipFile(
            io.BytesIO(exterior.read(internos[0]))
        ) as interior:

            with tempfile.TemporaryDirectory() as temporal:

                rutas = {}

                for pol in POLS:
                    candidatos = [
                        n for n in interior.namelist()
                        if n.lower().startswith("data/")
                        and n.lower().endswith(
                            f"-{pol.lower()}-m"
                        )
                    ]

                    if len(candidatos) != 1:
                        raise ValueError(
                            f"{producto}: no se encontro "
                            f"un unico raster {pol}"
                        )

                    destino = Path(temporal) / f"{pol}.tif"

                    with interior.open(candidatos[0]) as fuente:
                        with open(destino, "wb") as salida:
                            while True:
                                bloque = fuente.read(1024 * 1024)
                                if not bloque:
                                    break
                                salida.write(bloque)

                    rutas[pol] = destino

                with ExitStack() as stack:
                    rasters = {
                        pol: stack.enter_context(
                            rasterio.open(rutas[pol])
                        )
                        for pol in POLS
                    }

                    referencia = rasters["HH"]

                    if referencia.crs.to_epsg() != 32721:
                        raise ValueError(
                            f"{producto}: CRS inesperado"
                        )

                    for pol, raster in rasters.items():
                        if (
                            raster.crs != referencia.crs
                            or raster.transform != referencia.transform
                            or raster.width != referencia.width
                            or raster.height != referencia.height
                        ):
                            raise ValueError(
                                f"{producto}: grillas no coinciden "
                                f"en {pol}"
                            )

                    total_producto = 0

                    for _, lote in lotes.iterrows():

                        geometria = lote.geometry

                        win = from_bounds(
                            *geometria.bounds,
                            transform=referencia.transform
                        )

                        col0 = max(0, int(np.floor(win.col_off)))
                        fila0 = max(0, int(np.floor(win.row_off)))
                        col1 = min(
                            referencia.width,
                            int(np.ceil(win.col_off + win.width))
                        )
                        fila1 = min(
                            referencia.height,
                            int(np.ceil(win.row_off + win.height))
                        )

                        if col1 <= col0 or fila1 <= fila0:
                            continue

                        ventana = Window(
                            col0, fila0,
                            col1 - col0,
                            fila1 - fila0
                        )

                        transformacion = window_transform(
                            ventana,
                            referencia.transform
                        )

                        mascara = geometry_mask(
                            [geometria],
                            out_shape=(
                                int(ventana.height),
                                int(ventana.width)
                            ),
                            transform=transformacion,
                            invert=True,
                            all_touched=False
                        )

                        filas, columnas = np.where(mascara)

                        if len(filas) == 0:
                            continue

                        datos = {}

                        for pol, raster in rasters.items():
                            matriz = raster.read(
                                1,
                                window=ventana,
                                masked=True
                            )

                            valores = np.ma.filled(
                                matriz.astype("float64"),
                                np.nan
                            )[filas, columnas]

                            validos = (
                                np.isfinite(valores)
                                & (valores > 0)
                            )

                            db = np.full(
                                len(valores),
                                np.nan,
                                dtype="float64"
                            )

                            db[validos] = (
                                20 * np.log10(valores[validos])
                            )

                            datos[f"{pol}_db"] = db

                        filas_globales = filas + fila0
                        columnas_globales = columnas + col0

                        xs, ys = rasterio.transform.xy(
                            referencia.transform,
                            filas_globales,
                            columnas_globales,
                            offset="center"
                        )

                        tabla = pd.DataFrame({
                            "producto": producto,
                            "fecha": fecha,
                            "lote_id": lote["lote_id"],
                            "fila": filas_globales,
                            "columna": columnas_globales,
                            "x_utm": xs,
                            "y_utm": ys,
                            **datos
                        })

                        registros.append(tabla)
                        total_producto += len(tabla)

                    print(
                        f"Pixeles extraidos: {total_producto}",
                        flush=True
                    )

if not registros:
    raise RuntimeError("No se extrajeron observaciones.")

resultado = pd.concat(registros, ignore_index=True)

if resultado.duplicated(
    ["producto", "lote_id", "fila", "columna"]
).any():
    raise ValueError("Se detectaron registros duplicados.")

resultado = resultado[[
    "producto", "fecha", "lote_id", "fila", "columna",
    "x_utm", "y_utm", "HH_db", "HV_db", "VH_db", "VV_db"
]].sort_values(
    ["fecha", "lote_id", "fila", "columna"]
)

resultado.to_csv(SALIDA, index=False)

print("\n=== DATASET SAOCOM INTRALOTE ===")
print("Registros:", len(resultado))
print("Fechas:", resultado["fecha"].nunique())
print("Lotes:", resultado["lote_id"].nunique())
print("Productos:", resultado["producto"].nunique())
print("\nValores faltantes:")
print(resultado[POLS[0] + "_db"].isna().sum(), "HH")
print(resultado["HV_db"].isna().sum(), "HV")
print(resultado["VH_db"].isna().sum(), "VH")
print(resultado["VV_db"].isna().sum(), "VV")
print("\nArchivo:", SALIDA)
