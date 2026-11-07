from pathlib import Path
from collections import deque
import pandas as pd
import numpy as np

BASE = Path("data/processed")
TABLAS = Path("reports/tables")
TABLAS.mkdir(parents=True, exist_ok=True)

archivo = BASE / "clusters_intralote_L15_L16.csv"
df = pd.read_csv(archivo)

modelos = {
    "Optico": "cluster_optico_intralote",
    "Multisensor": "cluster_multi_intralote"
}

requeridas = [
    "celda_id", "lote_id",
    "fila_grilla", "columna_grilla",
    *modelos.values()
]

faltantes = [c for c in requeridas if c not in df.columns]
if faltantes:
    raise ValueError(
        f"Columnas faltantes en {archivo}: {faltantes}"
    )

def componentes_conectados(celdas):
    pendientes = set(celdas)
    componentes = []

    while pendientes:
        inicio = min(pendientes)
        pendientes.remove(inicio)

        cola = deque([inicio])
        componente = [inicio]

        while cola:
            fila, columna = cola.popleft()

            vecinos = [
                (fila - 1, columna),
                (fila + 1, columna),
                (fila, columna - 1),
                (fila, columna + 1)
            ]

            for vecino in vecinos:
                if vecino in pendientes:
                    pendientes.remove(vecino)
                    cola.append(vecino)
                    componente.append(vecino)

        componentes.append(componente)

    return sorted(
        componentes,
        key=len,
        reverse=True
    )

resultados = []

for lote in ["L15", "L16"]:
    sub = df.loc[df["lote_id"] == lote].copy()

    for nombre, variable in modelos.items():
        for grupo in sorted(sub[variable].dropna().unique()):
            seleccion = sub.loc[sub[variable] == grupo]

            celdas = set(
                zip(
                    seleccion["fila_grilla"].astype(int),
                    seleccion["columna_grilla"].astype(int)
                )
            )

            componentes = componentes_conectados(celdas)
            tamanos = [len(c) for c in componentes]

            resultados.append({
                "lote_id": lote,
                "modelo": nombre,
                "grupo": grupo,
                "n_celdas": len(celdas),
                "n_componentes": len(componentes),
                "componente_mayor": max(tamanos),
                "pct_componente_mayor": (
                    100 * max(tamanos) / len(celdas)
                ),
                "celdas_aisladas": sum(
                    t == 1 for t in tamanos
                ),
                "tamanos_componentes": ",".join(
                    map(str, tamanos)
                )
            })

continuidad = pd.DataFrame(resultados)

ruta_continuidad = (
    TABLAS / "continuidad_espacial_clusters_L15_L16.csv"
)
continuidad.to_csv(ruta_continuidad, index=False)

# Perfiles descriptivos de cada grupo.
variables = [
    c for c in df.columns
    if (
        c.startswith(("NDVI_", "NDRE_", "NDMI_",
                      "HH_db_", "HV_db_", "VH_db_", "VV_db_"))
        and c.endswith(("_mediana", "_std"))
        and pd.api.types.is_numeric_dtype(df[c])
    )
]

perfiles = []

for lote in ["L15", "L16"]:
    sub = df.loc[df["lote_id"] == lote]

    for nombre, variable in modelos.items():
        for grupo, seleccion in sub.groupby(variable):
            registro = {
                "lote_id": lote,
                "modelo": nombre,
                "grupo": grupo,
                "n_celdas": len(seleccion)
            }

            for v in variables:
                registro[v] = seleccion[v].median()

            perfiles.append(registro)

perfiles = pd.DataFrame(perfiles)

ruta_perfiles = (
    TABLAS / "perfiles_ambientes_intralote_L15_L16.csv"
)
perfiles.to_csv(ruta_perfiles, index=False)

print("\n=== PASO 17F: CONTINUIDAD ESPACIAL ===")
print(
    continuidad.round(1).to_string(index=False)
)

print("\n=== PERFILES: MEDIANAS OPTICAS ===")

columnas = [
    "lote_id", "modelo", "grupo", "n_celdas"
] + [
    c for c in [
        "NDVI_mediana", "NDRE_mediana", "NDMI_mediana"
    ] if c in perfiles.columns
]

print(
    perfiles[columnas].round(3).to_string(index=False)
)

print("\nArchivos generados:")
print(ruta_continuidad)
print(ruta_perfiles)

print("\nIMPORTANTE:")
print("- La continuidad se mide por lados compartidos.")
print("- Un grupo continuo no equivale a un ambiente validado.")
print("- La superficie corresponde a celdas de 44 x 44 m.")
print("- No se infiere rendimiento ni fertilidad del suelo.")
