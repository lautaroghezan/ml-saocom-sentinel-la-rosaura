from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import GroupKFold

RUTA = Path(
    "data/processed/clusters_intralote_L15_L16.csv"
)

SALIDA = Path(
    "reports/tables/auditoria_validacion_espacial_L15_L16.csv"
)
SALIDA.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RUTA)

resultados = []

print("\n=== PASO 19D: AUDITORIA ESPACIAL ===")

for lote in ["L15", "L16"]:
    sub = df.loc[df["lote_id"] == lote].copy()
    sub = sub.sort_values("celda_id").reset_index(drop=True)

    print(f"\n=== {lote}: {len(sub)} celdas ===")

    for orientacion, columna in [
        ("Este_Oeste", "columna_grilla"),
        ("Norte_Sur", "fila_grilla")
    ]:
        # Tres franjas espaciales por coordenada de grilla.
        # Se agrupan filas/columnas completas, no celdas al azar.
        valores = sorted(sub[columna].unique())
        franjas = np.array_split(valores, 3)

        asignacion = {
            int(valor): i
            for i, franja in enumerate(franjas)
            for valor in franja
        }

        grupos = sub[columna].map(asignacion).to_numpy()

        for objetivo in [
            "cluster_optico_intralote",
            "cluster_multi_intralote"
        ]:
            y = sub[objetivo].to_numpy()

            cv = GroupKFold(n_splits=3)

            for fold, (train, test) in enumerate(
                cv.split(sub, y, groups=grupos),
                start=1
            ):
                clases_train = pd.Series(
                    y[train]
                ).value_counts()

                clases_test = pd.Series(
                    y[test]
                ).value_counts()

                ambos_train = len(clases_train) == 2
                ambos_test = len(clases_test) == 2

                resultados.append({
                    "lote_id": lote,
                    "orientacion": orientacion,
                    "objetivo": objetivo,
                    "fold": fold,
                    "n_train": len(train),
                    "n_test": len(test),
                    "train_grupo_1":
                        int(clases_train.get(1, 0)),
                    "train_grupo_2":
                        int(clases_train.get(2, 0)),
                    "test_grupo_1":
                        int(clases_test.get(1, 0)),
                    "test_grupo_2":
                        int(clases_test.get(2, 0)),
                    "ambas_clases_train": ambos_train,
                    "ambas_clases_test": ambos_test,
                    "fold_evaluable":
                        ambos_train and ambos_test
                })

salida = pd.DataFrame(resultados)
salida.to_csv(SALIDA, index=False)

print("\nDistribucion por particion:")
print(
    salida[
        [
            "lote_id", "orientacion", "objetivo",
            "fold", "n_train", "n_test",
            "train_grupo_1", "train_grupo_2",
            "test_grupo_1", "test_grupo_2",
            "fold_evaluable"
        ]
    ].to_string(index=False)
)

print("\nResumen de particiones con ambas clases:")
print(
    salida.groupby(
        ["lote_id", "orientacion", "objetivo"]
    )["fold_evaluable"]
    .agg(["sum", "count"])
    .to_string()
)

print("\nArchivo generado:", SALIDA)
print("\nADVERTENCIAS:")
print("- Las franjas espaciales son una prueba de sensibilidad.")
print("- No equivalen a validacion entre campañas.")
print("- Las pseudoetiquetas originales usaron todas las celdas.")
print("- Una particion sin ambas clases limita las metricas.")
