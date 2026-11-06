from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path.cwd()

ENTRADA = BASE / "data/processed/dataset_saocom_intralote.csv"
SALIDA_FIG = BASE / "reports/figures/trayectorias_saocom_L14_L15_L16.png"
SALIDA_CSV = BASE / "reports/tables/trayectorias_saocom_L14_L15_L16.csv"

LOTES = ["L14", "L15", "L16"]
POLARIZACIONES = ["HH_db", "HV_db", "VH_db", "VV_db"]

datos = pd.read_csv(ENTRADA, parse_dates=["fecha"])

datos = datos.loc[
    (datos["fecha"] >= "2025-01-01")
    & (datos["fecha"] <= "2025-03-31")
    & datos["lote_id"].isin(LOTES)
].copy()

if datos.empty:
    raise ValueError("No se encontraron observaciones SAOCOM")

resumen = (
    datos.groupby(["fecha", "lote_id"])[POLARIZACIONES]
    .median()
    .reset_index()
    .sort_values(["fecha", "lote_id"])
)

SALIDA_FIG.parent.mkdir(parents=True, exist_ok=True)
SALIDA_CSV.parent.mkdir(parents=True, exist_ok=True)

resumen.to_csv(SALIDA_CSV, index=False)

fig, ejes = plt.subplots(
    2, 2,
    figsize=(13, 9),
    sharex=True
)

for ax, polarizacion in zip(ejes.flat, POLARIZACIONES):

    for lote in LOTES:
        grupo = resumen.loc[
            resumen["lote_id"] == lote
        ].sort_values("fecha")

        ax.plot(
            grupo["fecha"],
            grupo[polarizacion],
            marker="o",
            linewidth=2,
            label=lote
        )

    ax.axvspan(
        pd.Timestamp("2025-02-01"),
        pd.Timestamp("2025-02-16"),
        color="gray",
        alpha=0.18
    )

    ax.set_title(polarizacion)
    ax.set_ylabel("Retrodispersion (dB)")
    ax.grid(alpha=0.25)
    ax.legend()

fig.suptitle(
    "SAOCOM - Evolucion temporal L14, L15 y L16",
    fontsize=14
)

fig.autofmt_xdate()
plt.tight_layout()

plt.savefig(
    SALIDA_FIG,
    dpi=200,
    bbox_inches="tight"
)

plt.show()

print("\n=== MEDIANAS SAOCOM POR FECHA Y LOTE ===")
print(
    resumen.to_string(
        index=False,
        float_format="%.3f"
    )
)

print("\n=== VALIDACION ===")
print("Fechas:", resumen["fecha"].nunique())
print("Lotes:", resumen["lote_id"].nunique())
print("Observaciones lote-fecha:", len(resumen))

print("\nFigura:", SALIDA_FIG)
print("Tabla:", SALIDA_CSV)
print("\nDiagnostico finalizado.")
