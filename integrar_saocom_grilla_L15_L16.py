from pathlib import Path
import zipfile
import tempfile
import shutil

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds, transform as window_transform
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin

BASE = Path.cwd()
CARPETA = Path.home() / "OneDrive/Documentos/La_Rosaura_SAOCOM_2024_25"

GRILLA = BASE / "data/processed/grilla_espacial_L15_L16.csv"
META = BASE / "data/metadata/grilla_comun_saocom_L15_L16.csv"
ORIGINAL = BASE / "data/processed/dataset_saocom_intralote.csv"
SALIDA = BASE / "data/processed/dataset_saocom_grilla_L15_L16.csv"

POLS = ["HH", "HV", "VH", "VV"]

grilla = pd.read_csv(GRILLA)
meta = pd.read_csv(META)
original = pd.read_csv(ORIGINAL)

if not CARPETA.exists():
    raise FileNotFoundError(f"No existe la carpeta SAOCOM: {CARPETA}")

if len(grilla) != 107 or grilla["celda_id"].duplicated().any():
    raise ValueError("Grilla espacial invalida.")

if not {"producto", "fecha"}.issubset(original.columns):
    raise ValueError("No se encontraron producto y fecha en SAOCOM.")

catalogo = original[["producto", "fecha"]].drop_duplicates().copy()
catalogo["fecha"] = pd.to_datetime(catalogo["fecha"]).dt.strftime("%Y-%m-%d")

if catalogo["fecha"].nunique() != 13:
    raise ValueError("Se esperaban 13 fechas SAOCOM.")

if catalogo["fecha"].duplicated().any():
    raise ValueError("Hay varios productos para una misma fecha.")

if catalogo["producto"].duplicated().any():
    raise ValueError("Un producto aparece asociado a varias fechas.")

catalogo = catalogo.sort_values("fecha").reset_index(drop=True)

m = meta.iloc[0]
res = float(m["resolucion_m"])
origen_x = float(m["origen_x"])
origen_y = float(m["origen_y"])
alto = int(m["filas_grilla"])
ancho = int(m["columnas_grilla"])

for _, otra in meta.iterrows():
    if (
        float(otra["resolucion_m"]) != res
        or float(otra["origen_x"]) != origen_x
        or float(otra["origen_y"]) != origen_y
        or int(otra["filas_grilla"]) != alto
        or int(otra["columnas_grilla"]) != ancho
    ):
        raise ValueError("Los lotes no comparten la misma grilla.")

transform_destino = from_origin(origen_x, origen_y, res, res)

izq = origen_x
der = origen_x + ancho * res
sup = origen_y
inf = origen_y - alto * res

filas = grilla["fila_grilla"].to_numpy(dtype=int)
columnas = grilla["columna_grilla"].to_numpy(dtype=int)

if (
    (filas < 0).any() or (filas >= alto).any()
    or (columnas < 0).any() or (columnas >= ancho).any()
):
    raise ValueError("Hay celdas fuera de la grilla.")

# Verificar coordenadas de los centros.
xs = origen_x + (columnas + 0.5) * res
ys = origen_y - (filas + 0.5) * res

if not (
    np.allclose(xs, grilla["x_utm"])
    and np.allclose(ys, grilla["y_utm"])
):
    raise ValueError("Coordenadas de celda inconsistentes.")

def reproyectar_polarizacion(interno, nombre, temporal):
    raster_path = temporal / "polarizacion.tif"

    with interno.open(nombre) as origen:
        with raster_path.open("wb") as destino:
            shutil.copyfileobj(origen, destino)

    try:
        with rasterio.open(raster_path) as src:
            if src.crs is None:
                raise ValueError("Raster SAOCOM sin CRS.")

            ventana = from_bounds(
                izq - res, inf - res,
                der + res, sup + res,
                transform=src.transform
            ).round_offsets().round_lengths()

            amplitud = src.read(
                1,
                window=ventana,
                boundless=True,
                fill_value=0
            ).astype(np.float32)

            amplitud[
                ~np.isfinite(amplitud) | (amplitud <= 0)
            ] = np.nan

            destino = np.full(
                (alto, ancho), np.nan, dtype=np.float32
            )

            reproject(
                source=amplitud,
                destination=destino,
                src_transform=window_transform(
                    ventana, src.transform
                ),
                src_crs=src.crs,
                dst_transform=transform_destino,
                dst_crs="EPSG:32721",
                src_nodata=np.nan,
                dst_nodata=np.nan,
                resampling=Resampling.nearest
            )

            valores = destino[filas, columnas].astype(float)
            validos = np.isfinite(valores) & (valores > 0)

            db = np.full(len(grilla), np.nan, dtype=float)
            db[validos] = 20 * np.log10(valores[validos])

            return db
    finally:
        raster_path.unlink(missing_ok=True)

