from pathlib import Path
import pandas as pd

BASE = Path.cwd()

datos = pd.read_csv(
    BASE / "data/processed/dataset_sentinel2_intralote.csv",
    parse_dates=["fecha"]
)

datos["mes"] = datos["fecha"].dt.to_period("M").astype(str)

# Disponibilidad de cada adquisicion
fechas = (
    datos.groupby("fecha")
    .agg(
        pixeles=("valido_scl", "size"),
        validos=("valido_scl", "sum")
    )
    .reset_index()
)

fechas["mes"] = fechas["fecha"].dt.to_period("M").astype(str)

fechas["pct_validos"] = (
    100 * fechas["validos"] / fechas["pixeles"]
)

# Resumen mensual
mensual = (
    fechas.groupby("mes")
    .agg(
        adquisiciones=("fecha", "size"),
        fechas_sin_datos=("validos", lambda x: int((x == 0).sum())),
        fechas_cobertura_80=("pct_validos", lambda x: int((x >= 80).sum())),
        pixeles_evaluados=("pixeles", "sum"),
        pixeles_validos=("validos", "sum")
    )
    .reset_index()
)

mensual["pct_validos"] = (
    100 * mensual["pixeles_validos"]
    / mensual["pixeles_evaluados"]
)

salida = (
    BASE / "reports/tables"
    / "disponibilidad_mensual_sentinel2_intralote.csv"
)

salida.parent.mkdir(parents=True, exist_ok=True)
mensual.to_csv(salida, index=False)

print("\n=== DISPONIBILIDAD MENSUAL SENTINEL-2 ===")

print(
    mensual[
        [
            "mes",
            "adquisiciones",
            "fechas_sin_datos",
            "fechas_cobertura_80",
            "pct_validos"
        ]
    ].to_string(
        index=False,
        float_format="%.2f"
    )
)

print("\n=== RESUMEN ===")
print("Meses analizados:", len(mensual))
print(
    "Mes con menor cobertura:",
    mensual.loc[
        mensual["pct_validos"].idxmin(), "mes"
    ]
)
print(
    "Mes con mayor cobertura:",
    mensual.loc[
        mensual["pct_validos"].idxmax(), "mes"
    ]
)

print("\nDiagnostico finalizado.")
