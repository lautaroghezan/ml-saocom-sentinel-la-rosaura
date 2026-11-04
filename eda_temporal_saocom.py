from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data/processed/dataset_saocom_potreros.csv")
df["fecha"] = pd.to_datetime(df["fecha"])

polarizaciones = ["HH", "HV", "VH", "VV"]

resumen = (
    df.groupby(["fecha", "polarizacion"])
    .agg(
        mediana_entre_lotes=("mediana_db", "median"),
        n_lotes=("lote_id", "nunique")
    )
    .reset_index()
    .sort_values("fecha")
)

fig, axes = plt.subplots(
    2, 2, figsize=(13, 8), sharex=True
)

for ax, pol in zip(axes.flat, polarizaciones):
    d = resumen[resumen["polarizacion"] == pol]

    ax.plot(
        d["fecha"],
        d["mediana_entre_lotes"],
        marker="o",
        linewidth=1.8,
        markersize=5
    )

    ax.set_title(f"Polarización {pol}")
    ax.set_ylabel("Retrodispersión (dB)")
    ax.grid(alpha=0.2)

    ax.xaxis.set_major_locator(
        mdates.MonthLocator(interval=1)
    )
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%b %Y")
    )

fig.suptitle(
    "La Rosaura — Evolución temporal SAOCOM (2024/25)",
    fontsize=15
)

fig.supxlabel("Fecha de adquisición")
fig.tight_layout()

figuras = Path("reports/figures")
tablas = Path("reports/tables")
figuras.mkdir(parents=True, exist_ok=True)
tablas.mkdir(parents=True, exist_ok=True)

archivo = figuras / "eda_saocom_evolucion_polarizaciones.png"

fig.savefig(archivo, dpi=220, bbox_inches="tight")
plt.close(fig)

resumen.to_csv(
    tablas / "eda_saocom_resumen_temporal.csv",
    index=False
)

print("\n=== EDA TEMPORAL SAOCOM ===")
print("Fechas:", resumen["fecha"].nunique())
print("Polarizaciones:", resumen["polarizacion"].nunique())
print("Lotes por fecha y polarizacion:",
      resumen["n_lotes"].min(),
      "a",
      resumen["n_lotes"].max())
print("\nResumen temporal:")
print(resumen.to_string(index=False))
print("\nGrafico:", archivo)
