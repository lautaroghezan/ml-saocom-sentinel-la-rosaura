
import os
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.mask import mask

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)
PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

BASE = Path("data")
CATALOGO = BASE / "processed/catalogo_sentinel2_analitico_2024_25.csv"
GEOJSON = BASE / "raw/vectores/potreros_la_rosaura.geojson"
CARPETA_TIFF = BASE / "interim/sentinel2"
SALIDA = BASE / "processed/control_scl_sentinel2_2024_25.csv"
ERRORES = BASE / "processed/errores_scl_sentinel2.csv"

CARPETA_TIFF.mkdir(parents=True, exist_ok=True)
SALIDA.parent.mkdir(parents=True, exist_ok=True)

RES = 20
CRS = "EPSG:32721"

EVALSCRIPT = """
//VERSION=3
function setup() {
    return {
        input: ["SCL", "dataMask"],
        output: {
            bands: 2,
            sampleType: "UINT8"
        }
    };
}
function evaluatePixel(s) {
    return [s.SCL, s.dataMask];
}
"""

catalogo = pd.read_csv(CATALOGO)
catalogo = catalogo.sort_values("fecha")

lotes = gpd.read_file(GEOJSON).to_crs(CRS)

assert len(lotes) == 16
assert lotes["lote_id"].nunique() == 16
assert catalogo["fecha"].nunique() == 69

xmin, ymin, xmax, ymax = lotes.total_bounds

xmin = np.floor((xmin - 40) / RES) * RES
ymin = np.floor((ymin - 40) / RES) * RES
xmax = np.ceil((xmax + 40) / RES) * RES
ymax = np.ceil((ymax + 40) / RES) * RES

ancho = int(round((xmax - xmin) / RES))
alto = int(round((ymax - ymin) / RES))

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


def descargar_scl(fecha, token):
    archivo = CARPETA_TIFF / f"SCL_{fecha}_20m.tif"

    # Reutilizar solamente TIFF compatibles
    if archivo.exists():
        try:
            with rasterio.open(archivo) as src:
                if (
                    src.count == 2
                    and src.width == ancho
                    and src.height == alto
                    and src.crs.to_string() == CRS
                    and np.allclose(src.res, (RES, RES))
                    and np.allclose(
                        src.bounds,
                        (xmin, ymin, xmax, ymax),
                        atol=0.01,
                    )
                ):
                    print("  TIFF reutilizado")
                    return archivo, token
        except Exception:
            pass

    inicio = fecha + "T00:00:00Z"
    fin = (
        pd.Timestamp(fecha) + pd.Timedelta(days=1)
    ).strftime("%Y-%m-%dT00:00:00Z")

    payload = {
        "input": {
            "bounds": {
                "bbox": [xmin, ymin, xmax, ymax],
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/EPSG/0/32721"
                },
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": inicio,
                        "to": fin,
                    },
                    "mosaickingOrder": "leastCC",
                },
            }],
        },
        "output": {
            "width": ancho,
            "height": alto,
            "responses": [{
                "identifier": "default",
                "format": {"type": "image/tiff"},
            }],
        },
        "evalscript": EVALSCRIPT,
    }

    for intento in range(1, 4):
        r = requests.post(
            PROCESS_URL,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=120,
        )

        if r.status_code == 401:
            token = obtener_token()
            continue

        if r.ok:
            temporal = archivo.with_suffix(".tmp.tif")
            temporal.write_bytes(r.content)

            try:
                with rasterio.open(temporal) as src:
                    assert src.count == 2
                    assert src.width == ancho
                    assert src.height == alto
                    assert src.crs.to_string() == CRS
                    assert np.allclose(src.res, (RES, RES))
                    assert np.allclose(
                        src.bounds,
                        (xmin, ymin, xmax, ymax),
                        atol=0.01,
                    )
                temporal.replace(archivo)
                return archivo, token
            finally:
                if temporal.exists():
                    temporal.unlink()

        if r.status_code in (429, 500, 502, 503, 504):
            print(f"  HTTP {r.status_code}, reintento {intento}")
            time.sleep(3 * intento)
            continue

        raise RuntimeError(
            f"HTTP {r.status_code}: {r.text[:300]}"
        )

    raise RuntimeError("No se pudo descargar la imagen")


