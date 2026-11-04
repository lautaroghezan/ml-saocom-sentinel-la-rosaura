from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

entrada = Path("data/processed/dataset_sentinel2_potreros.csv")
salida = Path("reports/figures")
tablas = Path("reports/tables")

salida.mkdir(parents=True, exist_ok=True)
tablas.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(entrada)

indices = ["NDVI", "NDRE", "NDMI"]
columnas = [f"{i}_mediana" for i in indices]

calidad = (
    df[columnas].notna().all(axis=1)
    & (df["pct_validos_scl"] >= 80)
)

d = df.loc[calidad].copy()

fig, ax = plt.subplots(figsize=(9, 5.5))

ax.boxplot(
    [d[c].dropna().values for c in columnas],
    tick_labels=indices,
    showmeans=True,
    patch_artist=False
)

ax.axhline(0, color="gray", linewidth=0.8)
ax.set_ylabel("Valor del índice espectral")
ax.set_title("Distribución de índices Sentinel-2 — Calidad ≥80 %")
ax.grid(axis="y", alpha=0.2)

fig.tight_layout()

archivo = salida / "eda_sentinel2_boxplots_indices.png"
fig.savefig(archivo, dpi=220, bbox_inches="tight")
plt.close(fig)

resumen = d[columnas].describe().T
resumen["IQR"] = resumen["75%"] - resumen["25%"]

resumen.to_csv(
    tablas / "eda_sentinel2_estadisticos_indices.csv"
)

print("\n=== EDA SENTINEL-2 ===")
print("Observaciones de calidad alta:", len(d))
print("Fechas:", d["fecha"].nunique())
print("Lotes:", d["lote_id"].nunique())

print("\nEstadisticos descriptivos:")
print(resumen.round(4).to_string())

print("\nGrafico:", archivo)
