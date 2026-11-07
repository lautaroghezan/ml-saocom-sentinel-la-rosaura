from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.optimize import linear_sum_assignment
from sklearn.metrics import (
    adjusted_rand_score,
    confusion_matrix
)

ENTRADA = Path("data/processed/clusters_L15_L16.csv")
SALIDA = Path("data/processed/comparacion_clusters_L15_L16.csv")
TABLA = Path("reports/tables/perfiles_clusters_L15_L16.csv")
FIGURA = Path("reports/figures/concordancia_clusters_L15_L16.png")

df = pd.read_csv(ENTRADA)

original = df["cluster_optico"].astype(int)
multi = df["cluster_multisensor"].astype(int)

# Alineacion optima de etiquetas mediante asignacion hungara.
grupos_o = sorted(original.unique())
grupos_m = sorted(multi.unique())

matriz = pd.crosstab(
    original, multi
).reindex(
    index=grupos_o,
    columns=grupos_m,
    fill_value=0
)

filas, columnas = linear_sum_assignment(-matriz.to_numpy())

equivalencias = {
    grupos_m[j]: grupos_o[i]
    for i, j in zip(filas, columnas)
}

df["cluster_multi_alineado"] = multi.map(equivalencias)
df["coincide"] = (
    df["cluster_optico"] == df["cluster_multi_alineado"]
)

# ARI independiente de los nombres de grupo.
ari_global = adjusted_rand_score(original, multi)

print("\n=== PASO 17C: CONCORDANCIA ESPACIAL ===")
print("\nEquivalencia de etiquetas multisensor -> optico:")
print(equivalencias)

print("\nMatriz de contingencia original:")
print(matriz.to_string())

print("\nARI global:", round(ari_global, 3))
print(
    "Celdas coincidentes tras alinear etiquetas:",
    int(df["coincide"].sum()),
    "de", len(df)
)
print(
    "Celdas con asignacion diferente:",
    int((~df["coincide"]).sum())
)

print("\nResultados por lote:")
for lote, sub in df.groupby("lote_id"):
    ari = adjusted_rand_score(
        sub["cluster_optico"],
        sub["cluster_multisensor"]
    )
    print(
        lote,
        "| ARI:", round(ari, 3),
        "| Coincidentes:", int(sub["coincide"].sum()),
        "| Diferentes:", int((~sub["coincide"]).sum())
    )

print("\nCeldas que cambian:")
cambios = df.loc[
    ~df["coincide"],
    [
        "celda_id", "lote_id",
        "cluster_optico", "cluster_multi_alineado",
        "NDVI_mediana", "NDRE_mediana", "NDMI_mediana",
        "HH_db_mediana"
    ]
]
if len(cambios):
    print(cambios.round(3).to_string(index=False))
else:
    print("Ninguna.")

# Perfil de atributos por grupo, en cada modelo.
variables = [
    "NDVI_mediana", "NDRE_mediana", "NDMI_mediana",
    "HH_db_mediana", "HV_db_mediana",
    "VH_db_mediana", "VV_db_mediana"
]

perfiles = []
for nombre, columna in [
    ("Optico", "cluster_optico"),
    ("Multisensor", "cluster_multi_alineado")
]:
    resumen = df.groupby(columna)[variables].median()
    resumen["n_celdas"] = df.groupby(columna).size()
    resumen = resumen.reset_index().rename(
        columns={columna: "grupo"}
    )
    resumen.insert(0, "modelo", nombre)
    perfiles.append(resumen)

perfiles = pd.concat(perfiles, ignore_index=True)

print("\nPerfiles medianos por grupo:")
print(perfiles.round(3).to_string(index=False))

# Figura: celdas coincidentes y diferentes.
fig, axes = plt.subplots(
    1, 2, figsize=(12, 6),
    sharex=True, sharey=True
)

for ax, (lote, sub) in zip(axes, df.groupby("lote_id")):
    coincide = sub[sub["coincide"]]
    cambia = sub[~sub["coincide"]]

    ax.scatter(
        coincide["x_utm"], coincide["y_utm"],
        marker="s", s=210, c="#88b79a",
        edgecolors="white", linewidths=0.5,
        label=f"Coinciden ({len(coincide)})"
    )
    if len(cambia):
        ax.scatter(
            cambia["x_utm"], cambia["y_utm"],
            marker="s", s=210, c="#d97757",
            edgecolors="black", linewidths=0.6,
            label=f"Difieren ({len(cambia)})"
        )

    ax.set_title(lote)
    ax.set_xlabel("Este UTM (m)")
    ax.set_aspect("equal")
    ax.legend(fontsize=9)

axes[0].set_ylabel("Norte UTM (m)")
fig.suptitle(
    "Concordancia espacial: Sentinel-2 vs. Sentinel-2 + SAOCOM"
)
fig.tight_layout()

for ruta in [SALIDA, TABLA, FIGURA]:
    ruta.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(SALIDA, index=False)
perfiles.to_csv(TABLA, index=False)
fig.savefig(FIGURA, dpi=200)
plt.close(fig)

print("\nArchivos generados:")
print(SALIDA)
print(TABLA)
print(FIGURA)
