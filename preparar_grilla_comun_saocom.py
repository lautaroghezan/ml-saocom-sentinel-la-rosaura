from pathlib import Path
import math
import geopandas as gpd
import pandas as pd
from rasterio.transform import from_origin
from rasterio.features import geometry_mask

BASE = Path.cwd()

ENTRADA = (
    BASE / "data/raw/vectores/potreros_la_rosaura.geojson"
)

SALIDA = (
    BASE / "data/metadata/grilla_comun_saocom_L15_L16.csv"
)

RESOLUCION = 44.0
LOTES = ["L15", "L16"]

gdf = gpd.read_file(ENTRADA).to_crs("EPSG:32721")
gdf = gdf.loc[gdf["lote_id"].isin(LOTES)].copy()

if len(gdf) != 2:
    raise ValueError("No se encontraron exactamente L15 y L16")

xmin, ymin, xmax, ymax = gdf.total_bounds

# Limites alineados a multiplos de 44 metros.
izquierda = math.floor(xmin / RESOLUCION) * RESOLUCION
derecha = math.ceil(xmax / RESOLUCION) * RESOLUCION
abajo = math.floor(ymin / RESOLUCION) * RESOLUCION
arriba = math.ceil(ymax / RESOLUCION) * RESOLUCION

ancho = int(round((derecha - izquierda) / RESOLUCION))
alto = int(round((arriba - abajo) / RESOLUCION))

transform = from_origin(
    izquierda,
    arriba,
    RESOLUCION,
    RESOLUCION
)

resultados = []

for _, lote in gdf.iterrows():

    mascara = geometry_mask(
        [lote.geometry],
        out_shape=(alto, ancho),
        transform=transform,
        invert=True,
        all_touched=False
    )

    resultados.append({
        "lote_id": lote["lote_id"],
        "resolucion_m": RESOLUCION,
        "columnas_grilla": ancho,
        "filas_grilla": alto,
        "celdas_dentro_lote": int(mascara.sum()),
        "origen_x": izquierda,
        "origen_y": arriba,
        "crs": "EPSG:32721"
    })

resultado = pd.DataFrame(resultados)

SALIDA.parent.mkdir(parents=True, exist_ok=True)
resultado.to_csv(SALIDA, index=False)

print("\n=== GRILLA COMUN SAOCOM ===")
print(resultado.to_string(index=False))

print("\n=== EXTENSION ===")
print("X minimo:", izquierda)
print("X maximo:", derecha)
print("Y minimo:", abajo)
print("Y maximo:", arriba)

print("\n=== DIMENSIONES ===")
print("Columnas:", ancho)
print("Filas:", alto)
print("Celdas totales:", ancho * alto)

print("\nArchivo:", SALIDA)
print("Diagnostico finalizado.")
