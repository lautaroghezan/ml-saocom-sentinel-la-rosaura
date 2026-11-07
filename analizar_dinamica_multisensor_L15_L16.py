from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

BASE = Path("data/processed")
TABLAS = Path("reports/tables")
FIGURAS = Path("reports/figures")
TABLAS.mkdir(parents=True, exist_ok=True)
FIGURAS.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(
    BASE / "dataset_multisensor_grilla_L15_L16.csv",
    parse_dates=["fecha"]
)

opticas = ["NDVI", "NDRE", "NDMI"]
radar = ["HH_db", "HV_db", "VH_db", "VV_db"]

# A. Correlaciones espaciales dentro de cada fecha.
resultados = []

for (lote, fecha), sub in df.groupby(["lote_id", "fecha"]):
    for o in opticas:
        for r in radar:
            datos = sub[[o, r]].dropna()

            if (
                len(datos) >= 15
                and datos[o].nunique() > 1
                and datos[r].nunique() > 1
            ):
                rho = spearmanr(datos[o], datos[r]).statistic

                resultados.append({
                    "lote_id": lote,
                    "fecha": fecha,
                    "optica": o,
                    "radar": r,
                    "n_celdas": len(datos),
                    "rho": rho
                })

corr = pd.DataFrame(resultados)
ruta_corr = TABLAS / "correlaciones_por_fecha_L15_L16.csv"
corr.to_csv(ruta_corr, index=False)

print("\n=== PASO 17E.2: DINAMICA TEMPORAL ===")
print("\nA. Correlaciones NDVI-HH por fecha:")

seleccion = corr.loc[
    (corr["optica"] == "NDVI")
    & (corr["radar"] == "HH_db")
]

print(
    seleccion[[
        "lote_id", "fecha", "n_celdas", "rho"
    ]].round(3).to_string(index=False)
)

# B. Medianas temporales observadas.
medianas = (
    df.groupby(["lote_id", "fecha"])
    .agg(
        NDVI=("NDVI", "median"),
        HH_db=("HH_db", "median"),
        n_optico=("NDVI", "count"),
        n_radar=("HH_db", "count")
    )
    .reset_index()
    .sort_values(["lote_id", "fecha"])
)

# C. Cambios entre fechas consecutivas.
# Solo se calculan cuando ambas fechas tienen
# al menos 15 observaciones opticas.
cambios = []

for lote, sub in df.groupby("lote_id"):
    fechas = sorted(sub["fecha"].unique())

    for f0, f1 in zip(fechas[:-1], fechas[1:]):
        a = sub.loc[
            sub["fecha"] == f0,
            ["celda_id", "NDVI", "HH_db"]
        ]
        b = sub.loc[
            sub["fecha"] == f1,
            ["celda_id", "NDVI", "HH_db"]
        ]

        pares = a.merge(
            b,
            on="celda_id",
            suffixes=("_0", "_1"),
            validate="one_to_one"
        )

        opt = pares.dropna(
            subset=["NDVI_0", "NDVI_1"]
        )
        rad = pares.dropna(
            subset=["HH_db_0", "HH_db_1"]
        )

        cambios.append({
            "lote_id": lote,
            "fecha_inicio": f0,
            "fecha_fin": f1,
            "dias": (f1 - f0).days,
            "n_pares_opticos": len(opt),
            "n_pares_radar": len(rad),
            "delta_NDVI_mediano": (
                (opt["NDVI_1"] - opt["NDVI_0"]).median()
                if len(opt) >= 15 else np.nan
            ),
            "delta_HH_mediano": (
                (rad["HH_db_1"] - rad["HH_db_0"]).median()
                if len(rad) >= 15 else np.nan
            )
        })

cambios = pd.DataFrame(cambios)

ruta_cambios = TABLAS / "cambios_temporales_multisensor_L15_L16.csv"
cambios.to_csv(ruta_cambios, index=False)

print("\nB. Cambios entre adquisiciones:")
print(
    cambios[[
        "lote_id", "fecha_inicio", "fecha_fin",
        "n_pares_opticos", "n_pares_radar",
        "delta_NDVI_mediano", "delta_HH_mediano"
    ]].round(3).to_string(index=False)
)

# D. Figura temporal con ejes separados.
fig, axes = plt.subplots(
    2, 1, figsize=(12, 9),
    constrained_layout=True
)

for ax, lote in zip(axes, ["L15", "L16"]):
    sub = medianas.loc[medianas["lote_id"] == lote]

    ax.plot(
        sub["fecha"], sub["NDVI"],
        marker="o", label="NDVI"
    )
    ax.set_ylabel("NDVI")
    ax.set_ylim(-0.1, 1.0)
    ax.grid(alpha=0.25)

    ax2 = ax.twinx()
    ax2.plot(
        sub["fecha"], sub["HH_db"],
        marker="s", linestyle="--",
        color="#b45c43", label="HH"
    )
    ax2.set_ylabel("HH (dB provisionales)")

    ax.set_title(f"{lote}: evolucion temporal multisensor")
    ax.set_xlabel("Fecha SAOCOM")

    lineas1, etiquetas1 = ax.get_legend_handles_labels()
    lineas2, etiquetas2 = ax2.get_legend_handles_labels()

    ax.legend(
        lineas1 + lineas2,
        etiquetas1 + etiquetas2,
        loc="best"
    )

ruta_fig = FIGURAS / "dinamica_temporal_multisensor_L15_L16.png"
fig.savefig(ruta_fig, dpi=200)
plt.close(fig)

print("\nArchivos generados:")
print(ruta_corr)
print(ruta_cambios)
print(ruta_fig)

print("\nLIMITACIONES:")
print("- Las correlaciones por fecha son descriptivas.")
print("- NDVI y HH tienen distinta sensibilidad fisica.")
print("- Los desfases de hasta 5 dias siguen presentes.")
print("- Los cambios no prueban cosecha, estres o manejo.")
print("- HH conserva calibracion absoluta no verificada.")
