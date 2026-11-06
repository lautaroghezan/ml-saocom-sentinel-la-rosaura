from pathlib import Path
import pandas as pd
import geopandas as gpd

base = Path.cwd()

datos = pd.read_csv(
    base / "data/processed/dataset_saocom_intralote.csv"
)

lotes = gpd.read_file(
    base / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

lote = lotes.loc[
    lotes["lote_id"] == "L02"
].iloc[0]

muestra = datos.loc[
    (datos["fecha"] == "2024-10-09")
    & (datos["lote_id"] == "L02")
].copy()

puntos = gpd.GeoSeries(
    gpd.points_from_xy(
        muestra["x_utm"],
        muestra["y_utm"]
    ),
    crs="EPSG:32721"
)

dentro = puntos.within(lote.geometry)
cubiertos = puntos.apply(lote.geometry.covers)

duplicados = muestra.duplicated(
    ["fila", "columna"]
).sum()

print("\n=== VALIDACION GEOMETRICA L02 ===")
print("Pixeles evaluados:", len(muestra))
print("Centros estrictamente dentro:", int(dentro.sum()))
print("Centros cubiertos por el poligono:", int(cubiertos.sum()))
print("Centros fuera:", int((~cubiertos).sum()))
print("Duplicados:", int(duplicados))

valido = (
    len(muestra) == 73
    and cubiertos.all()
    and duplicados == 0
)

print("\nVALIDACION:", "APROBADA" if valido else "REVISAR")

if not valido:
    raise ValueError(
        "La seleccion espacial requiere revision."
    )
