
import os
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_bounds
from rasterio.transform import from_bounds
import requests

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)
PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

FECHAS = ["2024-09-04", "2024-09-09", "2024-09-14"]
CRS = "EPSG:32721"
RESOLUCION = 20

SALIDA = Path("data/interim/sentinel2")
SALIDA.mkdir(parents=True, exist_ok=True)

CATALOGO = Path("data/processed/catalogo_sentinel2_2024_25.csv")
LOTES = Path("data/raw/vectores/potreros_la_rosaura.geojson")

catalogo = pd.read_csv(CATALOGO)
lotes = gpd.read_file(LOTES).to_crs(CRS)

# Extensión de los lotes en metros, con margen de 40 m
xmin, ymin, xmax, ymax = lotes.total_bounds
xmin -= 40
ymin -= 40
xmax += 40
ymax += 40

# Grilla de 20 m
xmin = np.floor(xmin / RESOLUCION) * RESOLUCION
ymin = np.floor(ymin / RESOLUCION) * RESOLUCION
xmax = np.ceil(xmax / RESOLUCION) * RESOLUCION
ymax = np.ceil(ymax / RESOLUCION) * RESOLUCION

ancho = int(round((xmax - xmin) / RESOLUCION))
alto = int(round((ymax - ymin) / RESOLUCION))

evalscript = """
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

# Obtener token OAuth
respuesta = requests.post(
    TOKEN_URL,
    data={
        "grant_type": "client_credentials",
        "client_id": os.environ["CDSE_CLIENT_ID"],
        "client_secret": os.environ["CDSE_CLIENT_SECRET"]
    },
    timeout=30
)
respuesta.raise_for_status()
token = respuesta.json()["access_token"]

resultados = []

for fecha in FECHAS:
    print(f"\nProcesando {fecha}...")

    escena = catalogo[catalogo["fecha"] == fecha]

    if len(escena) != 1:
        print("Fecha sin producto único en catálogo. Se omite.")
        continue

    producto = escena.iloc[0]["product_id"]

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
                }
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": inicio,
                        "to": fin
                    },
                    "mosaickingOrder": "leastCC"
                }
            }]
        },
        "output": {
            "width": ancho,
            "height": alto,
            "responses": [{
                "identifier": "default",
                "format": {"type": "image/tiff"}
            }]
        },
        "evalscript": evalscript
    }

    r = requests.post(
        PROCESS_URL,
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=120
    )

    print("HTTP:", r.status_code)

    if not r.ok:
        print("Error:", r.text[:500])
        continue

    archivo = SALIDA / f"SCL_{fecha}_20m.tif"
    archivo.write_bytes(r.content)

    with rasterio.open(archivo) as src:
        print("CRS:", src.crs)
        print("Dimensiones:", src.width, src.height)

        for _, lote in lotes.iterrows():
            recorte, _ = mask(
                src,
                [lote.geometry],
                crop=True,
                filled=False,
                all_touched=False
            )

            scl = recorte[0]
            cobertura = recorte[1]

            dentro = ~np.ma.getmaskarray(scl)
            datos = dentro & (cobertura.data == 1)
            total = int(dentro.sum())
            validos_cobertura = int(datos.sum())

            if total == 0:
                continue

            valores = scl.data[datos]

            # Clases utilizables para análisis de vegetación
            utiles = np.isin(valores, [4, 5, 6])

            # Nubes y sombras
            nubes = np.isin(valores, [8, 9, 10])
            sombras = valores == 3
            inciertos = valores == 7

            resultados.append({
                "fecha": fecha,
                "lote_id": lote["lote_id"],
                "producto_catalogado": producto,
                "n_pixeles": total,
                "n_con_datos": validos_cobertura,
                "pct_cobertura": round(
                    100 * validos_cobertura / total, 2
                ),
                "pct_validos": round(
                    100 * utiles.sum() / total, 2
                ),
                "pct_nubes": round(
                    100 * nubes.sum() / total, 2
                ),
                "pct_sombras": round(
                    100 * sombras.sum() / total, 2
                ),
                "pct_inciertos": round(
                    100 * inciertos.sum() / total, 2
                )
            })

df = pd.DataFrame(resultados)

if not df.empty:
    destino = Path(
        "data/processed/control_scl_sentinel2_piloto.csv"
    )
    df.to_csv(destino, index=False)

    print("\nRESUMEN POR FECHA")
    print(
        df.groupby("fecha")[
            ["pct_cobertura", "pct_validos",
             "pct_nubes", "pct_sombras", "pct_inciertos"]
        ].mean().round(2).to_string()
    )

    print("\nRegistros:", len(df))
    print("Archivo:", destino)
else:
    print("No se generaron registros.")
