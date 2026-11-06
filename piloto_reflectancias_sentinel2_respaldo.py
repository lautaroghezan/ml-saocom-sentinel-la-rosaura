
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import requests

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)
PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

FECHA = "2024-09-04"
RES = 20
CRS = "EPSG:32721"

SALIDA = Path("data/interim/sentinel2")
SALIDA.mkdir(parents=True, exist_ok=True)

LOTES = Path("data/raw/vectores/potreros_la_rosaura.geojson")
lotes = gpd.read_file(LOTES).to_crs(CRS)

xmin, ymin, xmax, ymax = lotes.total_bounds
xmin = np.floor((xmin - 40) / RES) * RES
ymin = np.floor((ymin - 40) / RES) * RES
xmax = np.ceil((xmax + 40) / RES) * RES
ymax = np.ceil((ymax + 40) / RES) * RES

ancho = int(round((xmax - xmin) / RES))
alto = int(round((ymax - ymin) / RES))

evalscript = """
//VERSION=3
function setup() {
    return {
        input: [{
    bands: [
        "B04", "B05", "B08", "B8A", "B11",
        "SCL", "dataMask"
    ],
    units: [
        "REFLECTANCE",
        "REFLECTANCE",
        "REFLECTANCE",
        "REFLECTANCE",
        "REFLECTANCE",
        "DN",
        "DN"
    ]
}],
        output: {
            bands: 9,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(s) {
    var valid = s.dataMask === 1 &&
        [4, 5, 6].includes(s.SCL);

    var ndvi = valid && (s.B08 + s.B04) !== 0
        ? (s.B08 - s.B04) / (s.B08 + s.B04)
        : -9999;

    var ndre = valid && (s.B8A + s.B05) !== 0
        ? (s.B8A - s.B05) / (s.B8A + s.B05)
        : -9999;

    var ndmi = valid && (s.B08 + s.B11) !== 0
        ? (s.B08 - s.B11) / (s.B08 + s.B11)
        : -9999;

    return [
        s.B04, s.B05, s.B08, s.B8A, s.B11,
        s.SCL, ndvi, ndre, ndmi
    ];
}
"""

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
token = r.json()["access_token"]

inicio = FECHA + "T00:00:00Z"
fin = "2024-09-05T00:00:00Z"

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
    "evalscript": evalscript,
}

print("Solicitando reflectancias Sentinel-2...")

respuesta = requests.post(
    PROCESS_URL,
    headers={"Authorization": f"Bearer {token}"},
    json=payload,
    timeout=120,
)

print("HTTP:", respuesta.status_code)

if not respuesta.ok:
    print("DETALLE DEL ERROR DE COPERNICUS:")
    print(respuesta.text[:3000])

respuesta.raise_for_status()

archivo = SALIDA / f"reflectancias_indices_{FECHA}_20m.tif"
archivo.write_bytes(respuesta.content)

with rasterio.open(archivo) as src:
    print("Bandas:", src.count)
    print("CRS:", src.crs)
    print("Resolucion:", src.res)
    print("Dimensiones:", src.width, src.height)

    nombres = [
        "B04", "B05", "B08", "B8A", "B11",
        "SCL", "NDVI", "NDRE", "NDMI"
    ]

    for i, nombre in enumerate(nombres, start=1):
        datos = src.read(i)
        if nombre in ["NDVI", "NDRE", "NDMI"]:
            datos = datos[
                np.isfinite(datos) & (datos != -9999)
            ]
        else:
            datos = datos[np.isfinite(datos)]

        if len(datos):
            print(
                nombre,
                "min:", round(float(datos.min()), 4),
                "mediana:", round(float(np.median(datos)), 4),
                "max:", round(float(datos.max()), 4),
            )

print("Archivo guardado:", archivo)
