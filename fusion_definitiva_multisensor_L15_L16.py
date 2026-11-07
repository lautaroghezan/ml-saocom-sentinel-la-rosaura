from pathlib import Path
import numpy as np
import pandas as pd

RADAR = Path("data/processed/dataset_saocom_grilla_L15_L16.csv")
OPTICO = Path("data/processed/dataset_optico_grilla_L15_L16.csv")
SALIDA = Path("data/processed/dataset_multisensor_grilla_L15_L16.csv")

VENTANA_DIAS = 5
COBERTURA_MINIMA = 0.50

radar = pd.read_csv(RADAR, parse_dates=["fecha"])
optico = pd.read_csv(OPTICO, parse_dates=["fecha"])

if len(radar) != 1391 or len(optico) != 7383:
    raise ValueError("Dimensiones inesperadas en las matrices de origen.")

if radar.duplicated(["celda_id", "fecha"]).any():
    raise ValueError("Duplicados en SAOCOM.")

if optico.duplicated(["celda_id", "fecha"]).any():
    raise ValueError("Duplicados en Sentinel-2.")

columnas_opticas = [
    "celda_id", "fecha", "NDVI", "NDRE", "NDMI",
    "cobertura_optica", "pixeles_opticos_validos",
    "pixeles_opticos_totales"
]

candidatos = optico.loc[
    optico["cobertura_optica"].ge(COBERTURA_MINIMA)
    & optico[["NDVI", "NDRE", "NDMI"]].notna().all(axis=1),
    columnas_opticas
].copy()

candidatos = candidatos.rename(
    columns={"fecha": "fecha_sentinel"}
)

# merge_asof exige ordenar por la fecha de busqueda.
radar_ordenado = radar.sort_values(
    ["fecha", "celda_id"]
).reset_index(drop=True)

optico_ordenado = candidatos.sort_values(
    ["fecha_sentinel", "celda_id"]
).reset_index(drop=True)

fusion = pd.merge_asof(
    radar_ordenado,
    optico_ordenado,
    left_on="fecha",
    right_on="fecha_sentinel",
    by="celda_id",
    direction="nearest",
    tolerance=pd.Timedelta(days=VENTANA_DIAS),
    allow_exact_matches=True
)

fusion["desfase_dias"] = (
    fusion["fecha_sentinel"] - fusion["fecha"]
).dt.days

fusion["optico_disponible"] = fusion["NDVI"].notna()

fusion["sensor_disponible"] = np.where(
    fusion["optico_disponible"],
    "SAOCOM+Sentinel2",
    "Solo_SAOCOM"
)

fusion = fusion.sort_values(
    ["lote_id", "celda_id", "fecha"]
).reset_index(drop=True)

if len(fusion) != 1391:
    raise ValueError("La fusion modifico el numero de registros radar.")

if fusion.duplicated(["celda_id", "fecha"]).any():
    raise ValueError("La fusion genero duplicados.")

if fusion["desfase_dias"].dropna().abs().gt(VENTANA_DIAS).any():
    raise ValueError("Hay desfases superiores a la ventana permitida.")

SALIDA.parent.mkdir(parents=True, exist_ok=True)
fusion.to_csv(SALIDA, index=False, date_format="%Y-%m-%d")

print("\n=== PASO 16I: FUSION MULTISENSOR ===")
print("Archivo:", SALIDA)
print("Registros:", len(fusion))
print("Celdas:", fusion["celda_id"].nunique())
print("Fechas SAOCOM:", fusion["fecha"].nunique())

print("\nDisponibilidad de sensores:")
print(fusion["sensor_disponible"].value_counts().to_string())

print("\nCobertura multisensor por lote:")
resumen = fusion.groupby("lote_id").agg(
    registros=("celda_id", "size"),
    con_optico=("optico_disponible", "sum"),
    cobertura_optica_media=("cobertura_optica", "mean"),
    ndvi_mediano=("NDVI", "median"),
    hh_mediano=("HH_db", "median")
)
resumen["pct_con_optico"] = (
    100 * resumen["con_optico"] / resumen["registros"]
)
print(resumen.round(3).to_string())

print("\nDesfase temporal absoluto, en dias:")
print(
    fusion["desfase_dias"]
    .abs()
    .dropna()
    .describe()
    .round(2)
    .to_string()
)

print("\nCobertura por fecha SAOCOM:")
por_fecha = fusion.groupby("fecha").agg(
    celdas=("celda_id", "size"),
    con_optico=("optico_disponible", "sum")
)
por_fecha["porcentaje"] = (
    100 * por_fecha["con_optico"] / por_fecha["celdas"]
)
print(por_fecha.round(1).to_string())

print("\nFechas Sentinel-2 reutilizadas:")
usos = fusion.loc[fusion["optico_disponible"]].groupby(
    ["celda_id", "fecha_sentinel"]
).size()
print("Pares celda-fecha optica usados mas de una vez:",
      int((usos > 1).sum()))

print("\nMatriz lista para ingenieria de atributos.")
print("Las filas celda-fecha no son muestras independientes.")
