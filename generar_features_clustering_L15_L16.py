from pathlib import Path
import numpy as np
import pandas as pd

ENTRADA = Path(
    "data/processed/dataset_multisensor_grilla_L15_L16.csv"
)
SALIDA = Path(
    "data/processed/features_clustering_L15_L16.csv"
)

df = pd.read_csv(ENTRADA, parse_dates=["fecha"])

OPTICAS = ["NDVI", "NDRE", "NDMI"]
RADAR = ["HH_db", "HV_db", "VH_db", "VV_db"]
VARIABLES = OPTICAS + RADAR

# Solo fechas con observaciones opticas validas.
# Se conserva el mismo subconjunto temporal para ambos modelos.
pareados = df.loc[
    df[OPTICAS].notna().all(axis=1)
    & df["cobertura_optica"].ge(0.50)
].copy()

# Resumen por celda.
agrupacion = pareados.groupby(["celda_id", "lote_id"])

features = agrupacion.size().rename(
    "n_fechas_pareadas"
).reset_index()

for variable in VARIABLES:
    resumen = agrupacion[variable].agg(
        ["median", "std", "count"]
    ).reset_index()

    resumen = resumen.rename(columns={
        "median": f"{variable}_mediana",
        "std": f"{variable}_std",
        "count": f"{variable}_n"
    })

    features = features.merge(
        resumen,
        on=["celda_id", "lote_id"],
        validate="one_to_one"
    )

# Incorporar todas las celdas, aun si alguna carece de datos.
grilla = pd.read_csv(
    "data/processed/grilla_espacial_L15_L16.csv"
)

features = grilla.merge(
    features,
    on=["celda_id", "lote_id"],
    how="left",
    validate="one_to_one"
)

features["n_fechas_pareadas"] = (
    features["n_fechas_pareadas"]
    .fillna(0)
    .astype(int)
)

columnas_modelo_optico = [
    f"{v}_{estadistico}"
    for v in OPTICAS
    for estadistico in ["mediana", "std"]
]

columnas_modelo_multi = [
    f"{v}_{estadistico}"
    for v in VARIABLES
    for estadistico in ["mediana", "std"]
]

# Criterio inicial: al menos 7 fechas pareadas.
# Se verifica tambien que todos los atributos existan.
features["apta_clustering"] = (
    features["n_fechas_pareadas"].ge(7)
    & features[columnas_modelo_multi].notna().all(axis=1)
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)
features.to_csv(SALIDA, index=False)

print("\n=== PASO 17A: INGENIERIA DE ATRIBUTOS ===")
print("Archivo:", SALIDA)
print("Celdas totales:", len(features))
print(
    "Celdas aptas para clustering:",
    int(features["apta_clustering"].sum())
)

print("\nFechas pareadas por celda:")
print(
    features["n_fechas_pareadas"]
    .describe()
    .round(2)
    .to_string()
)

print("\nCeldas aptas por lote:")
print(
    features.groupby("lote_id")["apta_clustering"]
    .agg(["sum", "count"])
    .to_string()
)

print("\nVariables del modelo optico:")
print(columnas_modelo_optico)

print("\nVariables del modelo multisensor:")
print(columnas_modelo_multi)

print("\nValores faltantes en atributos multisensor:")
print(
    features[columnas_modelo_multi]
    .isna()
    .sum()
    .to_string()
)

print("\nPrimeras cinco celdas:")
print(
    features[[
        "celda_id",
        "n_fechas_pareadas",
        "NDVI_mediana",
        "HH_db_mediana",
        "apta_clustering"
    ]]
    .head()
    .round(3)
    .to_string(index=False)
)
