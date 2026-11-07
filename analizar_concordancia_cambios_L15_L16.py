from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

base = Path("data/processed")
tablas = Path("reports/tables")
figuras = Path("reports/figures")
tablas.mkdir(parents=True, exist_ok=True)
figuras.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(
    base / "dataset_multisensor_grilla_L15_L16.csv",
    parse_dates=["fecha"]
)

inicio = pd.Timestamp("2025-01-29")
fin = pd.Timestamp("2025-02-14")

a = df.loc[
    df["fecha"].eq(inicio),
    ["celda_id", "lote_id", "NDVI", "HH_db", "HV_db",
     "VH_db", "VV_db"]
]

b = df.loc[
    df["fecha"].eq(fin),
    ["celda_id", "lote_id", "NDVI", "HH_db", "HV_db",
     "VH_db", "VV_db"]
]

cambios = a.merge(
    b,
    on=["celda_id", "lote_id"],
    suffixes=("_inicio", "_fin"),
    validate="one_to_one"
)

variables = ["NDVI", "HH_db", "HV_db", "VH_db", "VV_db"]

for variable in variables:
    cambios["delta_" + variable] = (
        cambios[variable + "_fin"]
        - cambios[variable + "_inicio"]
    )

resultados = []

for lote, sub in cambios.groupby("lote_id"):
    for radar in ["HH_db", "HV_db", "VH_db", "VV_db"]:
        x = sub[["delta_NDVI", "delta_" + radar]].dropna()

        if (
            len(x) >= 10
            and x["delta_NDVI"].nunique() > 1
            and x["delta_" + radar].nunique() > 1
        ):
            rho = spearmanr(
                x["delta_NDVI"],
                x["delta_" + radar]
            ).statistic
        else:
            rho = np.nan

        resultados.append({
            "lote_id": lote,
            "polarizacion": radar,
            "n_celdas": len(x),
            "rho_delta": rho,
            "delta_NDVI_mediano": x["delta_NDVI"].median(),
            "delta_radar_mediano": x[
                "delta_" + radar
            ].median()
        })

resultado = pd.DataFrame(resultados)

ruta_tabla = tablas / "concordancia_cambios_enero_febrero.csv"
ruta_celdas = base / "cambios_por_celda_enero_febrero.csv"
ruta_figura = figuras / "cambios_ndvi_hh_enero_febrero.png"

resultado.to_csv(ruta_tabla, index=False)
cambios.to_csv(ruta_celdas, index=False)

fig, axes = plt.subplots(
    1, 2, figsize=(11, 5), constrained_layout=True
)

for ax, lote in zip(axes, ["L15", "L16"]):
    sub = cambios.loc[
        cambios["lote_id"].eq(lote),
        ["delta_NDVI", "delta_HH_db"]
    ].dropna()

    ax.scatter(
        sub["delta_NDVI"],
        sub["delta_HH_db"],
        s=35, alpha=0.8
    )
    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax.axvline(0, color="gray", linestyle="--", linewidth=1)
    ax.set_title(lote)
    ax.set_xlabel("Variacion NDVI")
    ax.set_ylabel("Variacion HH (dB provisionales)")
    ax.grid(alpha=0.2)

fig.suptitle(
    "Cambios por celda: 29/01 al 14/02/2025"
)
fig.savefig(ruta_figura, dpi=200)
plt.close(fig)

print("\n=== PASO 17E.3: CONCORDANCIA DE CAMBIOS ===")
print(
    resultado.round(3).to_string(index=False)
)

print("\nArchivos generados:")
print(ruta_tabla)
print(ruta_celdas)
print(ruta_figura)

print("\nNOTA:")
print("Las correlaciones son descriptivas.")
print("No se asume independencia espacial.")
print("No se infiere la causa agronomica de los cambios.")
