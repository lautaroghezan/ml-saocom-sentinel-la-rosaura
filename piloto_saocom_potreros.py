from pathlib import Path
import geopandas as gpd
import rasterio
import pandas as pd
import re

BASE = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\ml-saocom-sentinel-la-rosaura"
)

# Raster piloto que extrajimos previamente
DATA_SAOCOM = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
    r"\piloto_20240907\Data"
)

GEOJSON = (
    BASE / "data" / "raw" / "vectores" /
    "potreros_la_rosaura.geojson"
)

SALIDA = (
    BASE / "data" / "processed" /
    "piloto_pixeles_saocom_por_lote.csv"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 1. Localizar los cuatro raster
# ------------------------------------------------------------

rasters = [
    p for p in DATA_SAOCOM.iterdir()
    if p.is_file() and p.suffix.lower() != ".xml"
]

def polarizacion(nombre):
    m = re.search(
        r"-(hh|hv|vh|vv)-m$",
        nombre.lower()
    )
    return m.group(1).upper() if m else "?"

rasters = sorted(rasters)

print("=" * 72)
print("PILOTO SAOCOM x POTREROS - 07/09/2024")
print("=" * 72)
print(f"Rasters encontrados: {len(rasters)}")

for r in rasters:
    print(f"  {polarizacion(r.name)} -> {r.name}")

if len(rasters) != 4:
    raise RuntimeError(
        f"Se esperaban 4 raster y se encontraron {len(rasters)}"
    )

# ------------------------------------------------------------
# 2. Usar HH como geometría de referencia
# ------------------------------------------------------------

raster_ref = next(
    r for r in rasters
    if polarizacion(r.name) == "HH"
)

with rasterio.open(raster_ref) as src:

    raster_crs = src.crs
    transform = src.transform

    print()
    print(f"CRS raster : {raster_crs}")
    print(f"Resolucion : {src.res}")
    print(f"Dimensiones: {src.width} x {src.height}")

# ------------------------------------------------------------
# 3. Leer potreros y llevarlos al CRS SAOCOM
# ------------------------------------------------------------

potreros = gpd.read_file(GEOJSON)

print()
print(f"Potreros: {len(potreros)}")
print(f"CRS original: {potreros.crs}")

potreros = potreros.to_crs(raster_crs)

# ------------------------------------------------------------
# 4. Crear grilla de píxeles SOLO alrededor de La Rosaura
# ------------------------------------------------------------

minx, miny, maxx, maxy = potreros.total_bounds

with rasterio.open(raster_ref) as src:

    # Ventana mínima que cubre todos los potreros
    window = rasterio.windows.from_bounds(
        minx, miny, maxx, maxy,
        transform=src.transform
    )

    # Redondear a píxeles completos
    window = window.round_offsets().round_lengths()

    row0 = int(window.row_off)
    col0 = int(window.col_off)
    height = int(window.height)
    width = int(window.width)

    print()
    print("Ventana La Rosaura:")
    print(f"  columnas : {width}")
    print(f"  filas    : {height}")
    print(f"  total    : {width * height} pixeles")

    registros = []

    for rr in range(row0, row0 + height):
        for cc in range(col0, col0 + width):

            # Bounds exactos del píxel
            x_left, y_bottom, x_right, y_top = rasterio.transform.array_bounds(
                1,
                1,
                rasterio.windows.transform(
                    rasterio.windows.Window(cc, rr, 1, 1),
                    src.transform
                )
            )

            from shapely.geometry import box, Point

            pixel_geom = box(
                x_left,
                y_bottom,
                x_right,
                y_top
            )

            centro = Point(
                (x_left + x_right) / 2,
                (y_bottom + y_top) / 2
            )

            for _, lote in potreros.iterrows():

                geom = lote.geometry

                if pixel_geom.intersects(geom):

                    area_inter = pixel_geom.intersection(geom).area
                    area_pixel = pixel_geom.area
                    fraccion = area_inter / area_pixel

                    registros.append({
                        "lote_id": lote["lote_id"],
                        "row": rr,
                        "col": cc,
                        "centro_dentro": geom.contains(centro),
                        "fraccion_pixel_lote": fraccion
                    })

# ------------------------------------------------------------
# 5. Resumen por lote
# ------------------------------------------------------------

df = pd.DataFrame(registros)

resumen = (
    df.groupby("lote_id")
      .agg(
          pixeles_intersectan=("lote_id", "size"),
          pixeles_centro_dentro=("centro_dentro", "sum"),
          pixeles_equivalentes=(
              "fraccion_pixel_lote",
              "sum"
          ),
          fraccion_media=(
              "fraccion_pixel_lote",
              "mean"
          )
      )
      .reset_index()
)

resumen["pixeles_centro_dentro"] = (
    resumen["pixeles_centro_dentro"].astype(int)
)

resumen["pixeles_equivalentes"] = (
    resumen["pixeles_equivalentes"].round(2)
)

resumen["fraccion_media"] = (
    resumen["fraccion_media"].round(3)
)

resumen.to_csv(
    SALIDA,
    index=False,
    encoding="utf-8-sig"
)

# ------------------------------------------------------------
# 6. Mostrar resultado
# ------------------------------------------------------------

print()
print("-" * 72)
print("PIXELES SAOCOM POR LOTE")
print("-" * 72)

print(resumen.to_string(index=False))

print()
print("-" * 72)
print("RESUMEN")
print("-" * 72)

print(
    f"Pixeles equivalentes totales: "
    f"{resumen['pixeles_equivalentes'].sum():.2f}"
)

print(
    f"Minimo por lote: "
    f"{resumen['pixeles_equivalentes'].min():.2f}"
)

print(
    f"Maximo por lote: "
    f"{resumen['pixeles_equivalentes'].max():.2f}"
)

print()
print("CSV generado:")
print(SALIDA)