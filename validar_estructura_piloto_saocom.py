from pathlib import Path
import pandas as pd
import numpy as np

archivo = Path(
    "data/processed/"
    "piloto_saocom_L02_multipolarizacion_20241009.csv"
)

df = pd.read_csv(archivo)

variables = ["HH_db", "HV_db", "VH_db", "VV_db"]

claves = [
    "producto",
    "fecha",
    "lote_id",
    "fila",
    "columna"
]

print("\n=== VALIDACION ESTRUCTURAL DEL PILOTO ===")

print("Filas:", len(df))
print("Columnas:", len(df.columns))

print("\n=== COLUMNAS ===")
print(df.dtypes.to_string())

print("\n=== UNICIDAD ESPACIAL ===")

duplicados = df.duplicated(subset=claves).sum()

print("Registros duplicados:", duplicados)

print("\n=== VALORES FALTANTES ===")
print(df[variables].isna().sum().to_string())

print("\n=== VALORES FINITOS ===")

for variable in variables:
    serie = df[variable].dropna()

    print(
        variable,
        "valores finitos:",
        np.isfinite(serie).all()
    )

print("\n=== RANGOS DE COORDENADAS ===")

print(
    df[["x_utm", "y_utm"]]
    .agg(["min", "max"])
    .round(3)
    .to_string()
)

print("\n=== RESULTADO GENERAL ===")

estructura_valida = (
    duplicados == 0
    and len(df) > 0
    and all(
        pd.api.types.is_numeric_dtype(df[v])
        for v in variables
    )
)

print("Estructura valida:", estructura_valida)

if not estructura_valida:
    raise ValueError(
        "Se detectaron problemas estructurales."
    )
