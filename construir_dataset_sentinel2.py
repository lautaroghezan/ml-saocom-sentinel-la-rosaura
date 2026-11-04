
import os
import io
import json
import time
import zipfile
import argparse
from pathlib import Path
from email.parser import BytesParser
from email import policy

import requests
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask

# =====================================================
# CONFIGURACION
# =====================================================

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)

PROCESS_URL = (
    "https://sh.dataspace.copernicus.eu/api/v1/process"
)

BASE = Path("data")
CATALOGO = BASE / "processed/catalogo_sentinel2_analitico_2024_25.csv"
LOTES = BASE / "raw/vectores/potreros_la_rosaura.geojson"

CARPETA = BASE / "interim/sentinel2/reflectancias"
SALIDA = BASE / "processed/dataset_sentinel2_potreros.csv"
TRAZAS = BASE / "processed/trazabilidad_sentinel2.csv"
ERRORES = BASE / "processed/errores_reflectancias_sentinel2.csv"

CRS = "EPSG:32721"
RES = 20
NODATA = -9999

VARIABLES = {
    "B04": 0,
    "B05": 1,
    "B08": 2,
    "B8A": 3,
    "B11": 4,
    "NDVI": 6,
    "NDRE": 7,
    "NDMI": 8,
}

CARPETA.mkdir(parents=True, exist_ok=True)
SALIDA.parent.mkdir(parents=True, exist_ok=True)

# =====================================================
# EVALSCRIPT
# =====================================================

EVALSCRIPT = """
//VERSION=3

function setup() {
    return {
        input: [{
            bands: [
                "B04", "B05", "B08", "B8A", "B11",
                "SCL", "dataMask"
            ],
            units: [
                "REFLECTANCE", "REFLECTANCE",
                "REFLECTANCE", "REFLECTANCE",
                "REFLECTANCE", "DN", "DN"
            ]
        }],
        output: {
            id: "default",
            bands: 10,
            sampleType: "FLOAT32"
        },
        mosaicking: "ORBIT"
    };
}

function evaluatePixel(samples) {
    let s = samples[0];

    if (!s) {
        return [
            -9999, -9999, -9999, -9999, -9999,
            -9999, -9999, -9999, -9999, 0
        ];
    }

    let valid = s.dataMask === 1 &&
        [4, 5, 6].includes(s.SCL);

    function indice(a, b) {
        if (!valid || !Number.isFinite(a) ||
            !Number.isFinite(b) || (a + b) === 0) {
            return -9999;
        }
        return (a - b) / (a + b);
    }

    return [
        valid ? s.B04 : -9999,
        valid ? s.B05 : -9999,
        valid ? s.B08 : -9999,
        valid ? s.B8A : -9999,
        valid ? s.B11 : -9999,
        s.SCL,
        indice(s.B08, s.B04),
        indice(s.B8A, s.B05),
        indice(s.B08, s.B11),
        s.dataMask
    ];
}

function updateOutputMetadata(
    scenes, inputMetadata, outputMetadata
) {
    outputMetadata.userData = {
        adquisiciones: (scenes.orbits || []).map(function(orbita) {
            return {
                fecha: orbita.date
                    ? orbita.date.toISOString()
                    : null,
                escenas: (orbita.tiles || []).map(function(tile) {
                    return {
                        id: tile.id || null,
                        fecha: tile.date
                            ? String(tile.date)
                            : null,
                        cobertura_nubes: tile.cloudCoverage
                    };
                })
            };
        })
    };
}
"""

# =====================================================
# AUTENTICACION
# =====================================================

def obtener_token():
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["CDSE_CLIENT_ID"],
            "client_secret": os.environ["CDSE_CLIENT_SECRET"],
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


# =====================================================
# INTERPRETACION DE RESPUESTA
# =====================================================

def interpretar_respuesta(r):
    tipo = r.headers.get("Content-Type", "")

    print("  HTTP:", r.status_code)
    print("  Content-Type:", tipo)
    print("  Bytes:", len(r.content))

    partes = []

    if zipfile.is_zipfile(io.BytesIO(r.content)):
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            partes = [
                (n, z.read(n))
                for n in z.namelist()
                if not n.endswith("/")
            ]

    elif "multipart/" in tipo.lower():
        encabezado = (
            "MIME-Version: 1.0\r\n"
            f"Content-Type: {tipo}\r\n\r\n"
        ).encode()

        mensaje = BytesParser(
            policy=policy.default
        ).parsebytes(encabezado + r.content)

        for i, parte in enumerate(mensaje.iter_parts()):
            nombre = parte.get_filename() or f"parte_{i}"
            partes.append(
                (nombre, parte.get_payload(decode=True))
            )

    elif (
        r.content[:4] in (b"II*\x00", b"MM\x00*")
        or "image/tiff" in tipo.lower()
    ):
        partes = [("default.tif", r.content)]

    else:
        raise RuntimeError(
            f"Formato inesperado: {tipo}; "
            f"inicio={r.content[:100]!r}"
        )

    tiff = None
    metadata = None

    for nombre, contenido in partes:
        if (
            contenido[:4] in (b"II*\x00", b"MM\x00*")
            or nombre.lower().endswith((".tif", ".tiff"))
        ):
            tiff = contenido

        elif (
            nombre.lower().endswith(".json")
            or contenido.lstrip().startswith(b"{")
        ):
            try:
                metadata = json.loads(
                    contenido.decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError):
                pass

    if tiff is None:
        raise RuntimeError(
            "La respuesta no contiene un GeoTIFF. "
            f"Partes: {[n for n, _ in partes]}"
        )

    return tiff, metadata