def procesar_lotes(archivo, fecha, producto):
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

            scl = recorte[0].data
            cobertura = recorte[1].data

            dentro = ~np.ma.getmaskarray(recorte[0])
            total = int(dentro.sum())

            if total == 0:
                raise ValueError(
                    f"Sin píxeles: {fecha} {lote['lote_id']}"
                )

            con_datos = dentro & (cobertura == 1)
            valores = scl[con_datos]

            conteos = {
                f"n_scl_{i}": int((valores == i).sum())
                for i in range(12)
            }

            n_validos = int(
                np.isin(valores, [4, 5, 6]).sum()
            )
            n_nubes = int(
                np.isin(valores, [8, 9, 10]).sum()
            )
            n_sombras = int(
                np.isin(valores, [2, 3]).sum()
            )
            n_inciertos = int((valores == 7).sum())

            filas.append({
                "fecha": fecha,
                "lote_id": lote["lote_id"],
                "producto_catalogado": producto,
                "producto_api_verificado": False,
                "seleccion_api": "leastCC_por_dia",
                "n_pixeles": total,
                "n_con_datos": int(con_datos.sum()),
                "n_validos": n_validos,
                "pct_cobertura": round(
                    100 * con_datos.sum() / total, 2
                ),
                "pct_validos": round(
                    100 * n_validos / total, 2
                ),
                "pct_nubes": round(
                    100 * n_nubes / total, 2
                ),
                "pct_sombras": round(
                    100 * n_sombras / total, 2
                ),
                "pct_inciertos": round(
                    100 * n_inciertos / total, 2
                ),
                **conteos,
            })

    return filas


# Recuperar resultados anteriores
if SALIDA.exists():
    anteriores = pd.read_csv(SALIDA)
    if "producto_api_verificado" not in anteriores.columns:
        raise RuntimeError(
            "El CSV existente no tiene el esquema actual. "
            "Revisarlo antes de continuar."
        )
    resultados = anteriores.to_dict("records")
else:
    resultados = []

fechas_completas = set()
if resultados:
    previos = pd.DataFrame(resultados)
    conteos = previos.groupby("fecha")["lote_id"].nunique()
    fechas_completas = set(conteos[conteos == 16].index)

errores = []

print("Fechas catalogadas:", len(catalogo))
print("Fechas ya completas:", len(fechas_completas))
print("Grilla:", ancho, "x", alto, "píxeles")

token = obtener_token()

for _, escena in catalogo.iterrows():
    fecha = escena["fecha"]
    producto = escena["product_id"]

    if fecha in fechas_completas:
        print(fecha, "YA PROCESADA")
        continue

    print("\nProcesando", fecha)

    try:
        archivo, token = descargar_scl(fecha, token)
        filas = procesar_lotes(archivo, fecha, producto)

        if len(filas) != 16:
            raise ValueError(
                f"Se obtuvieron {len(filas)} lotes, no 16"
            )

        # Reemplazar registros parciales de esa fecha
        resultados = [
            x for x in resultados if x["fecha"] != fecha
        ]
        resultados.extend(filas)

        pd.DataFrame(resultados).sort_values(
            ["fecha", "lote_id"]
        ).to_csv(SALIDA, index=False)

        print(
            "  OK: 16 lotes |",
            "validos:",
            round(
                np.mean([x["pct_validos"] for x in filas]), 2
            ),
            "%",
        )

    except Exception as e:
        print("  ERROR:", str(e))
        errores.append({
            "fecha": fecha,
            "error": str(e),
        })
        pd.DataFrame(errores).to_csv(
            ERRORES, index=False
        )

    time.sleep(0.5)

if resultados:
    df = pd.DataFrame(resultados)

    print("\nRESUMEN FINAL")
    print("Registros:", len(df))
    print("Fechas:", df["fecha"].nunique())
    print("Lotes:", df["lote_id"].nunique())

    print("\nCalidad por fecha:")
    print(
        df.groupby("fecha")[
            ["pct_validos", "pct_nubes", "pct_sombras"]
        ].mean().round(2).to_string()
    )

    print("\nArchivo:", SALIDA)

print("\nFechas con error:", len(errores))
