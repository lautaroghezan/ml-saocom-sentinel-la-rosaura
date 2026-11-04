from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data/processed/dataset_saocom_potreros.csv")
df["fecha"] = pd.to_datetime(df["fecha"])

lotes = sorted(df["lote_id"].unique())
polarizaciones = ["HH", "HV", "VH", "VV"]

colores = {
    "HH": "#2563A6",
    "HV": "#D97706",
    "VH": "#16865D",
    "VV": "#9333EA"
}

fig, axes = plt.subplots(
    4, 4, figsize=(17, 12),
    sharex=True, sharey=True
)

for ax, lote in zip(axes.flat, lotes):
    datos_lote = df[df["lote_id"] == lote]

    for pol in polarizaciones:
        datos = (
            datos_lote[datos_lote["polarizacion"] == pol]
            .sort_values("fecha")
        )

        ax.plot(
            datos["fecha"],
            datos["mediana_db"],
            marker="o",
            markersize=2.5,
            linewidth=1.2,
            color=colores[pol],
            label=pol
        )

    ax.set_title(lote)
    ax.grid(alpha=0.2)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

fig.suptitle(
    "La Rosaura — Evolución temporal SAOCOM por lote (2024/25)",
    fontsize=15
)

fig.supxlabel("Fecha de adquisición")
fig.supylabel("Retrodispersión mediana (dB)")

handles, labels = axes.flat[0].get_legend_handles_labels()

fig.legend(
    handles, labels,
    loc="lower center",
    ncol=4,
    frameon=False,
    bbox_to_anchor=(0.5, 0.015)
)

fig.tight_layout(rect=[0.02, 0.04, 1, 0.96])

salida = Path("reports/figures")
salida.mkdir(parents=True, exist_ok=True)

archivo = salida / "eda_saocom_temporal_por_lote.png"

fig.savefig(archivo, dpi=220, bbox_inches="tight")
plt.close(fig)

print("\n=== SAOCOM POR LOTE ===")
print("Lotes:", len(lotes))
print("Fechas:", df["fecha"].nunique())
print("Polarizaciones:", len(polarizaciones))
print("Gráfico:", archivo)
