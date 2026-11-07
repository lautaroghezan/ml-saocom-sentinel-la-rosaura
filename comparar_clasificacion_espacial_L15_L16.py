from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
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

atributos = {
    "Optico": opticas,
    "Multisensor": opticas + radar
}

objetivos = {
    "Etiquetas_opticas": "cluster_optico_intralote",
    "Etiquetas_multisensor": "cluster_multi_intralote"
}

orientaciones = {
    "L15": ("Norte_Sur", "fila_grilla"),
    "L16": ("Este_Oeste", "columna_grilla")
}

resultados = []

print("\n=== PASO 19E: COMPARACION ESPACIAL JUSTA ===")

for lote, (orientacion, columna) in orientaciones.items():

    sub = df[df["lote_id"] == lote].copy()
    sub = sub.sort_values("celda_id").reset_index(drop=True)

    valores = sorted(sub[columna].unique())
    franjas = np.array_split(valores, 3)

    mapa = {
        int(valor): i
        for i, franja in enumerate(franjas)
        for valor in franja
    }

    grupos = sub[columna].map(mapa).to_numpy()
    cv = GroupKFold(n_splits=3)

    print(f"\n=== {lote} | {orientacion} ===")

    for nombre_objetivo, columna_objetivo in objetivos.items():

        y = sub[columna_objetivo].to_numpy()

        print(f"\nObjetivo: {nombre_objetivo}")

        for fold, (train, test) in enumerate(
            cv.split(sub, y, groups=grupos),
            start=1
        ):

            clases_train = np.unique(y[train])
            clases_test = np.unique(y[test])

            if len(clases_train) < 2 or len(clases_test) < 2:
                print(
                    f"  Fold {fold}: no evaluable "
                    f"(train={clases_train.tolist()}, "
                    f"test={clases_test.tolist()})"
                )
                continue

            for nombre_datos, variables in atributos.items():

                X = sub[variables].to_numpy()

                modelo = make_pipeline(
                    StandardScaler(),
                    LogisticRegression(
                        C=1.0,
                        max_iter=3000,
                        class_weight="balanced",
                        random_state=42
                    )
                )

                modelo.fit(X[train], y[train])
                pred = modelo.predict(X[test])

                ba = balanced_accuracy_score(y[test], pred)
                f1 = f1_score(
                    y[test],
                    pred,
                    average="macro",
                    zero_division=0
                )

                matriz = confusion_matrix(
                    y[test], pred, labels=[1, 2]
                )

                resultados.append({
                    "lote_id": lote,
                    "orientacion": orientacion,
                    "objetivo": nombre_objetivo,
                    "fold": fold,
                    "datos": nombre_datos,
                    "n_train": len(train),
                    "n_test": len(test),
                    "test_clase_1": int(sum(y[test] == 1)),
                    "test_clase_2": int(sum(y[test] == 2)),
                    "balanced_accuracy": ba,
                    "f1_macro": f1,
                    "errores": int(sum(pred != y[test])),
                    "tn_11": int(matriz[0, 0]),
                    "error_12": int(matriz[0, 1]),
                    "error_21": int(matriz[1, 0]),
                    "tn_22": int(matriz[1, 1])
                })

                print(
                    f"  Fold {fold} | "
                    f"{nombre_datos:11s} | "
                    f"BA={ba:.3f} | "
                    f"F1={f1:.3f} | "
                    f"Errores={sum(pred != y[test])}/{len(test)}"
                )

salida = pd.DataFrame(resultados)

if salida.empty:
    raise RuntimeError(
        "No se encontraron particiones espaciales evaluables."
    )

ruta = TABLAS / "comparacion_espacial_mismo_objetivo_L15_L16.csv"
salida.to_csv(ruta, index=False)

resumen = (
    salida.groupby(
        ["lote_id", "objetivo", "datos"],
        as_index=False
    )
    .agg(
        folds=("fold", "count"),
        BA_media=("balanced_accuracy", "mean"),
        F1_media=("f1_macro", "mean"),
        errores_totales=("errores", "sum"),
        evaluaciones=("n_test", "sum")
    )
)

print("\n=== RESUMEN ===")
print(resumen.round(3).to_string(index=False))

comparacion = resumen.pivot(
    index=["lote_id", "objetivo"],
    columns="datos",
    values="BA_media"
)

comparacion["delta_BA_multisensor_menos_optico"] = (
    comparacion["Multisensor"] - comparacion["Optico"]
)

print("\n=== APORTE RADAR CON MISMO OBJETIVO ===")
print(comparacion.round(3).to_string())

ruta_resumen = (
    TABLAS / "resumen_comparacion_espacial_L15_L16.csv"
)
resumen.to_csv(ruta_resumen, index=False)

print("\nArchivos:")
print(ruta)
print(ruta_resumen)

print("\nINTERPRETACION:")
print("Delta positivo: mejora en esta prueba exploratoria.")
print("Delta negativo: menor rendimiento multisensor.")
print("No implica mejora o deterioro agronomico demostrado.")
print("Las pseudoetiquetas se calcularon con todas las celdas.")
print("Las orientaciones se seleccionaron tras auditar las clases.")
