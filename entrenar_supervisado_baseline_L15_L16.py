from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier
)
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    confusion_matrix
)

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

experimentos = {
    "Optico": (
        opticas,
        "cluster_optico_intralote"
    ),
    "Multisensor": (
        opticas + radar,
        "cluster_multi_intralote"
    )
}

def modelos():
    return {
        "Regresion_logistica": make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=3000,
                class_weight="balanced",
                random_state=42
            )
        ),
        "Random_Forest": RandomForestClassifier(
            n_estimators=200,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),
        "HistGradientBoosting": (
            HistGradientBoostingClassifier(
                max_iter=100,
                max_leaf_nodes=7,
                min_samples_leaf=5,
                learning_rate=0.05,
                random_state=42
            )
        )
    }

cv = RepeatedStratifiedKFold(
    n_splits=3,
    n_repeats=5,
    random_state=42
)

resultados = []
matrices = []

print("\n=== PASO 19B: CLASIFICACION DE PSEUDOETIQUETAS ===")

for lote in ["L15", "L16"]:
    sub = df.loc[
        df["lote_id"] == lote
    ].copy()

    for tipo, (variables, objetivo) in experimentos.items():
        X = sub[variables].to_numpy()
        y = sub[objetivo].to_numpy()

        print(f"\n{lote} | {tipo}")
        print(
            "Celdas:", len(sub),
            "| Distribucion:",
            dict(zip(*np.unique(y, return_counts=True)))
        )

        for nombre, constructor in modelos().items():
            scores_ba = []
            scores_f1 = []
            matriz_total = np.zeros((2, 2), dtype=int)

            for train, test in cv.split(X, y):
                modelo = constructor
                modelo.fit(X[train], y[train])
                pred = modelo.predict(X[test])

                scores_ba.append(
                    balanced_accuracy_score(
                        y[test], pred
                    )
                )
                scores_f1.append(
                    f1_score(
                        y[test],
                        pred,
                        average="macro",
                        zero_division=0
                    )
                )
                matriz_total += confusion_matrix(
                    y[test], pred, labels=[1, 2]
                )

            fila = {
                "lote_id": lote,
                "modelo_datos": tipo,
                "clasificador": nombre,
                "balanced_accuracy_media": np.mean(scores_ba),
                "balanced_accuracy_std": np.std(scores_ba),
                "f1_macro_media": np.mean(scores_f1),
                "f1_macro_std": np.std(scores_f1)
            }
            resultados.append(fila)

            matrices.append({
                "lote_id": lote,
                "modelo_datos": tipo,
                "clasificador": nombre,
                "verdadero_1_predicho_1": matriz_total[0, 0],
                "verdadero_1_predicho_2": matriz_total[0, 1],
                "verdadero_2_predicho_1": matriz_total[1, 0],
                "verdadero_2_predicho_2": matriz_total[1, 1]
            })

            print(
                f"{nombre:23s} "
                f"BA={np.mean(scores_ba):.3f} "
                f"F1={np.mean(scores_f1):.3f}"
            )

salida = pd.DataFrame(resultados)
matrices_df = pd.DataFrame(matrices)

ruta_metricas = (
    TABLAS / "metricas_supervisado_baseline_L15_L16.csv"
)
ruta_matrices = (
    TABLAS / "matrices_supervisado_baseline_L15_L16.csv"
)

salida.to_csv(ruta_metricas, index=False)
matrices_df.to_csv(ruta_matrices, index=False)

print("\n=== RESUMEN ===")
print(
    salida.sort_values(
        ["lote_id", "modelo_datos",
         "balanced_accuracy_media"],
        ascending=[True, True, False]
    ).round(3).to_string(index=False)
)

print("\nArchivos generados:")
print(ruta_metricas)
print(ruta_matrices)

print("\nADVERTENCIA METODOLOGICA:")
print("Las etiquetas fueron generadas con KMeans.")
print("Las metricas miden reproduccion de pseudoetiquetas.")
print("No demuestran capacidad predictiva agronomica.")
print("La validacion aleatoria no es espacialmente independiente.")
