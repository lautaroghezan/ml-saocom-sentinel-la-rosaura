from pathlib import Path
import zipfile
import io
import tempfile
import rasterio
import pandas as pd

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

registros = []

for producto in sorted(carpeta.glob("EOL1DSARSAO1A*.zip")):

    print("Inspeccionando:", producto.name, flush=True)

    with zipfile.ZipFile(producto) as z1:
        internos = [
            n for n in z1.namelist()
            if n.lower().endswith(".zip")
        ]

        if len(internos) != 1:
            raise RuntimeError(
                f"ZIP interno inesperado: {producto.name}"
            )

        with zipfile.ZipFile(io.BytesIO(z1.read(internos[0]))) as z2:

            rasters = [
                n for n in z2.namelist()
                if n.startswith("Data/")
                and n.lower().endswith("-hh-m")
            ]

            if len(rasters) != 1:
                raise RuntimeError(
                    f"Raster HH inesperado: {producto.name}"
                )

            with tempfile.TemporaryDirectory() as temporal:
                destino = Path(temporal) / "saocom_hh.tif"

                with z2.open(rasters[0]) as origen:
                    with destino.open("wb") as salida:
                        import shutil
                        shutil.copyfileobj(origen, salida)

                with rasterio.open(destino) as src:
                    registros.append({
                        "producto": producto.stem,
                        "crs": str(src.crs),
                        "epsg": src.crs.to_epsg() if src.crs else None,
                        "res_x": round(src.res[0], 4),
                        "res_y": round(src.res[1], 4),
                        "origen_x": round(src.transform.c, 2),
                        "origen_y": round(src.transform.f, 2)
                    })

df = pd.DataFrame(registros)

print("\n=== CRS REALES DE LOS 13 RASTERS ===")
print(df.to_string(index=False))

print("\n=== FRECUENCIA DE CRS ===")
print(df["crs"].value_counts(dropna=False))

salida = Path("data/metadata/crs_reales_saocom.csv")
salida.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(salida, index=False, encoding="utf-8-sig")

print("\nArchivo generado:", salida)
