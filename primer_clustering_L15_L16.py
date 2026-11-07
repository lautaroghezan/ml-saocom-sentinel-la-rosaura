from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score
)

ENTRADA = Path("data/processed/features_clustering_L15_L16.csv")
TABLA = Path("reports/tables/metricas_clustering_L15_L16.csv")
ETIQUETAS = Path("data/processed/clusters_L15_L16.csv")
FIGURA = Path("reports/figures/clustering_optico_multisensor_L15_L16.png")

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

if len(df) != 107:
    raise ValueError("Se esperaban 107 celdas aptas.")

if df[opticas + radar].isna().any().any():
    raise ValueError("Hay atributos faltantes.")

if df["celda_id"].duplicated().any():
    raise ValueError("Hay celdas duplicadas.")

# Escalado por variable.
Xo = StandardScaler().fit_transform(df[opticas])
Xr = StandardScaler().fit_transform(df[radar])

# Cada bloque aporta el mismo peso total nominal.
Xm = np.column_stack([
    Xo / np.sqrt(len(opticas)),
    Xr / np.sqrt(len(radar))
])

modelos = {
    "Optico": Xo,
    "Multisensor": Xm
}

resultados = []
etiquetas_por_modelo = {}

for nombre, X in modelos.items():
    for k in range(2, 7):
        modelo = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=30
        )
        etiquetas = modelo.fit_predict(X)

        resultados.append({
            "modelo": nombre,
            "k": k,
            "silueta": silhouette_score(X, etiquetas),
            "davies_bouldin": davies_bouldin_score(
                X, etiquetas
            ),
            "calinski_harabasz": calinski_harabasz_score(
                X, etiquetas
            ),
            "inercia": modelo.inertia_,
            "tamano_minimo": int(
                pd.Series(etiquetas).value_counts().min()
            )
        })

metricas = pd.DataFrame(resultados)

# Seleccionamos k con la silueta del modelo optico.
opt = metricas.loc[metricas["modelo"] == "Optico"]
k_elegido = int(
    opt.sort_values(
        ["silueta", "k"],
        ascending=[False, True]
    ).iloc[0]["k"]
)

for nombre, X in modelos.items():
    modelo = KMeans(
        n_clusters=k_elegido,
        random_state=42,
        n_init=30
    )
    etiquetas_por_modelo[nombre] = (
        modelo.fit_predict(X) + 1
    )

df["cluster_optico"] = etiquetas_por_modelo["Optico"]
df["cluster_multisensor"] = etiquetas_por_modelo["Multisensor"]

ari = adjusted_rand_score(
    df["cluster_optico"],
    df["cluster_multisensor"]
)

TABLA.parent.mkdir(parents=True, exist_ok=True)
ETIQUETAS.parent.mkdir(parents=True, exist_ok=True)
FIGURA.parent.mkdir(parents=True, exist_ok=True)

metricas.to_csv(TABLA, index=False)
df.to_csv(ETIQUETAS, index=False)

# Mapas de las mismas celdas.
fig, axes = plt.subplots(
    1, 2, figsize=(12, 6),
    sharex=True, sharey=True
)

for ax, columna, titulo in zip(
    axes,
    ["cluster_optico", "cluster_multisensor"],
    ["Sentinel-2", "Sentinel-2 + SAOCOM"]
):
    for cluster in sorted(df[columna].unique()):
        datos = df.loc[df[columna] == cluster]
        ax.scatter(
            datos["x_utm"],
            datos["y_utm"],
            marker="s",
            s=210,
            label=f"Grupo {cluster}",
            edgecolors="white",
            linewidths=0.4
        )

    for lote, grupo in df.groupby("lote_id"):
        ax.text(
            grupo["x_utm"].mean(),
            grupo["y_utm"].mean(),
            lote,
            fontsize=11,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(
                facecolor="white",
                alpha=0.8,
                edgecolor="none"
            )
        )

    ax.set_title(titulo)
    ax.set_xlabel("Este UTM (m)")
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="best")

axes[0].set_ylabel("Norte UTM (m)")
fig.suptitle(
    f"Clustering exploratorio intralote | K-means, k={k_elegido}"
)
fig.tight_layout()
fig.savefig(FIGURA, dpi=200)
plt.close(fig)

print("\n=== PASO 17B: PRIMER CLUSTERING ===")
print("Celdas utilizadas:", len(df))
print("Grupos seleccionados:", k_elegido)

print("\nMetricas por modelo y numero de grupos:")
print(
    metricas[[
        "modelo", "k", "silueta",
        "davies_bouldin", "tamano_minimo"
    ]]
    .round(3)
    .to_string(index=False)
)

print("\nDistribucion de grupos:")
for nombre, columna in [
    ("Optico", "cluster_optico"),
    ("Multisensor", "cluster_multisensor")
]:
    print("\n", nombre)
    print(
        pd.crosstab(df["lote_id"], df[columna])
        .to_string()
    )

print("\nARI entre particiones:", round(ari, 3))

print("\nArchivos generados:")
print(TABLA)
print(ETIQUETAS)
print(FIGURA)

print("\nADVERTENCIAS:")
print("- Las etiquetas de grupo son arbitrarias.")
print("- Las siluetas de espacios distintos no prueban")
print("  por si solas que un sensor sea superior.")
print("- Los grupos no estan validados agronomicamente.")
