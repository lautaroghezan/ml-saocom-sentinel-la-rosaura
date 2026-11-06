from pathlib import Path
import pandas as pd

raiz = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

inventario = pd.read_csv(
    "data/metadata/inventario_saocom.csv"
)

resultados = []

for _, fila in inventario.iterrows():

    archivo = raiz / fila["archivo"]
    existe = archivo.is_file()

    tamano_real = (
        archivo.stat().st_size
        if existe else None
    )

    resultados.append({
        "producto_id": fila["producto_id"],
        "existe": existe,
        "tamano_coincide": (
            tamano_real == int(fila["tamano_bytes"])
            if existe else False
        ),
        "nombre_coincide": (
            fila["archivo"] ==
            fila["producto_id"] + ".zip"
        )
    })

df = pd.DataFrame(resultados)

print("\n=== VERIFICACION ARCHIVOS SAOCOM ===")
print(df.to_string(index=False))

print("\n=== RESUMEN ===")
print("Archivos existentes:", df["existe"].sum(), "/ 13")
print("Tamanos correctos:", df["tamano_coincide"].sum(), "/ 13")
print("Nombres correctos:", df["nombre_coincide"].sum(), "/ 13")

correcto = df[
    ["existe", "tamano_coincide", "nombre_coincide"]
].all().all()

print("\nCONTROL GENERAL:", "APROBADO" if correcto else "REVISAR")

if not correcto:
    raise ValueError("Hay archivos faltantes o inconsistencias.")
