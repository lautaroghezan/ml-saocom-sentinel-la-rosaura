from pathlib import Path
import numpy as np
import pandas as pd

base = Path("data/processed")

nuevo = pd.read_csv(
    base / "dataset_sentinel2_intralote.csv"
)

original = pd.read_csv(
    base / "dataset_sentinel2_potreros.csv"
)

indices = ["NDVI", "NDRE", "NDMI"]
claves = ["fecha", "lote_id"]

resultados = []

for nombre in indices:

    agrupado = nuevo.groupby(claves)[nombre].agg(
        n="count",
        mediana="median",
        p25=lambda x: x.quantile(0.25),
        p75=lambda x: x.quantile(0.75)
    ).reset_index()

    agrupado["iqr"] = (
        agrupado["p75"] - agrupado["p25"]
    )

    comparacion = original.merge(
        agrupado,
        on=claves,
        how="outer",
        validate="one_to_one",
        indicator=True
    )

    if not comparacion["_merge"].eq("both").all():
        raise ValueError(
            f"Combinaciones no coincidentes: {nombre}"
        )

    for estadistico in [
        "n", "mediana", "p25", "p75", "iqr"
    ]:

        anterior = comparacion[
            f"{nombre}_{estadistico}"
        ]

        actual = comparacion[estadistico]

        ambos_nan = anterior.isna() & actual.isna()

        iguales = np.isclose(
            anterior.to_numpy(dtype=float),
            actual.to_numpy(dtype=float),
            rtol=0,
            atol=1e-6,
            equal_nan=True
        )

        diferencia = (
            anterior - actual
        ).abs()

        resultados.append({
            "indice": nombre,
            "estadistico": estadistico,
            "comparaciones": len(comparacion),
            "coincidencias": int(iguales.sum()),
            "diferencia_maxima": (
                float(diferencia.max())
                if diferencia.notna().any()
                else np.nan
            ),
            "ambos_sin_datos": int(ambos_nan.sum())
        })

resumen = pd.DataFrame(resultados)

print("\n=== VALIDACION ESTADISTICA SENTINEL-2 ===")
print(resumen.to_string(index=False))

aprobado = (
    resumen["coincidencias"]
    == resumen["comparaciones"]
).all()

print("\nVALIDACION ESTADISTICA:",
      "APROBADA" if aprobado else "REVISAR")

if not aprobado:
    print(
        "\nExisten diferencias que debemos diagnosticar."
    )
