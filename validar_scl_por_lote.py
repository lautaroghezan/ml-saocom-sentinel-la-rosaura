
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.mask import mask

ruta_lotes = Path("data/raw/vectores/potreros_la_rosaura.geojson")
ruta_scl = Path("data/interim/sentinel2/SCL_2024-09-04_prueba.tif")

lotes = gpd.read_file(ruta_lotes)
resultados = []

with rasterio.open(ruta_scl) as src:
    lotes = lotes.to_crs(src.crs)

    print("Columnas de lotes:", lotes.columns.tolist())

    for i, lote in lotes.iterrows():
        recorte, _ = mask(
            src,
            [lote.geometry],
            crop=True,
            filled=False,
            all_touched=False
        )

        valores = recorte[0].compressed()
        total = len(valores)

        if total == 0:
            continue

        vegetacion = np.sum(valores == 4)
        suelo = np.sum(valores == 5)

        # Clases SCL consideradas no utilizables
        invalidos = np.isin(valores, [0, 1, 3, 8, 9, 10, 11]).sum()

        # Clase 2: sombras topográficas, separada de nubes
        sombra_topografica = np.sum(valores == 2)

        validos = np.isin(valores, [4, 5, 6, 7]).sum()

        resultados.append({
            "lote": f"L{i+1:02d}",
            "fecha": "2024-09-04",
            "n_pixeles": total,
            "pct_vegetacion": 100 * vegetacion / total,
            "pct_suelo": 100 * suelo / total,
            "pct_invalidos": 100 * invalidos / total,
            "pct_sombra_topografica": 100 * sombra_topografica / total,
            "pct_validos": 100 * validos / total
        })

df = pd.DataFrame(resultados)

salida = Path("data/processed/control_scl_sentinel2_2024-09-04.csv")
salida.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(salida, index=False)

print(df.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
print("\nArchivo guardado:", salida)