registros = []

print("\n=== PASO 16H: REPROYECCION SAOCOM ===")
print("Productos:", len(catalogo))
print("Celdas:", len(grilla))
print("Polarizaciones:", ", ".join(POLS))

for numero, item in catalogo.iterrows():
    fecha = item["fecha"]
    producto = str(item["producto"]).strip()

    # Evitar coincidencias parciales entre identificadores.
    archivos = [
        p for p in CARPETA.glob("*.zip")
        if p.stem == producto
    ]

    if len(archivos) != 1:
        raise FileNotFoundError(
            f"{fecha}: se esperaba un ZIP para {producto}; "
            f"encontrados: {len(archivos)}"
        )

    resultado = grilla[["celda_id", "lote_id"]].copy()
    resultado["fecha"] = fecha
    resultado["producto"] = producto

    with zipfile.ZipFile(archivos[0]) as externo:
        internos = [
            n for n in externo.namelist()
            if n.lower().endswith(".zip")
        ]

        if len(internos) != 1:
            raise ValueError(
                f"{producto}: ZIP interno no identificado."
            )

        with tempfile.TemporaryDirectory() as tmp:
            temporal = Path(tmp)
            zip_interno = temporal / "interno.zip"

            with externo.open(internos[0]) as origen:
                with zip_interno.open("wb") as destino:
                    shutil.copyfileobj(origen, destino)

            with zipfile.ZipFile(zip_interno) as interno:
                nombres = interno.namelist()

                for pol in POLS:
                    candidatos = [
                        n for n in nombres
                        if n.lower().startswith("data/")
                        and n.lower().endswith(
                            f"-{pol.lower()}-m"
                        )
                    ]

                    if len(candidatos) != 1:
                        raise ValueError(
                            f"{producto}: raster {pol} "
                            "no identificado."
                        )

                    resultado[f"{pol}_db"] = (
                        reproyectar_polarizacion(
                            interno,
                            candidatos[0],
                            temporal
                        )
                    )

    registros.append(resultado)

    validos = {
        pol: int(resultado[f"{pol}_db"].notna().sum())
        for pol in POLS
    }

    print(
        f"[{numero + 1:02d}/13] {fecha} | "
        + " ".join(
            f"{pol}={validos[pol]}" for pol in POLS
        ),
        flush=True
    )

radar = pd.concat(registros, ignore_index=True)

if len(radar) != 107 * 13:
    raise ValueError("Cantidad inesperada de registros.")

if radar.duplicated(["celda_id", "fecha"]).any():
    raise ValueError("Duplicados de celda-fecha.")

# Control de la fecha critica ya analizada.
control = radar[
    radar["fecha"].isin(["2025-01-29", "2025-02-14"])
]

comparacion = control.pivot(
    index="celda_id",
    columns="fecha",
    values="HH_db"
)

delta = (
    comparacion["2025-02-14"]
    - comparacion["2025-01-29"]
)

lotes_por_celda = grilla.set_index("celda_id")["lote_id"]

print("\n=== CONTROL ENERO-FEBRERO HH ===")

for lote in ["L15", "L16"]:
    ids = lotes_por_celda[lotes_por_celda == lote].index
    valores = delta.reindex(ids).dropna()

    print(
        lote,
        "| comparables:", len(valores),
        "| mediana delta dB:",
        round(float(valores.median()), 3)
    )

SALIDA.parent.mkdir(parents=True, exist_ok=True)
radar.to_csv(SALIDA, index=False)

print("\n=== RESULTADO FINAL ===")
print("Archivo:", SALIDA)
print("Registros:", len(radar))
print("Celdas:", radar["celda_id"].nunique())
print("Fechas:", radar["fecha"].nunique())

print("\nValores disponibles:")
print(radar[[f"{p}_db" for p in POLS]].notna().sum())

print("\nADVERTENCIA METODOLOGICA:")
print("Conversion provisional 20*log10(amplitud).")
print("No se ha verificado calibracion absoluta sigma0.")
print("Resolucion efectiva radar no determinada.")
