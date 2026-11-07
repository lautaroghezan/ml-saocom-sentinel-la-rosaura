from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score

BASE = Path("data/processed")
TABLAS = Path("reports/tables")
TABLAS.mkdir(parents=True, exist_ok=True)

fusion = pd.read_csv(
    BASE / "dataset_multisensor_grilla_L15_L16.csv",
    parse_dates=["fecha"]
)

original = pd.read_csv(
    BASE / "clusters_intralote_L15_L16.csv"
)

opticas = ["NDVI", "NDRE", "NDMI"]
radar = ["HH_db", "HV_db", "VH_db", "VV_db"]

vars_opticas = [
    f"{v}_{s}" for v in opticas
    for s in ["mediana", "std"]
]
vars_radar = [
    f"{v}_{s}" for v in radar
    for s in ["mediana", "std"]
]

# Utilizar solo fechas con indices opticos emparejados.
datos = fusion.loc[
    fusion[opticas].notna().all(axis=1)
].copy()

def crear_features(sub):
    registros = []

    for (lote, celda), grupo in sub.groupby(
        ["lote_id", "celda_id"]
    ):
        fila = {
            "lote_id": lote,
            "celda_id": celda
        }

        for v in opticas + radar:
            fila[f"{v}_mediana"] = grupo[v].median()
            fila[f"{v}_std"] = grupo[v].std()

        registros.append(fila)

    return pd.DataFrame(registros)

def preparar(sub, modelo):
    if modelo == "Optico":
        return StandardScaler().fit_transform(
            sub[vars_opticas]
        )

    Xo = StandardScaler().fit_transform(
        sub[vars_opticas]
    ) / np.sqrt(len(vars_opticas))

    Xr = StandardScaler().fit_transform(
        sub[vars_radar]
    ) / np.sqrt(len(vars_radar))

    return np.column_stack([Xo, Xr])

def clusterizar(sub, modelo, k):
    X = preparar(sub, modelo)

    return KMeans(
        n_clusters=k,
        random_state=42,
        n_init=30
    ).fit_predict(X)

referencias = {
    "Optico": "cluster_optico_intralote",
    "Multisensor": "cluster_multi_intralote"
}

resultados = []

print("\n=== PASO 17H: ROBUSTEZ TEMPORAL ===")

for lote in ["L15", "L16"]:
    original_lote = original.loc[
        original["lote_id"] == lote
    ].copy()

    datos_lote = datos.loc[
        datos["lote_id"] == lote
    ].copy()

    k = int(original_lote["k_intralote"].iloc[0])
    fechas = sorted(datos_lote["fecha"].unique())

    print(f"\n=== {lote} ===")

    for modelo, referencia in referencias.items():
        base_features = crear_features(datos_lote)

        base = original_lote[
            ["celda_id", referencia]
        ].merge(
            base_features,
            on="celda_id",
            how="inner",
            validate="one_to_one"
        )

        variables = (
            vars_opticas if modelo == "Optico"
            else vars_opticas + vars_radar
        )

        if (
            len(base) != len(original_lote)
            or base[variables].isna().any().any()
        ):
            raise ValueError(
                f"Features incompletas: {lote}, {modelo}"
            )

        etiquetas_base = clusterizar(
            base, modelo, k
        )

        ari_reproduccion = adjusted_rand_score(
            base[referencia],
            etiquetas_base
        )

        print(
            f"{modelo}: ARI reproduccion base = "
            f"{ari_reproduccion:.3f}"
        )

        if ari_reproduccion < 0.99:
            print(
                "ADVERTENCIA: la reconstruccion no reproduce "
                "el clustering original."
            )

        for fecha in fechas:
            reducido = datos_lote.loc[
                datos_lote["fecha"] != fecha
            ]

            features = crear_features(reducido)

            comparacion = base[
                ["celda_id", referencia]
            ].merge(
                features,
                on="celda_id",
                how="inner",
                validate="one_to_one"
            )

            if (
                len(comparacion) != len(original_lote)
                or comparacion[variables].isna().any().any()
            ):
                resultados.append({
                    "lote_id": lote,
                    "modelo": modelo,
                    "fecha_omitida": pd.Timestamp(fecha).date(),
                    "ari_vs_original": np.nan,
                    "ari_vs_base_recalculada": np.nan,
                    "celdas": len(comparacion),
                    "estado": "features_incompletas"
                })
                continue

            etiquetas = clusterizar(
                comparacion, modelo, k
            )

            resultados.append({
                "lote_id": lote,
                "modelo": modelo,
                "fecha_omitida": pd.Timestamp(fecha).date(),
                "ari_vs_original": adjusted_rand_score(
                    comparacion[referencia],
                    etiquetas
                ),
                "ari_vs_base_recalculada": adjusted_rand_score(
                    etiquetas_base, etiquetas
                ),
                "celdas": len(comparacion),
                "estado": "ok"
            })

salida = pd.DataFrame(resultados)

ruta = (
    TABLAS /
    "robustez_temporal_clustering_L15_L16.csv"
)
salida.to_csv(ruta, index=False)

print("\n=== RESULTADOS POR FECHA OMITIDA ===")
print(
    salida[
        ["lote_id", "modelo", "fecha_omitida",
         "ari_vs_original", "ari_vs_base_recalculada",
         "estado"]
    ].to_string(index=False, float_format=lambda x: f"{x:.3f}")
)

print("\n=== RESUMEN ===")
print(
    salida.groupby(["lote_id", "modelo"])[
        "ari_vs_original"
    ].agg(["min", "median", "max"])
    .round(3).to_string()
)

print("\nArchivo generado:", ruta)
print("\nIMPORTANTE:")
print("- La prueba evalua sensibilidad a fechas, no campanas.")
print("- Se mantienen fijos k=2 y las mismas celdas.")
print("- La eliminacion de una fecha modifica los atributos.")
print("- Revisar ARI de reproduccion antes de interpretar.")
