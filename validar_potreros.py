from pathlib import Path
import geopandas as gpd
import pandas as pd

BASE = Path(r"C:\Users\Usuario\OneDrive\Documentos\ml-saocom-sentinel-la-rosaura")

GEOJSON = BASE / "data" / "raw" / "vectores" / "potreros_la_rosaura.geojson"
SALIDA = BASE / "data" / "processed" / "validacion_potreros.csv"

SALIDA.parent.mkdir(parents=True, exist_ok=True)

# Superficies de referencia que veníamos utilizando (ha)
areas_ref = {
    "L01": 11.12,
    "L02": 13.49,
    "L03": 13.44,
    "L04": 12.92,
    "L05": 11.17,
    "L06": 10.88,
    "L07": 8.16,
    "L08": 10.43,
    "L09": 7.80,
    "L10": 9.90,
    "L11": 8.00,
    "L12": 7.13,
    "L13": 9.66,
    "L14": 10.52,
    "L15": 10.26,
    "L16": 10.45
}

# --------------------------------------------------
# 1. Leer GeoJSON
# --------------------------------------------------

gdf = gpd.read_file(GEOJSON)

print("=" * 70)
print("VALIDACION GEOMETRICA - LA ROSAURA")
print("=" * 70)

print(f"\nPoligonos encontrados : {len(gdf)}")
print(f"CRS original          : {gdf.crs}")

# --------------------------------------------------
# 2. Comprobaciones básicas
# --------------------------------------------------

gdf["geometria_valida"] = gdf.geometry.is_valid
gdf["geometria_vacia"] = gdf.geometry.is_empty

duplicados = gdf["lote_id"].duplicated().sum()

print(f"IDs duplicados        : {duplicados}")
print(f"Geometrias validas    : {gdf['geometria_valida'].sum()}/{len(gdf)}")
print(f"Geometrias vacias     : {gdf['geometria_vacia'].sum()}")

# --------------------------------------------------
# 3. Reproyectar a UTM 21S para calcular superficies
# --------------------------------------------------

utm = gdf.to_crs(epsg=32721)

utm["area_calculada_ha"] = utm.geometry.area / 10000

utm["area_referencia_ha"] = utm["lote_id"].map(areas_ref)

utm["diferencia_ha"] = (
    utm["area_calculada_ha"] -
    utm["area_referencia_ha"]
)

utm["diferencia_pct"] = (
    utm["diferencia_ha"] /
    utm["area_referencia_ha"] * 100
)

# --------------------------------------------------
# 4. Buscar solapamientos
# --------------------------------------------------

solapamientos = []

for i in range(len(utm)):
    for j in range(i + 1, len(utm)):

        g1 = utm.geometry.iloc[i]
        g2 = utm.geometry.iloc[j]

        inter = g1.intersection(g2)

        if not inter.is_empty:

            area_inter = inter.area / 10000

            # Ignoramos contactos de borde sin superficie
            if area_inter > 0.0001:
                solapamientos.append({
                    "lote_1": utm.iloc[i]["lote_id"],
                    "lote_2": utm.iloc[j]["lote_id"],
                    "area_solapada_ha": area_inter
                })

# --------------------------------------------------
# 5. Bounding box
# --------------------------------------------------

minx, miny, maxx, maxy = gdf.total_bounds

# --------------------------------------------------
# 6. Tabla final
# --------------------------------------------------

tabla = utm[
    [
        "lote_id",
        "geometria_valida",
        "area_calculada_ha",
        "area_referencia_ha",
        "diferencia_ha",
        "diferencia_pct"
    ]
].copy()

tabla = tabla.sort_values("lote_id")

tabla.to_csv(
    SALIDA,
    index=False,
    encoding="utf-8-sig"
)

# --------------------------------------------------
# 7. Resultados
# --------------------------------------------------

print("\n" + "-" * 70)
print("SUPERFICIES")
print("-" * 70)

print(
    tabla.to_string(
        index=False,
        formatters={
            "area_calculada_ha": "{:.2f}".format,
            "area_referencia_ha": "{:.2f}".format,
            "diferencia_ha": "{:+.2f}".format,
            "diferencia_pct": "{:+.2f}%".format
        }
    )
)

total_calc = tabla["area_calculada_ha"].sum()
total_ref = tabla["area_referencia_ha"].sum()

print("\n" + "-" * 70)
print("RESUMEN")
print("-" * 70)

print(f"Superficie calculada : {total_calc:.2f} ha")
print(f"Superficie referencia: {total_ref:.2f} ha")
print(f"Diferencia total     : {total_calc-total_ref:+.2f} ha")

print("\nBounding box EPSG:4326:")
print(f"Longitud mínima : {minx:.6f}")
print(f"Latitud mínima  : {miny:.6f}")
print(f"Longitud máxima : {maxx:.6f}")
print(f"Latitud máxima  : {maxy:.6f}")

print("\nSolapamientos con superficie:", len(solapamientos))

for s in solapamientos:
    print(
        f"  {s['lote_1']} - {s['lote_2']}: "
        f"{s['area_solapada_ha']:.4f} ha"
    )

print("\nCSV generado:")
print(SALIDA)