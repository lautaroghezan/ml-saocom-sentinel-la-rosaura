import geopandas as gpd

archivo = "data/raw/vectores/potreros_la_rosaura.geojson"

gdf = gpd.read_file(archivo).to_crs("EPSG:32721")

gdf["superficie_ha"] = (
    gdf.geometry.area / 10000
).round(2)

print("\n=== IDENTIFICADORES REALES DE LOS LOTES ===")
print(
    gdf[["lote_id", "superficie_ha"]]
    .to_string(index=True)
)

print("\nIdentificadores unicos:", gdf["lote_id"].is_unique)
print("Total de lotes:", len(gdf))
