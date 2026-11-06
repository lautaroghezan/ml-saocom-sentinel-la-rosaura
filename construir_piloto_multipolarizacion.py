from pathlib import Path
import zipfile
import io
import tempfile
import shutil

import numpy as np
import pandas as pd
import rasterio

BASE = Path.cwd()

CARPETA = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

PRODUCTO = CARPETA / "EOL1DSARSAO1A14056208.zip"

ENTRADA = BASE / "data/processed/piloto_saocom_L02_HH_20241009.csv"
SALIDA = BASE / "data/processed/piloto_saocom_L02_multipolarizacion_20241009.csv"

df = pd.read_csv(ENTRADA)

if df.empty:
    raise ValueError("El dataset HH esta vacio.")

if df[["fila", "columna"]].duplicated().any():
    raise ValueError("Existen pixeles duplicados.")

filas = df["fila"].to_numpy(dtype=int)
columnas = df["columna"].to_numpy(dtype=int)

resultado = df[
    ["producto", "fecha", "lote_id",
     "fila", "columna", "x_utm", "y_utm"]
].copy()

resultado["HH_db"] = df["sigma0_db"]

with zipfile.ZipFile(PRODUCTO) as exterior:

    internos = [
        n for n in exterior.namelist()
        if n.lower().endswith(".zip")
    ]

    if len(internos) != 1:
        raise ValueError("Se esperaba un unico ZIP interno.")

    with zipfile.ZipFile(io.BytesIO(exterior.read(internos[0]))) as interior:

        with tempfile.TemporaryDirectory() as temporal:

            for pol in ["HV", "VH", "VV"]:

                candidatos = [
                    n for n in interior.namelist()
                    if n.lower().startswith("data/")
                    and n.lower().endswith(f"-{pol.lower()}-m")
                ]

                if len(candidatos) != 1:
                    raise ValueError(
                        f"No se encontro un unico raster {pol}."
                    )

                destino = Path(temporal) / f"{pol}.tif"

                with interior.open(candidatos[0]) as origen:
                    with destino.open("wb") as archivo:
                        shutil.copyfileobj(origen, archivo)

                with rasterio.open(destino) as src:

                    if src.crs.to_epsg() != 32721:
                        raise ValueError(f"CRS inesperado en {pol}.")

                    if (
                        (filas >= src.height).any()
                        or (columnas >= src.width).any()
                        or (filas < 0).any()
                        or (columnas < 0).any()
                    ):
                        raise ValueError(
                            f"Indices fuera del raster {pol}."
                        )

                    # Lectura de una ventana pequena alrededor del lote.
                    fila_min = int(filas.min())
                    fila_max = int(filas.max())
                    col_min = int(columnas.min())
                    col_max = int(columnas.max())

                    from rasterio.windows import Window

                    ventana = Window(
                        col_min,
                        fila_min,
                        col_max - col_min + 1,
                        fila_max - fila_min + 1
                    )

                    datos = src.read(
                        1,
                        window=ventana,
                        masked=True
                    )

                    valores = np.asarray(
                        datos.data[
                            filas - fila_min,
                            columnas - col_min
                        ],
                        dtype=float
                    )

                    mascara = np.ma.getmaskarray(datos)[
                        filas - fila_min,
                        columnas - col_min
                    ]

                    validos = (
                        ~mascara
                        & np.isfinite(valores)
                        & (valores > 0)
                    )

                    db = np.full(len(df), np.nan)

                    db[validos] = (
                        20 * np.log10(valores[validos])
                    )

                    resultado[f"{pol}_db"] = db

                    print(
                        f"{pol}: "
                        f"{validos.sum()} valores validos "
                        f"de {len(df)}"
                    )

                destino.unlink()

completos = resultado[
    ["HH_db", "HV_db", "VH_db", "VV_db"]
].notna().all(axis=1)

print("\n=== DATASET MULTIPOLARIZACION ===")
print("Pixeles HH iniciales:", len(resultado))
print("Pixeles con cuatro polarizaciones validas:", completos.sum())
print("Pixeles incompletos:", (~completos).sum())

print("\n=== ESTADISTICAS POR POLARIZACION ===")
print(
    resultado[
        ["HH_db", "HV_db", "VH_db", "VV_db"]
    ].describe().round(3)
)

print("\n=== PRIMERAS OBSERVACIONES ===")
print(resultado.head(10).round(3).to_string(index=False))

SALIDA.parent.mkdir(parents=True, exist_ok=True)

resultado.to_csv(
    SALIDA,
    index=False,
    encoding="utf-8-sig"
)

print("\nArchivo generado:", SALIDA)
