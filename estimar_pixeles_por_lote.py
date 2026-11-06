from pathlib import Path
import geopandas as gpd
import pandas as pd

archivo = Path(
    "data/raw/vectores/potreros_la_rosaura.geojson"
)

gdf = gpd.read_file(archivo)

print("=== DATOS DEL GEOJSON ===")
print("Cantidad de lotes:", len(gdf))
print("CRS original:", gdf.crs)
print("Columnas:", list(gdf.columns))

if gdf.crs is None:
    raise ValueError("El GeoJSON no tiene CRS definido.")

gdf = gdf.to_crs("EPSG:32721")

if gdf.geometry.isna().any() or gdf.geometry.is_empty.any():
    raise ValueError("Existen geometrías vacías o nulas.")

superficie_ha = gdf.geometry.area / 10000

# Estimaciones por superficie, no conteos reales de raster.
area_pixel_saocom = 43.6 * 42.3
area_pixel_sentinel = 20 * 20

resultado = pd.DataFrame({
    "lote": range(1, len(gdf) + 1),
    "superficie_ha": superficie_ha.round(2),
    "pixeles_saocom_estimados": (
        superficie_ha * 10000 / area_pixel_saocom
    ).round().astype(int),
    "pixeles_sentinel20_estimados": (
        superficie_ha * 10000 / area_pixel_sentinel
    ).round().astype(int)
})

print("\n=== ESTIMACION POR LOTE ===")
print(resultado.to_string(index=False))

print("\n=== TOTALES ===")
print("Superficie total (ha):", round(superficie_ha.sum(), 2))
print(
    "Pixeles SAOCOM estimados:",
    resultado["pixeles_saocom_estimados"].sum()
)
print(
    "Pixeles Sentinel-2 estimados:",
    resultado["pixeles_sentinel20_estimados"].sum()
)

salida = Path("data/metadata/estimacion_pixeles_por_lote.csv")
salida.parent.mkdir(parents=True, exist_ok=True)

resultado.to_csv(salida, index=False, encoding="utf-8-sig")

print("\nArchivo generado:", salida)
