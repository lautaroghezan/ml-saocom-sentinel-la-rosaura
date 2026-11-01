import requests
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------
# La Rosaura - Catálogo Sentinel-2 L2A
# Campaña 2024/25
# ---------------------------------------------------------

STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"

BBOX = [
    -59.346686,   # lon oeste
    -37.217211,   # lat sur
    -59.322628,   # lon este
    -37.198368    # lat norte
]

FECHA_INICIO = "2024-08-01T00:00:00Z"
FECHA_FIN = "2025-06-30T23:59:59Z"

payload = {
    "collections": ["sentinel-2-l2a"],
    "bbox": BBOX,
    "datetime": f"{FECHA_INICIO}/{FECHA_FIN}",
    "limit": 100
}

print("Consultando catálogo Sentinel-2 L2A...")

r = requests.post(STAC_URL, json=payload, timeout=60)
r.raise_for_status()

features = r.json()["features"]

print(f"Productos encontrados: {len(features)}")

registros = []

for item in features:
    props = item.get("properties", {})
    assets = item.get("assets", {})

    fecha_hora = props.get("datetime")

    registros.append({
        "product_id": item.get("id"),
        "fecha_hora": fecha_hora,
        "fecha": fecha_hora[:10] if fecha_hora else None,
        "cloud_cover_global": props.get("eo:cloud_cover"),
        "collection": item.get("collection"),
        "B02": assets.get("B02", {}).get("href"),
        "B03": assets.get("B03", {}).get("href"),
        "B04": assets.get("B04", {}).get("href"),
        "B05": assets.get("B05", {}).get("href"),
        "B06": assets.get("B06", {}).get("href"),
        "B07": assets.get("B07", {}).get("href"),
        "B08": assets.get("B08", {}).get("href"),
        "B8A": assets.get("B8A", {}).get("href"),
        "B11": assets.get("B11", {}).get("href"),
        "B12": assets.get("B12", {}).get("href"),
        "SCL_20m": assets.get("SCL_20m", {}).get("href"),
    })

df = pd.DataFrame(registros)

if not df.empty:
    df = df.sort_values(["fecha", "cloud_cover_global"]).reset_index(drop=True)

print()
print("Fechas únicas:", df["fecha"].nunique())

if not df.empty:
    print("Primera fecha:", df["fecha"].min())
    print("Última fecha:", df["fecha"].max())

print()
print("Productos por fecha:")
print(df.groupby("fecha").size().value_counts().sort_index())

salida = Path("data/processed/catalogo_sentinel2_2024_25.csv")
salida.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(salida, index=False)

print()
print("Catálogo guardado en:")
print(salida.resolve())

print()
print("Primeras observaciones:")
print(
    df[
        ["fecha", "product_id", "cloud_cover_global"]
    ].head(10).to_string(index=False)
)