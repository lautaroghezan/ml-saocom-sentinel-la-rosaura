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

geometrias = lotes.set_index("lote_id").geometry

print("\n=== VALIDACION GEOMETRICA GENERAL ===")

resultados = []

for lote_id, grupo in datos.groupby("lote_id"):

    if lote_id not in geometrias.index:
        raise ValueError(f"Lote desconocido: {lote_id}")

    poligono = geometrias.loc[lote_id]

    puntos = gpd.GeoSeries(
        gpd.points_from_xy(
            grupo["x_utm"],
            grupo["y_utm"]
        ),
        crs="EPSG:32721"
    )

    dentro = puntos.within(poligono)

    resultados.append({
        "lote_id": lote_id,
        "registros": len(grupo),
        "dentro": int(dentro.sum()),
        "fuera": int((~dentro).sum()),
        "fechas": grupo["fecha"].nunique()
    })

resumen = pd.DataFrame(resultados)

print(resumen.to_string(index=False))

duplicados = datos.duplicated(
    ["producto", "lote_id", "fila", "columna"]
).sum()

print("\n=== RESUMEN GENERAL ===")
print("Registros:", len(datos))
print("Centros dentro:", resumen["dentro"].sum())
print("Centros fuera:", resumen["fuera"].sum())
print("Duplicados:", duplicados)
print("Lotes:", len(resumen))
print("Fechas por lote (min):", resumen["fechas"].min())
print("Fechas por lote (max):", resumen["fechas"].max())

aprobado = (
    len(datos) == 11658
    and resumen["fuera"].sum() == 0
    and duplicados == 0
    and len(resumen) == 16
    and (resumen["fechas"] == 13).all()
)

print(
    "\nVALIDACION GENERAL:",
    "APROBADA" if aprobado else "REVISAR"
)

if not aprobado:
    raise ValueError(
        "Se encontraron inconsistencias geometricas."
    )
