from pathlib import Path
import rasterio

carpeta = Path(
    "data/interim/sentinel2/reflectancias"
)

archivos = sorted(carpeta.glob("*.tif"))

print("\n=== INVENTARIO SENTINEL-2 ===")
print("Carpeta:", carpeta.resolve())
print("Archivos GeoTIFF:", len(archivos))

if not archivos:
    raise FileNotFoundError(
        "No se encontraron GeoTIFF Sentinel-2."
    )

print("\n=== PRIMEROS CINCO ARCHIVOS ===")
for archivo in archivos[:5]:
    print(archivo.name)

print("\n=== ESTRUCTURA DEL PRIMER GEOTIFF ===")

with rasterio.open(archivos[0]) as src:

    print("Archivo:", archivos[0].name)
    print("CRS:", src.crs)
    print("Resolucion:", src.res)
    print("Dimensiones:", src.width, "x", src.height)
    print("Numero de bandas:", src.count)
    print("Tipos de datos:", src.dtypes)
    print("Nodata:", src.nodata)

    print("\n=== DESCRIPCIONES DE BANDAS ===")

    for i in range(1, src.count + 1):
        print(
            f"Banda {i}:",
            src.descriptions[i - 1],
            "| etiquetas:",
            src.tags(i)
        )

    print("\n=== ETIQUETAS GENERALES ===")
    print(src.tags())

print("\nInspeccion finalizada.")
