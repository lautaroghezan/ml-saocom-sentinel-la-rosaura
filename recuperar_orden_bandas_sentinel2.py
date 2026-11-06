from pathlib import Path

base = Path.cwd()

terminos = [
    "src.read(",
    "dataset.read(",
    "raster.read(",
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B8A",
    "B11",
    "B12",
    "SCL",
    "band_order",
    "band_names"
]

print("\n=== BUSQUEDA DEL ORDEN DE BANDAS SENTINEL-2 ===")

archivos = sorted(base.glob("*.py"))

coincidencias = 0

for archivo in archivos:

    nombre = archivo.name.lower()

    if not any(
        palabra in nombre
        for palabra in [
            "sentinel",
            "reflectancia",
            "scl",
            "indice"
        ]
    ):
        continue

    lineas = archivo.read_text(
        encoding="utf-8-sig",
        errors="replace"
    ).splitlines()

    hallazgos = []

    for numero, linea in enumerate(lineas, 1):

        if any(
            termino.lower() in linea.lower()
            for termino in terminos
        ):
            hallazgos.append(
                (numero, linea.strip()[:160])
            )

    if hallazgos:

        print("\nARCHIVO:", archivo.name)

        for numero, linea in hallazgos[:35]:
            print(f"  Linea {numero}: {linea}")

        coincidencias += len(hallazgos)

print("\nCoincidencias encontradas:", coincidencias)
print("Inspeccion finalizada.")
