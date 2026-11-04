import pandas as pd

sar = pd.read_csv("data/processed/dataset_saocom_potreros.csv")
s2 = pd.read_csv("data/processed/dataset_sentinel2_potreros.csv")

sar["fecha"] = pd.to_datetime(sar["fecha"])
s2["fecha"] = pd.to_datetime(s2["fecha"])

sar = (
    sar.pivot(
        index=["fecha", "lote_id"],
        columns="polarizacion",
        values="mediana_db"
    )
    .reset_index()
    .rename(columns={"fecha": "fecha_saocom"})
)

indices = ["NDVI_mediana", "NDRE_mediana", "NDMI_mediana"]

s2 = s2.loc[
    s2[indices].notna().all(axis=1)
    & (s2["pct_validos_scl"] >= 80)
].copy()

s2 = s2.rename(columns={"fecha": "fecha_sentinel"})

print("\n=== EMPAREJAMIENTO MULTISENSOR CORREGIDO ===")
print("Observaciones SAOCOM:", len(sar))
print("Observaciones Sentinel-2 calidad alta:", len(s2))

for ventana in [3, 5, 7]:
    pares = []

    for lote in sorted(sar["lote_id"].unique()):
        a = (
            sar[sar["lote_id"] == lote]
            .sort_values("fecha_saocom")
        )

        b = (
            s2[s2["lote_id"] == lote]
            .drop(columns=["lote_id"])
            .sort_values("fecha_sentinel")
        )

        combinado = pd.merge_asof(
            a,
            b,
            left_on="fecha_saocom",
            right_on="fecha_sentinel",
            direction="nearest",
            tolerance=pd.Timedelta(days=ventana)
        )

        pares.append(combinado)

    resultado = pd.concat(pares, ignore_index=True)

    completos = resultado["fecha_sentinel"].notna()

    diferencia = (
        resultado.loc[completos, "fecha_saocom"]
        - resultado.loc[completos, "fecha_sentinel"]
    ).abs().dt.days

    print(f"\n=== VENTANA +/-{ventana} DIAS ===")
    print("Pares validos:", int(completos.sum()))
    print("Cobertura (%):", round(100 * completos.mean(), 2))
    print(
        "Fechas SAOCOM emparejadas:",
        resultado.loc[completos, "fecha_saocom"].nunique()
    )
    print(
        "Lotes emparejados:",
        resultado.loc[completos, "lote_id"].nunique()
    )

    if len(diferencia):
        print(
            "Diferencia temporal mediana (dias):",
            diferencia.median()
        )
        print(
            "Diferencia temporal maxima (dias):",
            diferencia.max()
        )
