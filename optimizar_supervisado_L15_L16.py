from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import (
    RepeatedStratifiedKFold,
    StratifiedKFold,
    GridSearchCV
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score
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
        opticas, "cluster_optico_intralote"
    ),
    "Multisensor": (
        opticas + radar, "cluster_multi_intralote"
    )
}

configuraciones = {
    "Regresion_logistica": (
        Pipeline([
            ("escala", StandardScaler()),
            ("modelo", LogisticRegression(
                max_iter=3000,
                class_weight="balanced",
                random_state=42
            ))
        ]),
        {
            "modelo__C": [0.01, 0.1, 1, 10],
            "modelo__solver": ["lbfgs"]
        }
    ),
    "Random_Forest": (
        RandomForestClassifier(
            n_estimators=120,
            class_weight="balanced",
            random_state=42,
            n_jobs=1
        ),
        {
            "max_depth": [2, 4, None],
            "min_samples_leaf": [1, 3]
        }
    )
}

externa = RepeatedStratifiedKFold(
    n_splits=3,
    n_repeats=2,
    random_state=42
)

interna = StratifiedKFold(
    n_splits=2,
    shuffle=True,
    random_state=123
)

resultados = []

print("\n=== PASO 19C: OPTIMIZACION ANIDADA ===")

for lote in ["L15", "L16"]:
    sub = df.loc[df["lote_id"] == lote].copy()

    for tipo, (variables, objetivo) in experimentos.items():
        X = sub[variables].to_numpy()
        y = sub[objetivo].to_numpy()

        for nombre, (estimador, grilla) in configuraciones.items():
            for fold, (train, test) in enumerate(
                externa.split(X, y), start=1
            ):
                busqueda = GridSearchCV(
                    estimator=estimador,
                    param_grid=grilla,
                    scoring="balanced_accuracy",
                    cv=interna,
                    n_jobs=1,
                    refit=True
                )

                busqueda.fit(X[train], y[train])
                pred = busqueda.predict(X[test])

                resultados.append({
                    "lote_id": lote,
                    "datos": tipo,
                    "clasificador": nombre,
                    "fold": fold,
                    "balanced_accuracy":
                        balanced_accuracy_score(
                            y[test], pred
                        ),
                    "f1_macro": f1_score(
                        y[test], pred,
                        average="macro",
                        zero_division=0
                    ),
                    "mejor_parametro":
                        str(busqueda.best_params_)
                })

            parcial = pd.DataFrame(resultados)
            actual = parcial.loc[
                (parcial["lote_id"] == lote) &
                (parcial["datos"] == tipo) &
                (parcial["clasificador"] == nombre)
            ]

            print(
                f"{lote} | {tipo:11s} | "
                f"{nombre:21s} | "
                f"BA={actual['balanced_accuracy'].mean():.3f} "
                f"| F1={actual['f1_macro'].mean():.3f}"
            )

salida = pd.DataFrame(resultados)

ruta = TABLAS / "optimizacion_anidada_L15_L16.csv"
salida.to_csv(ruta, index=False)

resumen = (
    salida.groupby(
        ["lote_id", "datos", "clasificador"]
    )
    .agg(
        BA_media=("balanced_accuracy", "mean"),
        BA_std=("balanced_accuracy", "std"),
        F1_media=("f1_macro", "mean"),
        F1_std=("f1_macro", "std")
    )
    .round(3)
    .reset_index()
)

ruta_resumen = (
    TABLAS / "resumen_optimizacion_anidada_L15_L16.csv"
)
resumen.to_csv(ruta_resumen, index=False)

print("\n=== RESUMEN FINAL ===")
print(resumen.to_string(index=False))

print("\nArchivos generados:")
print(ruta)
print(ruta_resumen)

print("\nLIMITACIONES:")
print("- Pseudoetiquetas calculadas con todos los datos.")
print("- No existe validacion agronomica independiente.")
print("- La validacion cruzada no controla dependencia espacial.")
print("- Las repeticiones no equivalen a nuevas campanas.")
