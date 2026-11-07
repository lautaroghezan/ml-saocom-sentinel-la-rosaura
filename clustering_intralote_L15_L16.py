from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    adjusted_rand_score
)
from scipy.optimize import linear_sum_assignment

ENTRADA = Path("data/processed/features_clustering_L15_L16.csv")
SALIDA = Path("data/processed/clusters_intralote_L15_L16.csv")
METRICAS = Path("reports/tables/metricas_clustering_intralote.csv")
FIGURA = Path("reports/figures/clustering_intralote_L15_L16.png")

df = pd.read_csv(ENTRADA)
df = df.loc[df["apta_clustering"] == True].copy()

opticas = [
    f"{v}_{s}"
    for v in ["NDVI", "NDRE", "NDMI"]
    for s in ["mediana", "std"]
]
radar = [
    f"{v}_{s}"
    for v in ["HH_db", "HV_db", "VH_db", "VV_db"]
    for s in ["mediana", "std"]
]

resultados = []
salidas = []
fig, axes = plt.subplots(
    2, 2, figsize=(12, 11),
    constrained_layout=True
)

for fila, lote in enumerate(["L15", "L16"]):
    sub = df.loc[df["lote_id"] == lote].copy()

    # Estandarizacion independiente dentro de cada lote.
    Xo = StandardScaler().fit_transform(sub[opticas])
    Xr = StandardScaler().fit_transform(sub[radar])

    Xm = np.column_stack([
        Xo / np.sqrt(len(opticas)),
        Xr / np.sqrt(len(radar))
    ])

    espacios = {"Optico": Xo, "Multisensor": Xm}
    etiquetas = {}

    for nombre, X in espacios.items():
        for k in [2, 3, 4]:
            modelo = KMeans(
                n_clusters=k,
                random_state=42,
                n_init=30
            )
            grupos = modelo.fit_predict(X)

            resultados.append({
                "lote_id": lote,
                "modelo": nombre,
                "k": k,
                "silueta": silhouette_score(X, grupos),
                "davies_bouldin": davies_bouldin_score(
                    X, grupos
                ),
                "tamano_minimo": int(
                    pd.Series(grupos).value_counts().min()
                )
            })

    # Comparacion controlada: mismo k por lote,
    # elegido a partir de la silueta del modelo optico.
    tabla = pd.DataFrame(resultados)
    candidatos = tabla.loc[
        (tabla["lote_id"] == lote)
        & (tabla["modelo"] == "Optico")
    ]
    k_elegido = int(
        candidatos.sort_values(
            ["silueta", "k"],
            ascending=[False, True]
        ).iloc[0]["k"]
    )

    for nombre, X in espacios.items():
        modelo = KMeans(
            n_clusters=k_elegido,
            random_state=42,
            n_init=30
        )
        etiquetas[nombre] = modelo.fit_predict(X) + 1

    # Alinear etiquetas multisensor con las opticas.
    contingencia = pd.crosstab(
        etiquetas["Optico"],
        etiquetas["Multisensor"]
    )
    indices, columnas = linear_sum_assignment(
        -contingencia.to_numpy()
    )
    mapa = {
        contingencia.columns[j]: contingencia.index[i]
        for i, j in zip(indices, columnas)
    }

    sub["cluster_optico_intralote"] = etiquetas["Optico"]
    sub["cluster_multi_intralote"] = pd.Series(
        etiquetas["Multisensor"], index=sub.index
    ).map(mapa)

    sub["coincide_intralote"] = (
        sub["cluster_optico_intralote"]
        == sub["cluster_multi_intralote"]
    )
    sub["k_intralote"] = k_elegido

    ari = adjusted_rand_score(
        sub["cluster_optico_intralote"],
        sub["cluster_multi_intralote"]
    )

    print(f"\n=== {lote} ===")
    print("Celdas:", len(sub))
    print("k elegido:", k_elegido)
    print("ARI:", round(ari, 3))
    print(
        "Coincidentes:",
        int(sub["coincide_intralote"].sum()),
        "de", len(sub)
    )

    for columna_fig, (nombre, columna) in enumerate([
        ("Sentinel-2", "cluster_optico_intralote"),
        ("Sentinel-2 + SAOCOM", "cluster_multi_intralote")
    ]):
        ax = axes[fila, columna_fig]

        for grupo in sorted(sub[columna].unique()):
            datos = sub.loc[sub[columna] == grupo]
            ax.scatter(
                datos["x_utm"],
                datos["y_utm"],
                marker="s",
                s=210,
                edgecolors="white",
                linewidths=0.5,
                label=f"Grupo {grupo}"
            )

        ax.set_title(
            f"{lote} | {nombre} | k={k_elegido}"
        )
        ax.set_xlabel("Este UTM (m)")
        ax.set_ylabel("Norte UTM (m)")
        ax.set_aspect("equal")
        ax.legend(fontsize=8)

    salidas.append(sub)

metricas = pd.DataFrame(resultados)
resultado = pd.concat(salidas, ignore_index=True)

for ruta in [SALIDA, METRICAS, FIGURA]:
    ruta.parent.mkdir(parents=True, exist_ok=True)

resultado.to_csv(SALIDA, index=False)
metricas.to_csv(METRICAS, index=False)

fig.suptitle(
    "Ambientes intralote: comparacion optica y multisensor",
    fontsize=14
)
fig.savefig(FIGURA, dpi=200)
plt.close(fig)

print("\n=== METRICAS INTRALOTE ===")
print(
    metricas.round(3).to_string(index=False)
)

print("\n=== DISTRIBUCION DE GRUPOS ===")
for lote, sub in resultado.groupby("lote_id"):
    print(f"\n{lote}")
    print(
        pd.crosstab(
            sub["cluster_optico_intralote"],
            sub["cluster_multi_intralote"]
        ).to_string()
    )

print("\nArchivos generados:")
print(SALIDA)
print(METRICAS)
print(FIGURA)

print("\nNOTA:")
print("Los grupos son exploratorios.")
print("La validacion agronomica sigue pendiente.")
