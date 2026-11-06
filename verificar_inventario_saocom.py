from pathlib import Path
import pandas as pd

archivo = Path("data/metadata/inventario_saocom.csv")

if not archivo.exists():
    raise FileNotFoundError(
        f"No se encontro el inventario: {archivo}"
    )

df = pd.read_csv(archivo)

print("\n=== INVENTARIO SAOCOM ===")
print("Productos registrados:", len(df))

print("\n=== COLUMNAS DISPONIBLES ===")
print(df.columns.tolist())

print("\n=== PRIMEROS REGISTROS ===")
print(df.head(5).to_string(index=False))

print("\n=== VALORES FALTANTES POR COLUMNA ===")
print(df.isna().sum().to_string())

print("\n=== ARCHIVOS DUPLICADOS ===")

columnas_archivo = [
    c for c in df.columns
    if any(
        termino in c.lower()
        for termino in ["archivo", "nombre", "filename"]
    )
]

for columna in columnas_archivo:
    print(
        columna,
        "duplicados:",
        df[columna].duplicated().sum()
    )

print("\n=== CONTROL DE CANTIDAD ===")
print("Se esperaban 13 productos.")
print("Cantidad correcta:", len(df) == 13)
