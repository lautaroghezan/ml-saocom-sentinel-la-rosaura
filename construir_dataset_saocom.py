from pathlib import Path
import zipfile
import io
import re
import tempfile

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask


# ============================================================
# CONFIGURACION
# ============================================================

BASE_REPO = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\ml-saocom-sentinel-la-rosaura"
)

CARPETA_SAOCOM = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

GEOJSON = (
    BASE_REPO
    / "data"
    / "raw"
    / "vectores"
    / "potreros_la_rosaura.geojson"
)

SALIDA = (
    BASE_REPO
    / "data"
    / "processed"
    / "dataset_saocom_potreros.csv"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# FECHAS VERIFICADAS
# ============================================================

FECHAS = {
    "EOL1DSARSAO1A14948973": "2024-08-06",
    "EOL1DSARSAO1A14948810": "2024-09-07",
    "EOL1DSARSAO1A14948841": "2024-09-23",
    "EOL1DSARSAO1A14056208": "2024-10-09",
    "EOL1DSARSAO1A14948886": "2024-10-25",
    "EOL1DSARSAO1A14948797": "2024-11-10",
    "EOL1DSARSAO1A15392623": "2024-12-12",
    "EOL1DSARSAO1A14948812": "2024-12-28",
    "EOL1DSARSAO1A14065611": "2025-01-13",
    "EOL1DSARSAO1A14065934": "2025-01-29",
    "EOL1DSARSAO1A14065630": "2025-02-14",
    "EOL1DSARSAO1A14065953": "2025-03-02",
    "EOL1DSARSAO1A14065706": "2025-03-18",
}


# ============================================================
# FUNCIONES
# ============================================================

def detectar_polarizacion(nombre):

    nombre = nombre.lower()

    m = re.search(
        r"-(hh|hv|vh|vv)-m$",
        nombre
    )

    if m:
        return m.group(1).upper()

    return None


def estadisticas(valores):

    valores = valores[
        np.isfinite(valores)
    ]

    # Sigma0Type = AMPLITUDE.
    # El logaritmo sólo está definido para A > 0.
    valores = valores[
        valores > 0
    ]

    if len(valores) == 0:
        return None

    # Conversión documentada:
    # sigma0_dB = 20 log10(amplitud)
    db = 20.0 * np.log10(valores)

    p25 = np.percentile(db, 25)
    mediana = np.percentile(db, 50)
    p75 = np.percentile(db, 75)

    return {
        "n_validos": len(db),
        "media_db": np.mean(db),
        "mediana_db": mediana,
        "p25_db": p25,
        "p75_db": p75,
        "iqr_db": p75 - p25,
        "std_db": np.std(db, ddof=1)
                  if len(db) > 1 else np.nan,
        "min_db": np.min(db),
        "max_db": np.max(db)
    }


# ============================================================
# CARGAR POTREROS
# ============================================================

potreros_original = gpd.read_file(
    GEOJSON
)

if len(potreros_original) != 16:
    raise RuntimeError(
        f"Se esperaban 16 potreros; "
        f"se encontraron {len(potreros_original)}."
    )


# ============================================================
# PRODUCTOS
# ============================================================

productos = sorted(
    CARPETA_SAOCOM.glob(
        "EOL1DSARSAO1A*.zip"
    )
)

print("=" * 75)
print("CONSTRUCCION DATASET SAOCOM - LA ROSAURA")
print("=" * 75)

print(
    f"Productos encontrados : {len(productos)}"
)

if len(productos) != 13:
    raise RuntimeError(
        f"Se esperaban 13 productos y "
        f"se encontraron {len(productos)}."
    )


registros = []


# ============================================================
# PROCESAMIENTO
# ============================================================

for numero, producto in enumerate(
    productos, 1
):

    producto_id = producto.stem

    if producto_id not in FECHAS:
        raise RuntimeError(
            f"Producto sin fecha definida: "
            f"{producto_id}"
        )

    fecha = FECHAS[producto_id]

    print()
    print("-" * 75)
    print(
        f"[{numero:02d}/13] "
        f"{fecha} | {producto_id}"
    )
    print("-" * 75)

    with zipfile.ZipFile(
        producto, "r"
    ) as z1:

        internos = [
            n for n in z1.namelist()
            if n.lower().endswith(".zip")
        ]

        if len(internos) != 1:
            raise RuntimeError(
                f"{producto_id}: "
                f"ZIP internos={len(internos)}"
            )

        contenido_interno = z1.read(
            internos[0]
        )

    with zipfile.ZipFile(
        io.BytesIO(contenido_interno),
        "r"
    ) as z2:

        rasters = [
            n for n in z2.namelist()
            if n.startswith("Data/")
            and not n.lower().endswith(".xml")
            and detectar_polarizacion(
                Path(n).name
            )
        ]

        if len(rasters) != 4:
            raise RuntimeError(
                f"{producto_id}: "
                f"se esperaban 4 raster, "
                f"se encontraron {len(rasters)}"
            )

        for raster_nombre in sorted(
            rasters
        ):

            pol = detectar_polarizacion(
                Path(raster_nombre).name
            )

            print(
                f"  Procesando {pol}..."
            )

            # Extraemos sólo este raster a un
            # archivo temporal.
            with tempfile.NamedTemporaryFile(
                suffix=".tif",
                delete=False
            ) as tmp:

                tmp.write(
                    z2.read(raster_nombre)
                )

                tmp_path = Path(tmp.name)

            try:

                with rasterio.open(
                    tmp_path
                ) as src:

                    # Cada adquisición puede tener
                    # geometría ligeramente diferente.
                    potreros = (
                        potreros_original
                        .to_crs(src.crs)
                    )

                    for _, lote in (
                        potreros.iterrows()
                    ):

                        lote_id = lote[
                            "lote_id"
                        ]

                        # all_touched=False:
                        # evita incorporar cualquier
                        # pixel que sólo roce el borde.
                        recorte, _ = mask(
                            src,
                            [lote.geometry],
                            crop=True,
                            all_touched=False,
                            filled=False
                        )

                        banda = recorte[0]

                        if np.ma.isMaskedArray(
                            banda
                        ):
                            valores = (
                                banda.compressed()
                            )
                        else:
                            valores = (
                                banda.ravel()
                            )

                        n_extraidos = len(
                            valores
                        )

                        est = estadisticas(
                            valores
                        )

                        if est is None:

                            registros.append({
                                "fecha": fecha,
                                "producto_id":
                                    producto_id,
                                "lote_id":
                                    lote_id,
                                "polarizacion":
                                    pol,
                                "n_extraidos":
                                    n_extraidos,
                                "n_validos": 0,
                                "pct_validos": 0.0,
                                "media_db":
                                    np.nan,
                                "mediana_db":
                                    np.nan,
                                "p25_db":
                                    np.nan,
                                "p75_db":
                                    np.nan,
                                "iqr_db":
                                    np.nan,
                                "std_db":
                                    np.nan,
                                "min_db":
                                    np.nan,
                                "max_db":
                                    np.nan
                            })

                            continue

                        pct_validos = (
                            est["n_validos"]
                            / n_extraidos
                            * 100
                            if n_extraidos > 0
                            else 0
                        )

                        registros.append({
                            "fecha": fecha,
                            "producto_id":
                                producto_id,
                            "lote_id":
                                lote_id,
                            "polarizacion":
                                pol,
                            "n_extraidos":
                                n_extraidos,
                            "n_validos":
                                est["n_validos"],
                            "pct_validos":
                                pct_validos,
                            "media_db":
                                est["media_db"],
                            "mediana_db":
                                est["mediana_db"],
                            "p25_db":
                                est["p25_db"],
                            "p75_db":
                                est["p75_db"],
                            "iqr_db":
                                est["iqr_db"],
                            "std_db":
                                est["std_db"],
                            "min_db":
                                est["min_db"],
                            "max_db":
                                est["max_db"]
                        })

            finally:

                if tmp_path.exists():
                    tmp_path.unlink()


# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(
    registros
)

