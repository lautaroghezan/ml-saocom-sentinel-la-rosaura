from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path.cwd()
ENTRADA = BASE / "data/processed/dataset_sentinel2_intralote.csv"
SALIDA = BASE / "reports/tables/caidas_ndvi_intralote.csv"

datos = pd.read_csv(ENTRADA, parse_dates=["fecha"])

datos = datos.loc[
    (datos["fecha"] >= "2024-11-01")
    & (datos["fecha"] <= "2025-04-30")
].copy()

resultados = []

for lote_id, grupo in datos.groupby("lote_id"):

    matriz = grupo.pivot(
        index=["fila", "columna"],
        columns="fecha",
        values="NDVI"
    ).sort_index(axis=1)

    # Excluir fechas sin cobertura suficiente.
    cobertura = matriz.notna().mean(axis=0)
    fechas = cobertura[cobertura >= 0.80].index.tolist()

    for anterior, posterior in zip(fechas[:-1], fechas[1:]):

        a = matriz[anterior]
        b = matriz[posterior]

        comunes = a.notna() & b.notna()
        n_comunes = int(comunes.sum())
        pct_comunes = 100 * comunes.mean()

        if pct_comunes < 80:
            continue

        diferencias = b[comunes] - a[comunes]
        dias = (posterior - anterior).days

        resultados.append({
            "lote_id": lote_id,
            "fecha_anterior": anterior.date().isoformat(),
            "fecha_posterior": posterior.date().isoformat(),
            "dias": dias,
            "pixeles_comunes": n_comunes,
            "pct_comunes": round(pct_comunes, 2),
            "ndvi_anterior": round(a[comunes].median(), 4),
            "ndvi_posterior": round(b[comunes].median(), 4),
            "delta_ndvi_mediana": round(
                b[comunes].median() - a[comunes].median(), 4
            ),
            "delta_mediano_pixeles": round(
                diferencias.median(), 4
            ),
            "pct_pixeles_descenso": round(
                100 * (diferencias < 0).mean(), 2
            ),
            "pct_pixeles_caida_020": round(
                100 * (diferencias <= -0.20).mean(), 2
            )
        })

resultado = pd.DataFrame(resultados)

if resultado.empty:
    raise ValueError("No hay pares de fechas comparables")

SALIDA.parent.mkdir(parents=True, exist_ok=True)
resultado.to_csv(SALIDA, index=False)

print("\n=== VALIDACION DE COMPARACIONES ===")
print("Comparaciones:", len(resultado))
print("Lotes:", resultado["lote_id"].nunique())
print("Dias entre imagenes:")
print(resultado["dias"].describe().to_string())

print("\n=== DIEZ MAYORES CAIDAS DE NDVI ===")
print(
    resultado.nsmallest(10, "delta_ndvi_mediana")[
        [
            "lote_id", "fecha_anterior", "fecha_posterior",
            "dias", "delta_ndvi_mediana",
            "pct_pixeles_descenso", "pct_pixeles_caida_020"
        ]
    ].to_string(index=False)
)

print("\n=== L15 Y L16: MAYORES CAIDAS ===")
seleccion = resultado[
    resultado["lote_id"].isin(["L15", "L16"])
]

print(
    seleccion.nsmallest(10, "delta_ndvi_mediana")[
        [
            "lote_id", "fecha_anterior", "fecha_posterior",
            "dias", "ndvi_anterior", "ndvi_posterior",
            "delta_ndvi_mediana", "pct_pixeles_caida_020"
        ]
    ].to_string(index=False)
)

print("\nArchivo generado:", SALIDA)
print("Diagnostico finalizado.")
