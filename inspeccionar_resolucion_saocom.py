from pathlib import Path
import zipfile
import io
import tempfile
import rasterio

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = sorted(carpeta.glob("EOL1DSARSAO1A*.zip"))[0]

print("PRODUCTO:", producto.name)

with zipfile.ZipFile(producto) as z1:
    internos = [
        n for n in z1.namelist()
        if n.lower().endswith(".zip")
    ]

    print("ZIP internos:", len(internos))

    with zipfile.ZipFile(io.BytesIO(z1.read(internos[0]))) as z2:
        rasters = [
            n for n in z2.namelist()
            if n.startswith("Data/")
            and n.lower().endswith(("-hh-m", "-hv-m", "-vh-m", "-vv-m"))
        ]

        print("Rasters encontrados:", len(rasters))

        if not rasters:
            raise RuntimeError("No se encontraron rasters SAOCOM.")

        nombre = sorted(rasters)[0]
        print("Raster:", nombre)

        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "saocom_prueba.tif"
            archivo.write_bytes(z2.read(nombre))

            with rasterio.open(archivo) as ds:
                print("\n=== METADATOS ESPACIALES ===")
                print("CRS:", ds.crs)
                print("Resolucion de grilla:", ds.res)
                print("Dimensiones:", ds.width, "x", ds.height)
                print("Bandas:", ds.count)
                print("Transformacion:", ds.transform)
                print("Bounds:", ds.bounds)
                print("Etiquetas:", ds.tags())
