from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

entrada = Path("data/processed/dataset_saocom_potreros.csv")
figuras = Path("reports/figures")
tablas = Path("reports/tables")

figuras.mkdir(parents=True, exist_ok=True)
tablas.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(entrada)
df["fecha"] = pd.to_datetime(df["fecha"])

polarizaciones = ["HH", "HV", "VH", "VV"]

# Control de integridad
duplicados = df.duplicated(
    subset=["fecha", "lote_id", "polarizacion"]
).sum()

print("\n=== CONTROL DE CALIDAD SAOCOM ===")
print("Registros:", len(df))
print("Fechas:", df["fecha"].nunique())
print("Lotes:", df["lote_id"].nunique())
print("Duplicados:", duplicados)
print("Medianas faltantes:", df["mediana_db"].isna().sum())
print("Medianas infinitas:",
      np.isinf(df["mediana_db"]).sum())

print("\nRegistros por polarizacion:")
print(df["polarizacion"].value_counts().to_string())

# Estadisticos descriptivos
resumen = (
    df.groupby("polarizacion")["mediana_db"]
    .describe()
    .reindex(polarizaciones)
)

resumen["IQR"] = resumen["75%"] - resumen["25%"]

print("\n=== ESTADISTICOS SAOCOM (dB) ===")
print(resumen.round(3).to_string())

resumen.to_csv(
    tablas / "eda_saocom_estadisticos_polarizaciones.csv"
)

# Diagramas de cajas
datos = [
    df.loc[
        df["polarizacion"] == pol, "mediana_db"
    ].dropna().values
    for pol in polarizaciones
]

fig, ax = plt.subplots(figsize=(9, 5.5))

ax.boxplot(
    datos,
    tick_labels=polarizaciones,
    showmeans=True
)

ax.set_xlabel("Polarizacion")
ax.set_ylabel("Retrodispersion mediana (dB)")
ax.set_title("SAOCOM - Distribucion por polarizacion")
ax.grid(axis="y", alpha=0.2)

fig.tight_layout()

archivo = figuras / "eda_saocom_boxplots_polarizaciones.png"
fig.savefig(archivo, dpi=220, bbox_inches="tight")
plt.close(fig)

print("\nGrafico generado:", archivo)
