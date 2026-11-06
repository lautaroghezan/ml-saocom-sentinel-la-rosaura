from pathlib import Path
import zipfile
import tempfile
import rasterio
import pandas as pd

BASE = Path.cwd()

CARPETA_SAOCOM = (
    Path.home()
    / "OneDrive/Documentos/La_Rosaura_SAOCOM_2024_25"
)

PRODUCTOS = {
    "2025-01-29": "EOL1DSARSAO1A14065934",
    "2025-02-14": "EOL1DSARSAO1A14065630"
}

resultados = []

for fecha, producto in PRODUCTOS.items():

    archivos = list(
        CARPETA_SAOCOM.glob(f"*{producto}*.zip")
    )

    if len(archivos) != 1:
        raise FileNotFoundError(
            f"Se esperaba un ZIP para {producto}; encontrados: {len(archivos)}"
        )

    with zipfile.ZipFile(archivos[0]) as externo:

        internos = [
            n for n in externo.namelist()
            if n.lower().endswith(".zip")
        ]

        if len(internos) != 1:
            raise ValueError("Estructura ZIP inesperada")

        with tempfile.TemporaryDirectory() as tmp:

            zip_interno = Path(tmp) / "interno.zip"
            zip_interno.write_bytes(
                externo.read(internos[0])
            )

            with zipfile.ZipFile(zip_interno) as interno:

                candidatos = [
                    n for n in interno.namelist()
                    if n.lower().startswith("data/")
                    and n.lower().endswith("-hh-m")
                ]

                if len(candidatos) != 1:
                    raise ValueError(
                        f"Raster HH no identificado: {producto}"
                    )

                raster_tmp = Path(tmp) / "hh.tif"

                with interno.open(candidatos[0]) as origen:
                    with raster_tmp.open("wb") as destino:
                        import shutil
                        shutil.copyfileobj(origen, destino)

                with rasterio.open(raster_tmp) as src:

                    resultados.append({
                        "fecha": fecha,
                        "producto": producto,
                        "crs": str(src.crs),
                        "ancho": src.width,
                        "alto": src.height,
                        "pixel_x_m": src.res[0],
                        "pixel_y_m": src.res[1],
                        "origen_x": src.transform.c,
                        "origen_y": src.transform.f,
                        "nodata": src.nodata
                    })

resultado = pd.DataFrame(resultados)

SALIDA = (
    BASE / "data/metadata"
    / "grillas_saocom_enero_febrero_2025.csv"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)
resultado.to_csv(SALIDA, index=False)

print("\n=== GRILLAS ORIGINALES SAOCOM ===")
print(resultado.to_string(index=False))

print("\n=== COMPARACION ===")
print(
    "Mismo CRS:",
    resultado["crs"].nunique() == 1
)
print(
    "Mismo origen X:",
    resultado["origen_x"].nunique() == 1
)
print(
    "Mismo origen Y:",
    resultado["origen_y"].nunique() == 1
)

print("\nArchivo:", SALIDA)
print("Diagnostico finalizado.")
