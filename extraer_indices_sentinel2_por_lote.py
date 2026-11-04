
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask

FECHA = "2024-09-04"

RASTER = Path(
    f"data/interim/sentinel2/"
    f"reflectancias_indices_{FECHA}_20m.tif"
)

GEOJSON = Path(
    "data/raw/vectores/potreros_la_rosaura.geojson"
)

SALIDA = Path(
    "data/processed/"
    "indices_sentinel2_piloto_por_lote.csv"
)

indices = {
    "NDVI": 7,
    "NDRE": 8,
    "NDMI": 9,
}

lotes = gpd.read_file(GEOJSON)

filas = []

with rasterio.open(RASTER) as src:
    lotes = lotes.to_crs(src.crs)

    for _, lote in lotes.iterrows():
        recorte, _ = mask(
            src,
            [lote.geometry],
            crop=True,
            filled=False,
            all_touched=False,
        )

        fila = {
            "fecha": FECHA,
            "lote_id": lote["lote_id"],
        }

        for nombre, banda in indices.items():
            datos = recorte[banda - 1]
            valores = datos.compressed()
            valores = valores[
                np.isfinite(valores)
                & (valores != -9999)
                & (valores >= -1)
                & (valores <= 1)
            ]

            fila[f"{nombre}_n_validos"] = len(valores)

            if len(valores):
                fila[f"{nombre}_mediana"] = np.median(valores)
                fila[f"{nombre}_p25"] = np.percentile(valores, 25)
                fila[f"{nombre}_p75"] = np.percentile(valores, 75)
                fila[f"{nombre}_iqr"] = (
                    fila[f"{nombre}_p75"]
                    - fila[f"{nombre}_p25"]
                )
            else:
                for estadistico in [
                    "mediana", "p25", "p75", "iqr"
                ]:
                    fila[f"{nombre}_{estadistico}"] = np.nan

        filas.append(fila)

df = pd.DataFrame(filas).sort_values("lote_id")

SALIDA.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(SALIDA, index=False)

print("Registros:", len(df))
print("Lotes:", df["lote_id"].nunique())

print(
    df[
        [
            "lote_id",
            "NDVI_mediana",
            "NDRE_mediana",
            "NDMI_mediana",
            "NDVI_n_validos",
        ]
    ].round(4).to_string(index=False)
)

print("Archivo:", SALIDA)