# =====================================================
# DESCARGA
# =====================================================

def descargar(fecha, producto, token, bbox, ancho, alto):
    archivo = CARPETA / f"S2_{fecha}_20m.tif"
    metadatos = CARPETA / f"S2_{fecha}_metadata.json"

    # Solo reutilizar archivos de esta version
    if archivo.exists() and metadatos.exists():
        try:
            info = json.loads(
                metadatos.read_text(encoding="utf-8")
            )
            with rasterio.open(archivo) as src:
                correcto = (
                    src.count == 10
                    and src.width == ancho
                    and src.height == alto
                    and src.crs.to_string() == CRS
                    and np.allclose(src.res, (RES, RES))
                    and np.allclose(tuple(src.bounds), bbox)
                    and info.get("producto_catalogado") == producto
                )
            if correcto:
                return archivo, metadatos, token
        except (OSError, ValueError, KeyError):
            pass

    fin = (
        pd.Timestamp(fecha) + pd.Timedelta(days=1)
    ).strftime("%Y-%m-%dT00:00:00Z")

    payload = {
        "input": {
            "bounds": {
                "bbox": list(bbox),
                "properties": {
                    "crs": (
                        "http://www.opengis.net/"
                        "def/crs/EPSG/0/32721"
                    )
                },
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": fecha + "T00:00:00Z",
                        "to": fin,
                    },
                    "mosaickingOrder": "leastCC",
                },
            }],
        },
        "output": {
            "width": ancho,
            "height": alto,
            "responses": [
                {
                    "identifier": "default",
                    "format": {"type": "image/tiff"},
                },
                {
                    "identifier": "userdata",
                    "format": {"type": "application/json"},
                },
            ],
        },
        "evalscript": EVALSCRIPT,
    }

    for intento in range(1, 5):
        r = requests.post(
            PROCESS_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "multipart/mixed",
            },
            json=payload,
            timeout=180,
        )

        if r.status_code == 401:
            token = obtener_token()
            continue

        if r.status_code in (429, 500, 502, 503, 504):
            print("  Reintento:", intento)
            time.sleep(3 * intento)
            continue

        if not r.ok:
            raise RuntimeError(
                f"HTTP {r.status_code}: {r.text[:1500]}"
            )

        contenido, metadata = interpretar_respuesta(r)

        temporal = archivo.with_suffix(".tmp.tif")

        try:
            temporal.write_bytes(contenido)

            with rasterio.open(temporal) as src:
                correcto = (
                    src.count == 10
                    and src.width == ancho
                    and src.height == alto
                    and src.crs.to_string() == CRS
                    and np.allclose(src.res, (RES, RES))
                    and np.allclose(tuple(src.bounds), bbox)
                )

            if not correcto:
                raise RuntimeError(
                    "Geometria o bandas TIFF incorrectas"
                )

            temporal.replace(archivo)

        finally:
            if temporal.exists():
                temporal.unlink()

        info = {
            "fecha": fecha,
            "producto_catalogado": producto,
            "metadata_recibida": metadata is not None,
            "metadata": metadata,
        }

        metadatos.write_text(
            json.dumps(info, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return archivo, metadatos, token

    raise RuntimeError(
        "Solicitud fallida tras cuatro intentos"
    )


# =====================================================
# ESTADISTICAS POR LOTE
# =====================================================

def procesar_lotes(archivo, fecha, producto, lotes):
    filas = []

    with rasterio.open(archivo) as src:
        for _, lote in lotes.iterrows():
            recorte, _ = mask(
                src,
                [lote.geometry],
                crop=True,
                filled=False,
                all_touched=False,
            )

            dentro = ~np.ma.getmaskarray(recorte[0])
            n_pixeles = int(dentro.sum())

            if n_pixeles == 0:
                raise RuntimeError(
                    f"Sin pixeles: {lote['lote_id']}"
                )

            scl = recorte[5].data
            data_mask = recorte[9].data

            validos = (
                dentro
                & (data_mask == 1)
                & np.isin(scl, [4, 5, 6])
            )

            fila = {
                "fecha": fecha,
                "lote_id": lote["lote_id"],
                "producto_catalogado": producto,
                "n_pixeles": n_pixeles,
                "n_validos_scl": int(validos.sum()),
                "pct_validos_scl": round(
                    100 * validos.sum() / n_pixeles, 2
                ),
            }

            for nombre, posicion in VARIABLES.items():
                datos = recorte[posicion].data

                mascara = (
                    validos
                    & np.isfinite(datos)
                    & (datos != NODATA)
                )

                if nombre in ("NDVI", "NDRE", "NDMI"):
                    mascara &= (
                        (datos >= -1) & (datos <= 1)
                    )

                valores = datos[mascara]

                fila[f"{nombre}_n"] = len(valores)

                for estadistico in (
                    "mediana", "p25", "p75", "iqr"
                ):
                    fila[f"{nombre}_{estadistico}"] = np.nan

                if len(valores):
                    p25, p75 = np.percentile(
                        valores, [25, 75]
                    )

                    fila[f"{nombre}_mediana"] = float(
                        np.median(valores)
                    )
                    fila[f"{nombre}_p25"] = float(p25)
                    fila[f"{nombre}_p75"] = float(p75)
                    fila[f"{nombre}_iqr"] = float(
                        p75 - p25
                    )

            filas.append(fila)

    return filas


# =====================================================
# GUARDADO PROGRESIVO
# =====================================================

def guardar(path, filas, claves):
    nuevo = pd.DataFrame(filas)

    if path.exists():
        anterior = pd.read_csv(
            path, dtype={"fecha": str}
        )
        nuevo = pd.concat(
            [anterior, nuevo], ignore_index=True
        )

    nuevo = nuevo.drop_duplicates(
        claves, keep="last"
    ).sort_values(claves)

    nuevo.to_csv(path, index=False)


# =====================================================
# PROGRAMA PRINCIPAL
# =====================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--todas",
        action="store_true",
        help="Procesar las 69 fechas"
    )

    parser.add_argument(
        "--fecha",
        default="2024-09-04",
        help="Fecha para prueba piloto"
    )

    args = parser.parse_args()

    catalogo = pd.read_csv(
        CATALOGO, dtype={"fecha": str}
    ).sort_values("fecha")

    if catalogo["fecha"].duplicated().any():
        raise ValueError(
            "El catalogo contiene fechas duplicadas"
        )

    if not args.todas:
        catalogo = catalogo[
            catalogo["fecha"] == args.fecha
        ].copy()

    if catalogo.empty:
        raise ValueError(
            "No hay fechas para procesar"
        )

    lotes = gpd.read_file(LOTES).to_crs(CRS)

    if (
        len(lotes) != 16
        or lotes["lote_id"].nunique() != 16
        or not lotes.geometry.is_valid.all()
    ):
        raise ValueError(
            "Error en geometria de lotes"
        )

    xmin, ymin, xmax, ymax = lotes.total_bounds

    bbox = (
        float(np.floor((xmin - 40) / RES) * RES),
        float(np.floor((ymin - 40) / RES) * RES),
        float(np.ceil((xmax + 40) / RES) * RES),
        float(np.ceil((ymax + 40) / RES) * RES),
    )

    ancho = round((bbox[2] - bbox[0]) / RES)
    alto = round((bbox[3] - bbox[1]) / RES)

    print("Fechas seleccionadas:", len(catalogo))
    print("Lotes:", len(lotes))
    print("Grilla:", ancho, "x", alto)

    completas = set()

    if SALIDA.exists():
        anterior = pd.read_csv(
            SALIDA, dtype={"fecha": str}
        )

        conteos = anterior.groupby(
            "fecha"
        )["lote_id"].nunique()

        completas = set(
            conteos[conteos == 16].index
        )

    token = obtener_token()

    for _, escena in catalogo.iterrows():
        fecha = escena["fecha"]
        producto = escena["product_id"]

        if fecha in completas:
            print(fecha, "YA PROCESADA")
            continue

        print("\nProcesando:", fecha)

        try:
            archivo, metadata_path, token = descargar(
                fecha, producto, token,
                bbox, ancho, alto
            )

            filas = procesar_lotes(
                archivo, fecha, producto, lotes
            )

            if len(filas) != 16:
                raise RuntimeError(
                    "No se obtuvieron 16 registros"
                )

            info = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            guardar(
                SALIDA, filas,
                ["fecha", "lote_id"]
            )

            guardar(
                TRAZAS,
                [{
                    "fecha": fecha,
                    "producto_catalogado": producto,
                    "metadata_recibida": (
                        info["metadata_recibida"]
                    ),
                    "metadata_escenas": json.dumps(
                        info["metadata"],
                        ensure_ascii=False
                    ),
                    "archivo_tiff": str(archivo),
                }],
                ["fecha"],
            )

            calidad = np.mean([
                f["pct_validos_scl"]
                for f in filas
            ])

            print(
                "  OK | 16 lotes | calidad media:",
                round(calidad, 2), "%"
            )

        except Exception as e:
            print("  ERROR:", str(e))

            guardar(
                ERRORES,
                [{
                    "fecha": fecha,
                    "error": str(e),
                }],
                ["fecha"],
            )

        if args.todas:
            time.sleep(0.5)

    if SALIDA.exists():
        df = pd.read_csv(SALIDA)

        print("\nRESUMEN")
        print("Registros:", len(df))
        print("Fechas:", df["fecha"].nunique())
        print("Lotes:", df["lote_id"].nunique())
        print(
            "Duplicados:",
            df.duplicated(
                ["fecha", "lote_id"]
            ).sum()
        )
        print("Archivo:", SALIDA)


if __name__ == "__main__":
    main()
