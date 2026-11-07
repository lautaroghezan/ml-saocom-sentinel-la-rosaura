from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import spearmanr
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    adjusted_rand_score,
    silhouette_score,
    r2_score
)
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline

BASE = Path("data/processed")
TABLAS = Path("reports/tables")
FIGURAS = Path("reports/figures")

TABLAS.mkdir(parents=True, exist_ok=True)
FIGURAS.mkdir(parents=True, exist_ok=True)

fusion = pd.read_csv(
    BASE / "dataset_multisensor_grilla_L15_L16.csv",
    parse_dates=["fecha"]
)

features = pd.read_csv(
    BASE / "features_clustering_L15_L16.csv"
)

clusters = pd.read_csv(
    BASE / "clusters_intralote_L15_L16.csv"
)

OPTICAS = ["NDVI", "NDRE", "NDMI"]
RADAR = ["HH_db", "HV_db", "VH_db", "VV_db"]

# Analisis temporal: solo observaciones realmente emparejadas.
pares = fusion.loc[
    fusion[OPTICAS].notna().all(axis=1)
    & fusion["cobertura_optica"].ge(0.50)
].copy()

pares["fecha"] = pd.to_datetime(pares["fecha"])

print("\n=== PASO 17E: COMPLEMENTARIEDAD MULTISENSOR ===")
print("Observaciones emparejadas:", len(pares))
print("Celdas:", pares["celda_id"].nunique())
print("Fechas:", pares["fecha"].nunique())

# ----------------------------------------------------
# A. CORRELACIONES ENTRE SENSORES
# ----------------------------------------------------

correlaciones = []

for lote, sub in pares.groupby("lote_id"):
    for optica in OPTICAS:
        for radar in RADAR:
            datos = sub[["fecha", optica, radar]].dropna()

            if len(datos) < 10:
                continue

            rho_original = spearmanr(
                datos[optica], datos[radar]
            ).statistic

            # Anomalias respecto de la mediana de cada fecha.
            # Control descriptivo de diferencias temporales comunes.
            anom = datos.copy()

            for variable in [optica, radar]:
                anom[variable] = (
                    anom[variable]
                    - anom.groupby("fecha")[variable].transform(
                        "median"
                    )
                )

            if (
                anom[optica].nunique() > 1
                and anom[radar].nunique() > 1
            ):
                rho_anomalia = spearmanr(
                    anom[optica], anom[radar]
                ).statistic
            else:
                rho_anomalia = np.nan

            correlaciones.append({
                "lote_id": lote,
                "variable_optica": optica,
                "variable_radar": radar,
                "n": len(datos),
                "rho_original": rho_original,
                "rho_anomalia_fecha": rho_anomalia
            })

corr = pd.DataFrame(correlaciones)

ruta_corr = TABLAS / "correlaciones_multisensor_L15_L16.csv"
corr.to_csv(ruta_corr, index=False)

print("\n=== A. CORRELACIONES DE SPEARMAN ===")
print(
    corr[[
        "lote_id", "variable_optica",
        "variable_radar", "n",
        "rho_original", "rho_anomalia_fecha"
    ]]
    .round(3)
    .to_string(index=False)
)

# ----------------------------------------------------
# B. REDUNDANCIA: PREDICCION DE RADAR CON INDICES OPTICOS
# ----------------------------------------------------

redundancia = []

for lote, sub in pares.groupby("lote_id"):
    for radar in RADAR:
        datos = sub[
            ["fecha"] + OPTICAS + [radar]
        ].dropna().copy()

        if datos["fecha"].nunique() < 3:
            continue

        X = datos[OPTICAS].to_numpy()
        y = datos[radar].to_numpy()
        grupos = datos["fecha"].to_numpy()

        n_splits = min(5, datos["fecha"].nunique())

        cv = GroupKFold(n_splits=n_splits)
        predicciones = np.full(len(datos), np.nan)

        for train, test in cv.split(X, y, groups=grupos):
            modelo = make_pipeline(
                StandardScaler(),
                Ridge(alpha=10.0)
            )
            modelo.fit(X[train], y[train])
            predicciones[test] = modelo.predict(X[test])

        r2 = r2_score(y, predicciones)

        redundancia.append({
            "lote_id": lote,
            "variable_radar": radar,
            "n": len(datos),
            "fechas": datos["fecha"].nunique(),
            "r2_cv_por_fecha": r2
        })

red = pd.DataFrame(redundancia)
ruta_red = TABLAS / "redundancia_radar_optico_L15_L16.csv"
red.to_csv(ruta_red, index=False)

