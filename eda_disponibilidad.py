from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

salida = Path("reports/figures")
salida.mkdir(parents=True, exist_ok=True)

tablas = Path("reports/tables")
tablas.mkdir(parents=True, exist_ok=True)

sar = pd.read_csv("data/processed/dataset_saocom_potreros.csv")
s2 = pd.read_csv("data/processed/dataset_sentinel2_potreros.csv")

sar["fecha"] = pd.to_datetime(sar["fecha"])
s2["fecha"] = pd.to_datetime(s2["fecha"])

sar_fechas = sorted(sar["fecha"].unique())
s2_fechas = sorted(s2["fecha"].unique())

s2["valido"] = (
    s2["NDVI_mediana"].notna()
    & s2["NDRE_mediana"].notna()
    & s2["NDMI_mediana"].notna()
)

# 1. Calendario de adquisiciones
fig, ax = plt.subplots(figsize=(12, 3.5))

ax.scatter(sar_fechas, [1] * len(sar_fechas),
           marker="|", s=250, linewidths=2.5,
           label="SAOCOM")

ax.scatter(s2_fechas, [0] * len(s2_fechas),
           marker="|", s=250, linewidths=2,
           label="Sentinel-2")

ax.set_yticks([0, 1])
ax.set_yticklabels(["Sentinel-2", "SAOCOM"])
ax.set_xlabel("Fecha de adquisición")
ax.set_title("Disponibilidad temporal de adquisiciones")
ax.grid(axis="x", alpha=0.2)
fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(salida / "eda_calendario_satelital.png",
            dpi=220, bbox_inches="tight")
plt.close(fig)

# 2. Cobertura válida por fecha
cobertura = (
    s2.groupby("fecha")
    .agg(
        lotes=("lote_id", "nunique"),
        lotes_validos=("valido", "sum")
    )
    .reset_index()
)

cobertura["pct_validos"] = (
    100 * cobertura["lotes_validos"] / cobertura["lotes"]
)

fig, ax = plt.subplots(figsize=(12, 4.5))
ax.bar(cobertura["fecha"], cobertura["pct_validos"], width=3.5)
ax.set_ylim(0, 105)
ax.set_ylabel("Lotes con índices válidos (%)")
ax.set_xlabel("Fecha de adquisición")
ax.set_title("Disponibilidad óptica por fecha — Sentinel-2")
ax.grid(axis="y", alpha=0.2)
fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(salida / "eda_cobertura_sentinel2.png",
            dpi=220, bbox_inches="tight")
plt.close(fig)

# 3. Mapa de calor fecha × lote
matriz = (
    s2.pivot(index="lote_id", columns="fecha", values="valido")
    .sort_index()
)

fig, ax = plt.subplots(figsize=(15, 5))
ax.imshow(matriz.astype(int), aspect="auto",
          interpolation="nearest", cmap="Greens",
          vmin=0, vmax=1)

ax.set_yticks(range(len(matriz.index)))
ax.set_yticklabels(matriz.index)
ax.set_xlabel("Fechas Sentinel-2 (orden cronológico)")
ax.set_ylabel("Lote")
ax.set_title("Disponibilidad de índices por lote y fecha")

fig.tight_layout()
fig.savefig(salida / "eda_mapa_calor_disponibilidad.png",
            dpi=220, bbox_inches="tight")
plt.close(fig)

# 4. Resumen exportable
cobertura.to_csv(
    tablas / "eda_cobertura_temporal_sentinel2.csv",
    index=False
)

print("\n=== EDA DE DISPONIBILIDAD ===")
print("Fechas SAOCOM:", len(sar_fechas))
print("Fechas Sentinel-2:", len(s2_fechas))
print("Observaciones Sentinel-2:", len(s2))
print("Observaciones validas:", int(s2["valido"].sum()))
print("Observaciones sin indices:", int((~s2["valido"]).sum()))
print("Disponibilidad (%):", round(100 * s2["valido"].mean(), 2))
print("Fechas con datos validos:",
      int((cobertura["lotes_validos"] > 0).sum()))
print("Fechas sin datos validos:",
      int((cobertura["lotes_validos"] == 0).sum()))
print("\nGraficos guardados en:", salida)
print("Tabla guardada en:", tablas)
