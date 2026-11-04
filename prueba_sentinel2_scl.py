
import os
import requests
from pathlib import Path

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)

PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Autenticación
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

# Zona de La Rosaura, coordenadas WGS84
bbox = [-59.346686, -37.217211, -59.322628, -37.198368]

evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["SCL"],
    output: { bands: 1, sampleType: "UINT8" }
  };
}

function evaluatePixel(sample) {
  return [sample.SCL];
}
"""

payload = {
    "input": {
        "bounds": {
            "bbox": bbox,
            "properties": {
                "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
            }
        },
        "data": [{
            "type": "sentinel-2-l2a",
            "dataFilter": {
                "timeRange": {
                    "from": "2024-09-04T00:00:00Z",
                    "to": "2024-09-05T00:00:00Z"
                },
                "mosaickingOrder": "leastCC"
            }
        }]
    },
    "output": {
        "width": 110,
        "height": 105,
        "responses": [{
            "identifier": "default",
            "format": {"type": "image/tiff"}
        }]
    },
    "evalscript": evalscript
}

print("Solicitando SCL Sentinel-2...")

response = requests.post(
    PROCESS_URL,
    headers={"Authorization": f"Bearer {token}"},
    json=payload,
    timeout=120,
)

print("HTTP:", response.status_code)

if response.ok:
    output = Path("data/interim/sentinel2")
    output.mkdir(parents=True, exist_ok=True)

    archivo = output / "SCL_2024-09-04_prueba.tif"
    archivo.write_bytes(response.content)

    print("Imagen guardada:", archivo)
    print("Tamaño:", len(response.content), "bytes")
else:
    print("Error:", response.text[:1500])
