from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from rasterio.transform import from_origin, xy

POLIGONOS = Path("data/raw/vectores/potreros_la_rosaura.geojson")
METADATOS = Path("data/metadata/grilla_comun_saocom_L15_L16.csv")
SALIDA = Path("data/processed/grilla_espacial_L15_L16.csv")

gdf = gpd.read_file(POLIGONOS)
meta = pd.read_csv(METADATOS)

print("\n=== PASO 16E: GRILLA ESPACIAL ===")
print("CRS original:", gdf.crs)
print("Columnas del GeoJSON:", gdf.columns.tolist())

# Identificar la columna que contiene L15 y L16.
candidatas = []

for columna in gdf.columns:
    if columna == "geometry":
        continue

    valores = set(
        gdf[columna]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if {"L15", "L16"}.issubset(valores):
        candidatas.append(columna)

if len(candidatas) != 1:
    raise ValueError(
        "No se identifico una unica columna de lotes. "
        f"Candidatas: {candidatas}. "
        "Revisar atributos del GeoJSON."
    )

columna_lote = candidatas[0]
print("Columna identificadora:", columna_lote)

if gdf.crs is None:
    raise ValueError("El GeoJSON no declara un CRS.")

gdf = gdf.to_crs("EPSG:32721")
gdf["lote_id"] = (
    gdf[columna_lote].astype(str).str.strip().str.upper()
)

gdf = gdf[gdf["lote_id"].isin(["L15", "L16"])]

# Unir geometrías si un lote tiene más de una parte.
geometrias = {
    lote: grupo.geometry.union_all()
    for lote, grupo in gdf.groupby("lote_id")
}

registros = []

for _, m in meta.iterrows():
    lote = m["lote_id"]

    if lote not in geometrias:
        raise ValueError(f"No se encontro el poligono {lote}")

    resolucion = float(m["resolucion_m"])
    filas = int(m["filas_grilla"])
    columnas = int(m["columnas_grilla"])

    transform = from_origin(
        float(m["origen_x"]),
        float(m["origen_y"]),
        resolucion,
        resolucion
    )

    poligono = geometrias[lote]

    contador = 0

    for fila in range(filas):
        for columna in range(columnas):
            x, y = xy(
                transform,
                fila,
                columna,
                offset="center"
            )

            if poligono.covers(Point(x, y)):
                registros.append({
                    "celda_id": f"{lote}_F{fila:02d}_C{columna:02d}",
                    "lote_id": lote,
                    "fila_grilla": fila,
                    "columna_grilla": columna,
                    "x_utm": x,
                    "y_utm": y,
                    "resolucion_m": resolucion
                })
                contador += 1

    esperado = int(m["celdas_dentro_lote"])

    print(
        f"{lote}: {contador} celdas "
        f"(esperadas: {esperado})"
    )

    if contador != esperado:
        raise ValueError(
            f"Discrepancia en {lote}: "
            f"{contador} != {esperado}. "
            "No se guardara el archivo."
        )

grilla = pd.DataFrame(registros)

if grilla["celda_id"].duplicated().any():
    raise ValueError("Hay identificadores duplicados.")

SALIDA.parent.mkdir(parents=True, exist_ok=True)
grilla.to_csv(SALIDA, index=False)

print("\nGRILLA GENERADA CORRECTAMENTE")
print("Archivo:", SALIDA)
print("Total de celdas:", len(grilla))
print("\nPrimeras cinco celdas:")
print(grilla.head().to_string(index=False))
