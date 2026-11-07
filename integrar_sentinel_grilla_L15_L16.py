from pathlib import Path
import numpy as np
import pandas as pd

GRILLA = Path("data/processed/grilla_espacial_L15_L16.csv")
META = Path("data/metadata/grilla_comun_saocom_L15_L16.csv")
OPTICO = Path("data/processed/dataset_sentinel2_intralote.csv")
SALIDA = Path("data/processed/dataset_optico_grilla_L15_L16.csv")

grilla = pd.read_csv(GRILLA)
meta = pd.read_csv(META)
df = pd.read_csv(OPTICO, parse_dates=["fecha"])

lotes = ["L15", "L16"]
indices = ["NDVI", "NDRE", "NDMI"]

df = df.loc[df["lote_id"].isin(lotes)].copy()

if len(grilla) != 107 or grilla["celda_id"].duplicated().any():
    raise ValueError("La grilla de referencia no tiene 107 celdas unicas.")

# Asignar cada centro Sentinel-2 a una celda fija de 44 m.
partes = []

for _, m in meta.iterrows():
    lote = m["lote_id"]
    d = df.loc[df["lote_id"] == lote].copy()

    resolucion = float(m["resolucion_m"])
    origen_x = float(m["origen_x"])
    origen_y = float(m["origen_y"])

    d["fila_grilla"] = np.floor(
        (origen_y - d["y_utm"]) / resolucion
    ).astype(int)

    d["columna_grilla"] = np.floor(
        (d["x_utm"] - origen_x) / resolucion
    ).astype(int)

    d = d.merge(
        grilla[[
            "celda_id", "lote_id",
            "fila_grilla", "columna_grilla"
        ]],
        on=["lote_id", "fila_grilla", "columna_grilla"],
        how="inner",
        validate="many_to_one"
    )

    partes.append(d)

asignados = pd.concat(partes, ignore_index=True)

# Comprobar que cada pixel optico aparece una sola vez por fecha.
clave = ["fecha", "lote_id", "fila", "columna"]

if asignados.duplicated(clave).any():
    raise ValueError("Hay pixeles opticos asignados mas de una vez.")

# Denominador fijo por celda: centros opticos disponibles
# en la geometria, independientemente de las nubes.
universo = (
    asignados[["celda_id", "lote_id", "fila", "columna"]]
    .drop_duplicates()
    .groupby("celda_id")
    .size()
    .rename("pixeles_opticos_totales")
    .reset_index()
)

# Exigir calidad SCL y los tres indices finitos.
valido = asignados["valido_scl"].eq(True)

for indice in indices:
    valido &= np.isfinite(asignados[indice])

asignados["optico_valido"] = valido

observaciones = (
    asignados.loc[asignados["optico_valido"]]
    .groupby(["celda_id", "fecha"], as_index=False)
    .agg(
        NDVI=("NDVI", "median"),
        NDRE=("NDRE", "median"),
        NDMI=("NDMI", "median"),
        pixeles_opticos_validos=("NDVI", "size")
    )
)

# Construir todas las combinaciones de las 107 celdas
# y las 69 fechas Sentinel-2, incluso sin datos validos.
fechas = pd.DataFrame({
    "fecha": sorted(df["fecha"].dropna().unique())
})

base = grilla.merge(fechas, how="cross")

base = base.merge(
    universo,
    on="celda_id",
    how="left",
    validate="many_to_one"
)

base = base.merge(
    observaciones,
    on=["celda_id", "fecha"],
    how="left",
    validate="one_to_one"
)

base["pixeles_opticos_totales"] = (
    base["pixeles_opticos_totales"]
    .fillna(0)
    .astype(int)
)

base["pixeles_opticos_validos"] = (
    base["pixeles_opticos_validos"]
    .fillna(0)
    .astype(int)
)

base["cobertura_optica"] = np.where(
    base["pixeles_opticos_totales"] > 0,
    base["pixeles_opticos_validos"]
    / base["pixeles_opticos_totales"],
    np.nan
)

base["optico_disponible"] = (
    base["pixeles_opticos_validos"] > 0
)

base = base.sort_values(
    ["lote_id", "celda_id", "fecha"]
).reset_index(drop=True)

esperado = len(grilla) * len(fechas)

if len(base) != esperado:
    raise ValueError("Cantidad inesperada de filas.")

if base.duplicated(["celda_id", "fecha"]).any():
    raise ValueError("Duplicados de celda y fecha.")

SALIDA.parent.mkdir(parents=True, exist_ok=True)
base.to_csv(SALIDA, index=False, date_format="%Y-%m-%d")

print("\n=== PASO 16F COMPLETADO ===")
print("Archivo:", SALIDA)
print("Celdas espaciales:", base["celda_id"].nunique())
print("Fechas Sentinel-2:", base["fecha"].nunique())
print("Filas celda-fecha:", len(base))
print("Filas esperadas:", esperado)

print("\nCobertura por lote:")
print(
    base.groupby("lote_id")
    .agg(
        filas=("celda_id", "size"),
        con_optico=("optico_disponible", "sum"),
        cobertura_media=("cobertura_optica", "mean"),
        ndvi_mediano=("NDVI", "median")
    )
    .round(3)
    .to_string()
)

print("\nPixeles opticos por celda:")
print(
    universo["pixeles_opticos_totales"]
    .describe()
    .round(2)
    .to_string()
)

print("\nCeldas sin centros opticos asociados:",
      len(grilla) - len(universo))

print("\nFechas con cobertura optica >= 70 %:")
print(
    base.groupby("fecha")["cobertura_optica"]
    .mean()
    .ge(0.70)
    .sum()
)

print("\nNOTA: la cobertura es por centros opticos")
print("asignados geometricamente a cada celda.")
print("No equivale a cobertura areal exacta.")
