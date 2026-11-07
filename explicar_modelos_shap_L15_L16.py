from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

BASE = Path("data/processed")
TABLAS = Path("reports/tables")
FIGURAS = Path("reports/figures")
TABLAS.mkdir(parents=True, exist_ok=True)
FIGURAS.mkdir(parents=True, exist_ok=True)

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

configuraciones = {
    "Optico": opticas,
    "Multisensor": opticas + radar
}

resultados = []

print("\n=== PASO 19G: EXPLICABILIDAD SHAP ===")

for lote in ["L15", "L16"]:
    sub = df[df["lote_id"] == lote].copy()
    y = sub["cluster_optico_intralote"].to_numpy()

    for nombre, variables in configuraciones.items():
        X = sub[variables].astype(float).to_numpy()

        modelo = make_pipeline(
            StandardScaler(),
            LogisticRegression(
                C=1.0,
                class_weight="balanced",
                max_iter=3000,
                random_state=42
            )
        )

        modelo.fit(X, y)

        escalador = modelo.named_steps["standardscaler"]
        clasificador = modelo.named_steps["logisticregression"]

        X_escalado = escalador.transform(X)

        explicador = shap.LinearExplainer(
            clasificador,
            X_escalado
        )

        valores = np.asarray(
            explicador.shap_values(X_escalado)
        )

        if valores.ndim == 3:
            valores = valores[:, :, -1]

        importancia = np.abs(valores).mean(axis=0)

        ranking = pd.DataFrame({
            "variable": variables,
            "importancia_shap": importancia
        }).sort_values(
            "importancia_shap",
            ascending=False
        )

        ranking["lote_id"] = lote
        ranking["modelo"] = nombre
        ranking["objetivo"] = "cluster_optico_intralote"

        resultados.append(ranking)

        print(f"\n{lote} - {nombre}")
        print(
            ranking[
                ["variable", "importancia_shap"]
            ].head(8).round(4).to_string(index=False)
        )

        grafico = ranking.sort_values(
            "importancia_shap"
        )

        fig, ax = plt.subplots(figsize=(9, 5.5))
        ax.barh(
            grafico["variable"],
            grafico["importancia_shap"]
        )
        ax.set_xlabel(
            "Importancia media absoluta SHAP"
        )
        ax.set_title(
            f"{lote} - {nombre} - etiquetas opticas"
        )
        ax.grid(axis="x", alpha=0.2)
        fig.tight_layout()

        ruta_figura = (
            FIGURAS /
            f"shap_{lote}_{nombre.lower()}.png"
        )
        fig.savefig(
            ruta_figura,
            dpi=200,
            bbox_inches="tight"
        )
        plt.close(fig)

        print("Figura:", ruta_figura)

tabla = pd.concat(resultados, ignore_index=True)

ruta_tabla = (
    TABLAS / "importancia_shap_L15_L16.csv"
)
tabla.to_csv(ruta_tabla, index=False)

print("\nARCHIVO DE RESULTADOS:")
print(ruta_tabla)

print("\nLIMITACIONES:")
print("- SHAP explica un modelo de pseudoetiquetas.")
print("- El modelo se ajusto sobre todas las celdas.")
print("- No es una evaluacion predictiva independiente.")
print("- Importancia SHAP no equivale a causalidad.")
print("- Variables correlacionadas pueden compartir importancia.")

print("\n=== PASO 19G FINALIZADO ===")
