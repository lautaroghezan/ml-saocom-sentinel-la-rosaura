from pathlib import Path
from collections import Counter
import rasterio

carpeta = Path("data/interim/sentinel2/reflectancias")
archivos = sorted(carpeta.glob("*.tif"))

print("\n=== CONSISTENCIA ESPACIAL SENTINEL-2 ===")
print("Archivos encontrados:", len(archivos))

if len(archivos) != 69:
    raise ValueError("Cantidad de archivos inesperada")

registros = []

for archivo in archivos:
    with rasterio.open(archivo) as src:
        registros.append({
            "archivo": archivo.name,
            "crs": str(src.crs),
            "res": tuple(src.res),
            "dimensiones": (src.width, src.height),
            "bandas": src.count,
            "transform": tuple(src.transform)[:6],
            "bounds": tuple(src.bounds)
        })

for campo in [
    "crs", "res", "dimensiones",
    "bandas", "transform", "bounds"
]:
    valores = Counter(
        str(r[campo]) for r in registros
    )

    print(f"\n{campo}:")
    print("Configuraciones distintas:", len(valores))

    for valor, cantidad in valores.most_common(5):
        print(" ", cantidad, "archivos:", valor)

referencia = registros[0]

diferentes = [
    r["archivo"]
    for r in registros
    if any(
        r[campo] != referencia[campo]
        for campo in [
            "crs", "res", "dimensiones",
            "bandas", "transform"
        ]
    )
]

print("\n=== RESULTADO ===")
print("Archivos con grilla diferente:", len(diferentes))

if diferentes:
    print("Primeros archivos diferentes:")
    for nombre in diferentes[:10]:
        print(" ", nombre)
else:
    print("Las 69 imagenes comparten la misma grilla.")

print("\nInspeccion finalizada.")
