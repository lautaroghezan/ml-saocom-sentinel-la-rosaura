from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_sentinel2_intralote.csv",
    parse_dates=["fecha"]
)

LOTES = ["L14", "L15", "L16"]

datos = datos.loc[
    (datos["fecha"] >= "2024-11-01")
    & (datos["fecha"] <= "2025-04-30")
    & datos["lote_id"].isin(LOTES)
].copy()

resumen = (
    datos.groupby(["fecha", "lote_id"])
    .agg(
        pixeles=("NDVI", "size"),
        validos=("NDVI", "count"),
        mediana=("NDVI", "median"),
        p25=("NDVI", lambda x: x.quantile(0.25)),
        p75=("NDVI", lambda x: x.quantile(0.75))
    )
    .reset_index()
)

resumen["pct_validos"] = (
    100 * resumen["validos"] / resumen["pixeles"]
)

validos = resumen.loc[
    resumen["pct_validos"] >= 80
].copy()

fig, ax = plt.subplots(figsize=(12, 6))

for lote in LOTES:
    grupo = validos.loc[
        validos["lote_id"] == lote
    ].sort_values("fecha")

    ax.plot(
        grupo["fecha"],
        grupo["mediana"],
        marker="o",
        linewidth=2,
        label=lote
    )

ax.axvspan(
    pd.Timestamp("2025-02-01"),
    pd.Timestamp("2025-02-16"),
    color="gray",
    alpha=0.18,
    label="Intervalo de cambio L15-L16"
)

ax.set_title("Evolucion temporal NDVI - L14, L15 y L16")
ax.set_ylabel("Mediana NDVI")
ax.set_xlabel("Fecha")
ax.set_ylim(0, 1)
ax.grid(alpha=0.25)
ax.legend()

fig.autofmt_xdate()
plt.tight_layout()

SALIDA = (
    BASE / "reports/figures"
    / "trayectorias_ndvi_L14_L15_L16.png"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)

plt.savefig(SALIDA, dpi=200)
plt.show()

print("\n=== OBSERVACIONES VALIDAS POR LOTE ===")
print(validos.groupby("lote_id").size().to_string())

print("\n=== NDVI DESPUES DEL EVENTO ===")
print(
    validos.loc[
        validos["fecha"] >= "2025-02-16",
        ["fecha", "lote_id", "mediana", "pct_validos"]
    ].to_string(index=False)
)

print("\nFigura generada:", SALIDA)
print("Diagnostico finalizado.")
