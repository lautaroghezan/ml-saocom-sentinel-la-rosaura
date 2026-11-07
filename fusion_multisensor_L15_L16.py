from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

RADAR = Path("data/processed/dataset_saocom_intralote.csv")
OPTICO = Path("data/processed/dataset_sentinel2_intralote.csv")
SALIDA = Path("data/processed/dataset_multisensor_L15_L16.csv")

LOTES = ["L15", "L16"]
TOLERANCIA_DIAS = 5
RADIO_METROS = 31.2  # Semidiagonal aproximada de 44 x 44 m

radar = pd.read_csv(RADAR, parse_dates=["fecha"])
optico = pd.read_csv(OPTICO, parse_dates=["fecha"])

radar = radar.loc[radar["lote_id"].isin(LOTES)].copy()
optico = optico.loc[
    optico["lote_id"].isin(LOTES)
    & optico["valido_scl"].eq(True)
].copy()

variables = ["NDVI", "NDRE", "NDMI"]

resultados = []

for lote in LOTES:
    r_lote = radar.loc[radar["lote_id"] == lote]
    o_lote = optico.loc[optico["lote_id"] == lote]

    for fecha_radar, r_fecha in r_lote.groupby("fecha"):

        disponibles = o_lote.loc[
            (o_lote["fecha"] - fecha_radar)
            .abs()
            .dt.days <= TOLERANCIA_DIAS
        ]

        if disponibles.empty:
            bloque = r_fecha.copy()
            for variable in variables:
                bloque[variable] = np.nan
            bloque["n_pixeles_opticos"] = 0
            bloque["desfase_dias"] = np.nan
            bloque["fecha_sentinel"] = pd.NaT
            resultados.append(bloque)
            continue

        fechas = (
            disponibles["fecha"]
            .drop_duplicates()
            .sort_values()
        )

        fecha_optica = min(
            fechas,
            key=lambda f: (
                abs((f - fecha_radar).days),
                f
            )
        )

        o_fecha = disponibles.loc[
            disponibles["fecha"] == fecha_optica
        ].copy()

        coords_o = o_fecha[["x_utm", "y_utm"]].to_numpy()
        arbol = cKDTree(coords_o)

        bloque = r_fecha.copy()
        coords_r = bloque[["x_utm", "y_utm"]].to_numpy()

        vecinos = arbol.query_ball_point(
            coords_r,
            r=RADIO_METROS
        )

        for variable in variables:
            valores = o_fecha[variable].to_numpy(dtype=float)
            medianas = []

            for indices in vecinos:
                if len(indices) == 0:
                    medianas.append(np.nan)
                else:
                    v = valores[indices]
                    v = v[np.isfinite(v)]
                    medianas.append(
                        float(np.median(v))
                        if len(v) else np.nan
                    )

            bloque[variable] = medianas

        bloque["n_pixeles_opticos"] = [
            len(indices) for indices in vecinos
        ]

        bloque["fecha_sentinel"] = fecha_optica
        bloque["desfase_dias"] = (
            fecha_optica - fecha_radar
        ).days

        resultados.append(bloque)

fusion = pd.concat(resultados, ignore_index=True)

fusion["fecha_sentinel"] = pd.to_datetime(
    fusion["fecha_sentinel"]
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)
fusion.to_csv(SALIDA, index=False)

print("\n=== PASO 16A: FUSION MULTISENSOR ===")
print("Archivo:", SALIDA)
print("Filas integradas:", len(fusion))
print("Lotes:", sorted(fusion["lote_id"].unique()))
print("Fechas SAOCOM:", fusion["fecha"].nunique())

print("\nCobertura de integracion:")
print(
    fusion.groupby("lote_id")
    .agg(
        celdas=("NDVI", "size"),
        con_ndvi=("NDVI", "count"),
        ndvi_mediano=("NDVI", "median"),
        desfase_mediano=("desfase_dias", "median")
    )
    .to_string()
)

print("\nCobertura por fecha y lote:")
print(
    fusion.groupby(["fecha", "lote_id"])
    .agg(
        celdas=("NDVI", "size"),
        con_ndvi=("NDVI", "count"),
        pixeles_opticos_mediana=(
            "n_pixeles_opticos", "median"
        )
    )
    .to_string()
)

print("\nAdvertencia metodologica:")
print("Asociacion espacial aproximada mediante radio de 31.2 m.")
print("No equivale a una interseccion exacta de huellas.")
print("Las celdas radar pueden cambiar de posicion entre fechas.")
