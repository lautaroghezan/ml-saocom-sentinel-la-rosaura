from pathlib import Path

archivo = Path("construir_dataset_sentinel2.py")

lineas = archivo.read_text(
    encoding="utf-8-sig"
).splitlines()

rangos = [
    (35, 130),
    (370, 445)
]

for inicio, fin in rangos:

    print("\n" + "=" * 65)
    print(f"LINEAS {inicio} A {fin}")
    print("=" * 65)

    for numero in range(inicio, min(fin, len(lineas)) + 1):
        print(f"{numero:4d}: {lineas[numero - 1]}")
