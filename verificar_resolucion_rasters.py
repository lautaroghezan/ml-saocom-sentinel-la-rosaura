from pathlib import Path
import rasterio

extensiones = {".tif", ".tiff"}
carpetas = [Path("data"), Path("raw")]

archivos = []
for carpeta in carpetas:
    if carpeta.exists():
        archivos.extend(
            p for p in carpeta.rglob("*")
            if p.suffix.lower() in extensiones
            and p.is_file()
        )

archivos = sorted(set(archivos))

print("=== INVENTARIO DE RASTERS ===")
print("Archivos encontrados:", len(archivos))

for archivo in archivos[:12]:
    print("\nARCHIVO:", archivo)
    try:
        with rasterio.open(archivo) as ds:
            print("CRS:", ds.crs)
            print("Dimensiones:", ds.width, "x", ds.height)
            print("Bandas:", ds.count)
            print("Resolucion de grilla:", ds.res)
            print("Transformacion:", ds.transform)
            print("Etiquetas:", ds.tags())
    except Exception as e:
        print("Error:", e)

if not archivos:
    print("No se encontraron GeoTIFF en data/ o raw/.")
