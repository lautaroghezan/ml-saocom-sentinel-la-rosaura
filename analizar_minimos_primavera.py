import pandas as pd
import numpy as np

ruta = "data/processed/dataset_sentinel2_intralote.csv"
df = pd.read_csv(ruta, parse_dates=["fecha"])

totales = (
    df.groupby("lote_id")[["fila", "columna"]]
      .apply(lambda x: len(x.drop_duplicates()))
      .rename("total")
)

df = df.loc[
    df["valido_scl"].eq(True)
].copy()

indices = ["NDVI", "NDRE", "NDMI"]

serie = (
    df.groupby(["lote_id", "fecha"], as_index=False)
      .agg(
          NDVI=("NDVI", "median"),
          NDRE=("NDRE", "median"),
          NDMI=("NDMI", "median"),
          n=("NDVI", "count")
      )
)

serie["total"] = serie["lote_id"].map(totales)
serie["cobertura"] = serie["n"] / serie["total"]

serie = serie.loc[serie["cobertura"] >= 0.70].copy()

primavera = serie.loc[
    serie["fecha"].between("2024-09-01", "2024-10-31")
]

crecimiento = serie.loc[
    serie["fecha"].between("2024-11-01", "2025-01-31")
]

ciclo = serie.loc[
    serie["fecha"].between("2024-08-01", "2025-03-31")
]

resultados = []

for lote in sorted(serie["lote_id"].unique()):

    p = primavera.loc[primavera["lote_id"] == lote]
    c = crecimiento.loc[crecimiento["lote_id"] == lote]
    h = ciclo.loc[ciclo["lote_id"] == lote]

    if p.empty:
        continue

    fila = {
        "lote": lote,
        "fechas_primavera": len(p)
    }

    for indice in indices:
        datos = p.dropna(subset=[indice])

        if datos.empty:
            fila[f"{indice}_min"] = np.nan
            fila[f"{indice}_fecha"] = None
            continue

        idx = datos[indice].idxmin()

        fila[f"{indice}_min"] = round(
            float(datos.loc[idx, indice]), 3
        )
        fila[f"{indice}_fecha"] = (
            datos.loc[idx, "fecha"].date()
        )

    ndvi_posterior = c["NDVI"].median()

    fila["NDVI_post"] = (
        round(float(ndvi_posterior), 3)
        if pd.notna(ndvi_posterior) else np.nan
    )

    fila["crecimiento_NDVI"] = (
        round(ndvi_posterior - fila["NDVI_min"], 3)
        if pd.notna(ndvi_posterior)
        and pd.notna(fila["NDVI_min"])
        else np.nan
    )

    if not h.empty and pd.notna(fila["NDVI_min"]):
        minimo_ciclo = h["NDVI"].min()
        fila["min_primavera_es_min_ciclo"] = (
            abs(fila["NDVI_min"] - minimo_ciclo) < 1e-6
        )
    else:
        fila["min_primavera_es_min_ciclo"] = None

    resultados.append(fila)

tabla = pd.DataFrame(resultados)

tabla = tabla.sort_values(
    "crecimiento_NDVI",
    ascending=False
)

print("\n=== MINIMOS SEPTIEMBRE-OCTUBRE 2024 ===")
print(
    tabla[
        [
            "lote",
            "fechas_primavera",
            "NDVI_min",
            "NDVI_fecha",
            "NDRE_min",
            "NDRE_fecha",
            "NDMI_min",
            "NDMI_fecha",
            "NDVI_post",
            "crecimiento_NDVI",
            "min_primavera_es_min_ciclo"
        ]
    ].to_string(index=False)
)

print("\nNDVI_post: mediana noviembre 2024-enero 2025")
print("crecimiento_NDVI: NDVI_post menos minimo primavera")
print("Los resultados describen patrones, no confirman cultivos.")
