from pathlib import Path
import zipfile
import io
import tempfile
import shutil
import rasterio

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = carpeta / "EOL1DSARSAO1A14056208.zip"

resultados = {}

with zipfile.ZipFile(producto) as exterior:
    internos = [
        n for n in exterior.namelist()
        if n.lower().endswith(".zip")
    ]

    if len(internos) != 1:
        raise ValueError("Se esperaba un unico ZIP interno.")

    with zipfile.ZipFile(io.BytesIO(exterior.read(internos[0]))) as interior:
        with tempfile.TemporaryDirectory() as temporal:

            for pol in ["hh", "hv", "vh", "vv"]:
                candidatos = [
                    n for n in interior.namelist()
                    if n.lower().startswith("data/")
                    and n.lower().endswith(f"-{pol}-m")
                ]

                if len(candidatos) != 1:
                    raise ValueError(
                        f"Raster {pol.upper()}: encontrados {len(candidatos)}"
                    )

                destino = Path(temporal) / f"{pol}.tif"

                with interior.open(candidatos[0]) as origen:
                    with destino.open("wb") as archivo:
                        shutil.copyfileobj(origen, archivo)

                with rasterio.open(destino) as src:
                    resultados[pol] = {
                        "crs": str(src.crs),
                        "ancho": src.width,
                        "alto": src.height,
                        "transform": tuple(src.transform),
                        "nodata": src.nodata
                    }

                print(
                    f"{pol.upper()}: "
                    f"{resultados[pol]['ancho']} x "
                    f"{resultados[pol]['alto']} | "
                    f"{resultados[pol]['crs']}"
                )

referencia = resultados["hh"]

alineados = all(
    resultados[pol]["crs"] == referencia["crs"]
    and resultados[pol]["ancho"] == referencia["ancho"]
    and resultados[pol]["alto"] == referencia["alto"]
    and resultados[pol]["transform"] == referencia["transform"]
    for pol in ["hv", "vh", "vv"]
)

print("\n=== VERIFICACION MULTIPOLARIZACION ===")
print("Las cuatro polarizaciones comparten grilla:", alineados)

if not alineados:
    for pol, datos in resultados.items():
        print(pol.upper(), datos)