print("\n=== B. REDUNDANCIA INFORMATIVA ===")
print(
    red.round(3).to_string(index=False)
)

print("\nInterpretacion del R2:")
print("Cercano a 1: el radar es predecible desde los indices.")
print("Cercano a 0: poca capacidad predictiva fuera de fecha.")
print("Negativo: peor que predecir la media global.")
print("Un R2 bajo no demuestra por si solo informacion util.")

# ----------------------------------------------------
# C. CLUSTERING EXCLUSIVAMENTE RADAR
# ----------------------------------------------------

variables_radar = [
    f"{v}_{s}"
    for v in RADAR
    for s in ["mediana", "std"]
]

comparaciones = []
asignaciones = []

for lote in ["L15", "L16"]:
    sub = clusters.loc[
        clusters["lote_id"] == lote
    ].copy()

    X = StandardScaler().fit_transform(
        sub[variables_radar]
    )

    k = int(sub["k_intralote"].iloc[0])

    modelo = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=30
    )

    etiquetas_radar = modelo.fit_predict(X) + 1

    ari_optico = adjusted_rand_score(
        sub["cluster_optico_intralote"],
        etiquetas_radar
    )

    ari_multi = adjusted_rand_score(
        sub["cluster_multi_intralote"],
        etiquetas_radar
    )

    silueta = silhouette_score(X, etiquetas_radar)

    sub["cluster_solo_radar"] = etiquetas_radar
    asignaciones.append(sub)

    comparaciones.append({
        "lote_id": lote,
        "k": k,
        "n_celdas": len(sub),
        "silueta_radar": silueta,
        "ari_radar_vs_optico": ari_optico,
        "ari_radar_vs_multisensor": ari_multi,
        "tamano_minimo_radar": int(
            pd.Series(etiquetas_radar).value_counts().min()
        )
    })

comp = pd.DataFrame(comparaciones)
asignaciones = pd.concat(asignaciones, ignore_index=True)

ruta_comp = TABLAS / "comparacion_clustering_radar_L15_L16.csv"
ruta_asig = BASE / "clusters_tres_modelos_L15_L16.csv"

comp.to_csv(ruta_comp, index=False)
asignaciones.to_csv(ruta_asig, index=False)

print("\n=== C. CLUSTERING EXCLUSIVAMENTE RADAR ===")
print(
    comp.round(3).to_string(index=False)
)

# ----------------------------------------------------
# D. FIGURA COMPARATIVA
# ----------------------------------------------------

fig, axes = plt.subplots(
    2, 3, figsize=(15, 9),
    constrained_layout=True
)

modelos = [
    ("cluster_optico_intralote", "Sentinel-2"),
    ("cluster_solo_radar", "SAOCOM"),
    ("cluster_multi_intralote", "Fusion multisensor")
]

for fila, lote in enumerate(["L15", "L16"]):
    sub = asignaciones.loc[
        asignaciones["lote_id"] == lote
    ]

    for columna, (variable, nombre) in enumerate(modelos):
        ax = axes[fila, columna]

        for grupo in sorted(sub[variable].unique()):
            datos = sub.loc[sub[variable] == grupo]

            ax.scatter(
                datos["x_utm"],
                datos["y_utm"],
                marker="s",
                s=170,
                edgecolors="white",
                linewidths=0.4,
                label=f"Grupo {grupo}"
            )

        ax.set_title(f"{lote} | {nombre}")
        ax.set_aspect("equal")
        ax.set_xlabel("Este UTM (m)")

        if columna == 0:
            ax.set_ylabel("Norte UTM (m)")

        ax.legend(fontsize=8)

fig.suptitle(
    "Comparacion exploratoria de tres modelos de clustering",
    fontsize=14
)

ruta_fig = FIGURAS / "complementariedad_clustering_L15_L16.png"
fig.savefig(ruta_fig, dpi=200)
plt.close(fig)

print("\n=== ARCHIVOS GENERADOS ===")
for ruta in [
    ruta_corr,
    ruta_red,
    ruta_comp,
    ruta_asig,
    ruta_fig
]:
    print(ruta)

print("\nLIMITACIONES:")
print("- Las observaciones celda-fecha no son independientes.")
print("- Las correlaciones son descriptivas.")
print("- La validacion por fecha evalua transferencia temporal,")
print("  no independencia espacial.")
print("- Los R2 dependen del modelo Ridge y de sus atributos.")
print("- Los grupos radar no tienen validacion agronomica.")
print("- Las etiquetas de los grupos son arbitrarias.")