df["fecha"] = pd.to_datetime(
    df["fecha"]
)

df = df.sort_values(
    [
        "fecha",
        "lote_id",
        "polarizacion"
    ]
).reset_index(drop=True)


# ============================================================
# CONTROL DE INTEGRIDAD
# ============================================================

esperados = 13 * 16 * 4

print()
print("=" * 75)
print("CONTROL FINAL")
print("=" * 75)

print(
    f"Registros esperados : {esperados}"
)

print(
    f"Registros obtenidos : {len(df)}"
)

print(
    f"Fechas              : "
    f"{df['fecha'].nunique()}"
)

print(
    f"Lotes               : "
    f"{df['lote_id'].nunique()}"
)

print(
    f"Polarizaciones      : "
    f"{sorted(df['polarizacion'].unique())}"
)

duplicados = df.duplicated(
    subset=[
        "fecha",
        "lote_id",
        "polarizacion"
    ]
).sum()

print(
    f"Duplicados          : {duplicados}"
)

faltantes = df[
    [
        "mediana_db",
        "p25_db",
        "p75_db"
    ]
].isna().any(axis=1).sum()

print(
    f"Filas sin estadisticas: "
    f"{faltantes}"
)


# ============================================================
# RANGOS DIAGNOSTICOS
# ============================================================

print()
print("-" * 75)
print("RANGOS OBSERVADOS POR POLARIZACION")
print("-" * 75)

resumen_pol = (
    df.groupby("polarizacion")
      .agg(
          registros=(
              "polarizacion",
              "size"
          ),
          n_validos_min=(
              "n_validos",
              "min"
          ),
          n_validos_mediana=(
              "n_validos",
              "median"
          ),
          mediana_db_min=(
              "mediana_db",
              "min"
          ),
          mediana_db_mediana=(
              "mediana_db",
              "median"
          ),
          mediana_db_max=(
              "mediana_db",
              "max"
          ),
          pct_validos_min=(
              "pct_validos",
              "min"
          )
      )
)

print(
    resumen_pol.round(2).to_string()
)


# ============================================================
# GUARDAR
# ============================================================

df.to_csv(
    SALIDA,
    index=False,
    encoding="utf-8-sig",
    date_format="%Y-%m-%d"
)

print()
print("=" * 75)
print("DATASET GENERADO")
print("=" * 75)

print(SALIDA)