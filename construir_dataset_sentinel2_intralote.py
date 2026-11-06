from pathlib import Path
import re
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask

BASE = Path.cwd()
CARPETA = BASE / "data/interim/sentinel2/reflectancias"
SALIDA = BASE / "data/processed/dataset_sentinel2_intralote.csv"

BANDAS = [
    "B04", "B05", "B08", "B8A", "B11",
    "SCL", "NDVI", "NDRE", "NDMI", "dataMask"
]

lotes = gpd.read_file(
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

archivos = sorted(CARPETA.glob("*.tif"))

if len(archivos) != 69:
    raise ValueError("Se esperaban 69 imagenes Sentinel-2")

registros = []
referencia = None

for numero, archivo in enumerate(archivos, 1):

    coincidencia = re.fullmatch(
        r"S2_(\d{4}-\d{2}-\d{2})_20m\.tif",
        archivo.name
    )

    if not coincidencia:
        raise ValueError(f"Nombre inesperado: {archivo.name}")

    fecha = coincidencia.group(1)

    with rasterio.open(archivo) as src:

        if src.count != 10 or str(src.crs) != "EPSG:32721":
            raise ValueError(f"Estructura inesperada: {archivo.name}")

        grilla = (
            src.width,
            src.height,
            tuple(src.transform)
        )

        if referencia is None:
            referencia = grilla
        elif grilla != referencia:
            raise ValueError(f"Grilla diferente: {archivo.name}")

        datos = src.read()

        for _, lote in lotes.iterrows():

            mascara = geometry_mask(
                [lote.geometry],
                out_shape=(src.height, src.width),
                transform=src.transform,
                invert=True,
                all_touched=False
            )

            filas, columnas = np.where(mascara)

            if len(filas) == 0:
                raise ValueError(
                    f"Sin pixeles: {lote['lote_id']} {fecha}"
                )

            xs, ys = rasterio.transform.xy(
                src.transform,
                filas,
                columnas,
                offset="center"
            )

            valores = datos[:, filas, columnas]

            scl = valores[5]
            data_mask = valores[9]

            validos = (
                (data_mask == 1)
                & np.isin(scl, [4, 5, 6])
                & np.all(np.isfinite(valores[:5]), axis=0)
                & np.all(valores[:5] != -9999, axis=0)
            )

            tabla = pd.DataFrame({
                "fecha": fecha,
                "lote_id": lote["lote_id"],
                "fila": filas,
                "columna": columnas,
                "x_utm": xs,
                "y_utm": ys,
                "valido_scl": validos
            })

            for indice, nombre in enumerate(BANDAS):
                v = valores[indice].astype(float)

                if nombre in (
                    "B04", "B05", "B08", "B8A",
                    "B11", "NDVI", "NDRE", "NDMI"
                ):
                    v[~validos] = np.nan
                    v[~np.isfinite(v)] = np.nan
                    v[v == -9999] = np.nan

                if nombre in ("NDVI", "NDRE", "NDMI"):
                    v[(v < -1) | (v > 1)] = np.nan

                tabla[nombre] = v

            registros.append(tabla)

    print(
        f"[{numero:02d}/{len(archivos)}] "
        f"{fecha}: {sum(len(x) for x in registros[-16:])} registros"
    )

resultado = pd.concat(registros, ignore_index=True)

duplicados = resultado.duplicated(
    ["fecha", "lote_id", "fila", "columna"]
).sum()

if duplicados:
    raise ValueError(f"Registros duplicados: {duplicados}")

SALIDA.parent.mkdir(parents=True, exist_ok=True)
resultado.to_csv(SALIDA, index=False)

print("\n=== DATASET SENTINEL-2 INTRALOTE ===")
print("Registros:", len(resultado))
print("Fechas:", resultado["fecha"].nunique())
print("Lotes:", resultado["lote_id"].nunique())
print("Celdas espaciales unicas:",
      resultado[["fila", "columna"]].drop_duplicates().shape[0])
print("Observaciones validas SCL:",
      int(resultado["valido_scl"].sum()))
print("Porcentaje valido:",
      round(100 * resultado["valido_scl"].mean(), 2))
print("Duplicados:", duplicados)
print("Archivo:", SALIDA)
