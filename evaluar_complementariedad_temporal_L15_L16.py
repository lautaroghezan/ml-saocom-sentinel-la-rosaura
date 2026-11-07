from pathlib import Path
import pandas as pd

base = Path("data/processed")
salida = Path("reports/tables")
salida.mkdir(parents=True, exist_ok=True)

opt = pd.read_csv(base / "dataset_optico_grilla_L15_L16.csv")
rad = pd.read_csv(base / "dataset_saocom_grilla_L15_L16.csv")

opt["fecha"] = pd.to_datetime(opt["fecha"])
rad["fecha"] = pd.to_datetime(rad["fecha"])

opt["valida"] = (
    (opt["cobertura_optica"] >= 0.50)
    & opt[["NDVI", "NDRE", "NDMI"]].notna().all(axis=1)
)
rad["valida"] = rad[["HH_db", "VV_db"]].notna().all(axis=1)

detalle = []
resumen = []

for lote in ["L15", "L16"]:
    o = opt[opt["lote_id"] == lote]
    r = rad[rad["lote_id"] == lote]

    dias_opticos = set(o.loc[o["valida"], "fecha"].dt.date)
    dias_radar = set(r.loc[r["valida"], "fecha"].dt.date)

    resumen.append({
        "lote_id": lote,
        "fechas_opticas_validas": len(dias_opticos),
        "fechas_radar_validas": len(dias_radar),
        "fechas_union": len(dias_opticos | dias_radar),
        "fechas_adicionales_radar": len(dias_radar - dias_opticos)
    })

    for fecha in sorted(r["fecha"].unique()):
        fecha = pd.Timestamp(fecha)

        rr = r[(r["fecha"] == fecha) & r["valida"]]
        radar_celdas = set(rr["celda_id"])

        cercanas = o[
            (o["fecha"] >= fecha - pd.Timedelta(days=5))
            & (o["fecha"] <= fecha + pd.Timedelta(days=5))
            & o["valida"]
        ]
        opt_celdas = set(cercanas["celda_id"])

        detalle.append({
            "lote_id": lote,
            "fecha_saocom": fecha.date().isoformat(),
            "radar_validas": len(radar_celdas),
            "con_optico_cercano": len(radar_celdas & opt_celdas),
            "solo_radar": len(radar_celdas - opt_celdas)
        })

df_detalle = pd.DataFrame(detalle)
df_resumen = pd.DataFrame(resumen)

df_detalle.to_csv(
    salida / "complementariedad_temporal_por_fecha_L15_L16.csv",
    index=False
)
df_resumen.to_csv(
    salida / "resumen_complementariedad_temporal_L15_L16.csv",
    index=False
)

print("\n=== PASO 19F: RESULTADOS ===")
print("\nRESUMEN:")
print(df_resumen.to_string(index=False))
print("\nDETALLE POR FECHA:")
print(df_detalle.to_string(index=False))
print("\nTOTAL OBSERVACIONES SOLO RADAR:")
print(int(df_detalle["solo_radar"].sum()))
print("\nPASO 19F FINALIZADO CORRECTAMENTE")
