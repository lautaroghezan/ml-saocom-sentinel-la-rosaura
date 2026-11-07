from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score

BASE = Path("data/processed")
TABLAS = Path("reports/tables")
TABLAS.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(
    BASE / "clusters_intralote_L15_L16.csv"
)

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

modelos = {
    "Optico": (opticas, "cluster_optico_intralote"),
    "Multisensor": (
        opticas + radar,
        "cluster_multi_intralote"
    )
}

def preparar(sub, variables, nombre):
    if sub[variables].isna().any().any():
        raise ValueError("Existen valores faltantes")

    if nombre == "Optico":
        return StandardScaler().fit_transform(
            sub[variables]
        )

    bloques = []

    o = [v for v in variables if v in opticas]
    r = [v for v in variables if v in radar]

    if o:
        bloques.append(
            StandardScaler().fit_transform(sub[o])
            / np.sqrt(len(o))
        )

    if r:
        bloques.append(
            StandardScaler().fit_transform(sub[r])
            / np.sqrt(len(r))
        )

    return np.column_stack(bloques)

def ajustar(X, k, semilla):
    return KMeans(
        n_clusters=k,
        random_state=semilla,
        n_init=30
    ).fit_predict(X)

resultados = []

print("\n=== PASO 17G: ROBUSTEZ DEL CLUSTERING ===")

for lote in ["L15", "L16"]:
    sub = df.loc[df["lote_id"] == lote].copy()
    k = int(sub["k_intralote"].iloc[0])

    for nombre, (variables, columna) in modelos.items():
        referencia = sub[columna].to_numpy()
        X = preparar(sub, variables, nombre)

        ari_semillas = []

        for semilla in range(30):
            etiquetas = ajustar(X, k, semilla)
            ari = adjusted_rand_score(
                referencia, etiquetas
            )
            ari_semillas.append(ari)

            resultados.append({
                "lote_id": lote,
                "modelo": nombre,
                "prueba": "semilla",
                "detalle": str(semilla),
                "ari": ari
            })

        ari_atributos = []

        for omitida in variables:
            restantes = [
                v for v in variables if v != omitida
            ]

            X_reducida = preparar(
                sub, restantes, nombre
            )

            etiquetas = ajustar(
                X_reducida, k, 42
            )

            ari = adjusted_rand_score(
                referencia, etiquetas
            )

            ari_atributos.append(
                (omitida, ari)
            )

            resultados.append({
                "lote_id": lote,
                "modelo": nombre,
                "prueba": "omitir_atributo",
                "detalle": omitida,
                "ari": ari
            })

        peor = min(
            ari_atributos,
            key=lambda x: x[1]
        )

        print(f"\n{lote} | {nombre}")
        print(
            "Semillas: ARI minimo =",
            round(min(ari_semillas), 3),
            "| mediana =",
            round(float(np.median(ari_semillas)), 3)
        )
        print(
            "Omision de atributos: ARI minimo =",
            round(min(x[1] for x in ari_atributos), 3),
            "| mediana =",
            round(float(np.median(
                [x[1] for x in ari_atributos]
            )), 3)
        )
        print(
            "Atributo mas sensible:",
            peor[0],
            "| ARI =",
            round(peor[1], 3)
        )

salida = pd.DataFrame(resultados)

ruta = TABLAS / "robustez_clustering_intralote_L15_L16.csv"
salida.to_csv(ruta, index=False)

print("\nArchivo generado:", ruta)
print("\nInterpretacion:")
print("ARI = 1: clasificaciones identicas.")
print("ARI cercano a 0: concordancia similar al azar.")
print("Esta prueba no demuestra estabilidad interanual.")
print("Tampoco sustituye la validacion agronomica.")
