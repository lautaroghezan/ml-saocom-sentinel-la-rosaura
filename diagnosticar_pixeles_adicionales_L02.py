from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

base = Path.cwd()

general = pd.read_csv(
    base / "data/processed/dataset_saocom_intralote.csv"
)

piloto = pd.read_csv(
    base / "data/processed/piloto_saocom_L02_multipolarizacion_20241009.csv"
)

lotes = gpd.read_file(
    base / "data/raw/vectores/potreros_la_rosaura.geojson"
).to_crs("EPSG:32721")

poligono = lotes.loc[
    lotes["lote_id"] == "L02", "geometry"
].iloc[0]

muestra = general.loc[
    (general["fecha"] == "2024-10-09")
    & (general["lote_id"] == "L02")
].copy()

comparacion = muestra.merge(
    piloto[["fila", "columna"]],
    on=["fila", "columna"],
    how="left",
    indicator=True,
    validate="one_to_one"
)

adicionales = comparacion.loc[
    comparacion["_merge"] == "left_only"
].copy()

print("\n=== PIXELES ADICIONALES ===")
print("Cantidad:", len(adicionales))

for _, fila in adicionales.iterrows():

    punto = Point(
        float(fila["x_utm"]),
        float(fila["y_utm"])
    )

    print("\nFila raster:", fila["fila"])
    print("Columna raster:", fila["columna"])
    print("Coordenada X:", round(punto.x, 3))
    print("Coordenada Y:", round(punto.y, 3))

    print("Centro dentro:", poligono.contains(punto))
    print("Centro cubierto:", poligono.covers(punto))

    print(
        "Distancia al limite (m):",
        round(punto.distance(poligono.boundary), 3)
    )

    print(
        "Polarizaciones:",
        {
            p: fila[p]
            for p in ["HH_db", "HV_db", "VH_db", "VV_db"]
        }
    )

print("\nDiagnostico finalizado.")
