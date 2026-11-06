from pathlib import Path
import numpy as np
import pandas as pd

base = Path("data/processed")

general = pd.read_csv(
    base / "dataset_saocom_intralote.csv"
)

piloto = pd.read_csv(
    base / "piloto_saocom_L02_multipolarizacion_20241009.csv"
)

variables = ["HH_db", "HV_db", "VH_db", "VV_db"]
claves = ["fila", "columna"]

muestra = general.loc[
    (general["fecha"] == "2024-10-09")
    & (general["lote_id"] == "L02")
].copy()

comparacion = piloto.merge(
    muestra,
    on=claves,
    how="outer",
    suffixes=("_piloto", "_general"),
    indicator=True,
    validate="one_to_one"
)

print("\n=== VALIDACION CONTRA PILOTO L02 ===")
print("Registros piloto:", len(piloto))
print("Registros general:", len(muestra))
print("Coincidencias:", (comparacion["_merge"] == "both").sum())
print("Solo piloto:", (comparacion["_merge"] == "left_only").sum())
print("Solo general:", (comparacion["_merge"] == "right_only").sum())

print("\n=== DIFERENCIAS NUMERICAS ===")

coincidentes = comparacion[
    comparacion["_merge"] == "both"
]

for variable in ["x_utm", "y_utm"] + variables:
    a = coincidentes[f"{variable}_piloto"].to_numpy(dtype=float)
    b = coincidentes[f"{variable}_general"].to_numpy(dtype=float)

    mismos_faltantes = np.array_equal(
        np.isnan(a), np.isnan(b)
    )

    iguales = np.allclose(
        a, b, rtol=1e-9, atol=1e-6, equal_nan=True
    )

    print(
        f"{variable:8s} | "
        f"iguales={iguales} | "
        f"faltantes_coinciden={mismos_faltantes}"
    )

print("\n=== FALTANTES HV-VH ===")

hv = general["HV_db"].isna()
vh = general["VH_db"].isna()

print("Solo HV faltante:", (hv & ~vh).sum())
print("Solo VH faltante:", (~hv & vh).sum())
print("Ambas faltantes:", (hv & vh).sum())

print("\n=== COBERTURA TEMPORAL POR LOTE ===")

cobertura = general.groupby(
    ["fecha", "lote_id"]
).size()

print("Combinaciones fecha-lote:", len(cobertura))
print("Combinaciones esperadas:", 13 * 16)
print("Minimo pixeles por fecha-lote:", cobertura.min())
print("Maximo pixeles por fecha-lote:", cobertura.max())

print("\n=== RESULTADO ===")

piloto_valido = (
    len(muestra) == len(piloto)
    and len(coincidentes) == len(piloto)
    and all(
        np.allclose(
            coincidentes[f"{v}_piloto"].to_numpy(dtype=float),
            coincidentes[f"{v}_general"].to_numpy(dtype=float),
            rtol=1e-9,
            atol=1e-6,
            equal_nan=True
        )
        for v in ["x_utm", "y_utm"] + variables
    )
)

cobertura_valida = len(cobertura) == 208

print("Piloto reproducido:", piloto_valido)
print("Cobertura completa:", cobertura_valida)

if not (piloto_valido and cobertura_valida):
    raise ValueError("Se requiere revisar la extraccion.")
