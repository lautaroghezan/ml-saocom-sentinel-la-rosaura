from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

geojson = Path(
    "data/raw/vectores/potreros_la_rosaura.geojson"
)

csv = Path(
    "data/metadata/alineacion_espacial_saocom.csv"
)

gdf = gpd.read_file(geojson).to_crs("EPSG:32721")
lote = gdf.loc[gdf["lote_id"] == "L02"]

if len(lote) != 1:
    raise ValueError("No se encontro exactamente un lote L02.")

df = pd.read_csv(csv)

producto = df.loc[
    df["producto"] == "EOL1DSARSAO1A14056208"
]

if len(producto) != 1:
    raise ValueError("No se encontro el producto SAOCOM esperado.")

r = producto.iloc[0]

huella = box(
    min(r["origen_x"], r["limite_x"]),
    min(r["origen_y"], r["limite_y"]),
    max(r["origen_x"], r["limite_x"]),
    max(r["origen_y"], r["limite_y"])
)

geometria = lote.geometry.iloc[0]

area_lote = geometria.area
area_cubierta = geometria.intersection(huella).area

porcentaje = 100 * area_cubierta / area_lote

print("=== PILOTO SAOCOM INTRALOTE ===")
print("Lote:", lote["lote_id"].iloc[0])
print("Producto:", r["producto"])
print("Fecha:", r["fecha"])
print("CRS:", gdf.crs)
print("Superficie (ha):", round(area_lote / 10000, 2))
print("Cobertura espacial (%):", round(porcentaje, 2))
print("Cobertura completa:", huella.covers(geometria))
print("Limites del lote:", tuple(round(v, 2) for v in geometria.bounds))
print("Limites del raster:", tuple(round(v, 2) for v in huella.bounds))
