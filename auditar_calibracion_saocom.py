from pathlib import Path
import zipfile
import io
import re
import csv
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

CARPETA = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

SALIDA = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\ml-saocom-sentinel-la-rosaura"
    r"\data\processed\auditoria_calibracion_saocom.csv"
)

SALIDA.parent.mkdir(parents=True, exist_ok=True)

FECHAS = {
    "EOL1DSARSAO1A14948973": "2024-08-06",
    "EOL1DSARSAO1A14948810": "2024-09-07",
    "EOL1DSARSAO1A14948841": "2024-09-23",
    "EOL1DSARSAO1A14056208": "2024-10-09",
    "EOL1DSARSAO1A14948886": "2024-10-25",
    "EOL1DSARSAO1A14948797": "2024-11-10",
    "EOL1DSARSAO1A15392623": "2024-12-12",
    "EOL1DSARSAO1A14948812": "2024-12-28",
    "EOL1DSARSAO1A14065611": "2025-01-13",
    "EOL1DSARSAO1A14065934": "2025-01-29",
    "EOL1DSARSAO1A14065630": "2025-02-14",
    "EOL1DSARSAO1A14065953": "2025-03-02",
    "EOL1DSARSAO1A14065706": "2025-03-18",
}


def polarizacion(nombre):
    m = re.search(r"-(hh|hv|vh|vv)-m\.xml$", nombre.lower())
    return m.group(1).upper() if m else "?"


def localname(tag):
    return tag.split("}")[-1]


def extraer_campos_xml(contenido):
    """
    Conserva todos los campos simples del XML.
    No interpreta todavía su significado.
    """
    root = ET.fromstring(contenido)

    campos = []

    for elem in root.iter():

        texto = elem.text.strip() if elem.text else ""

        if texto:
            campos.append(
                (localname(elem.tag), texto)
            )

        for k, v in elem.attrib.items():
            campos.append(
                (
                    f"{localname(elem.tag)}@{localname(k)}",
                    str(v)
                )
            )

    return campos


# Palabras que pueden señalar información radiométrica/calibración.
# Se usan sólo para LOCALIZAR campos, no para interpretarlos.
CLAVES = (
    "sigma",
    "beta",
    "gamma",
    "calib",
    "radiom",
    "amplitude",
    "intensity",
    "power",
    "scale",
    "factor",
    "gain",
    "offset",
    "unit",
    "pixel",
    "sample",
    "data",
    "image",
    "value"
)


productos = sorted(
    CARPETA.glob("EOL1DSARSAO1A*.zip")
)

filas = []
campos_interes_globales = defaultdict(set)

print("=" * 78)
print("AUDITORIA RADIOMETRICA SAOCOM")
print("=" * 78)
print(f"Productos encontrados: {len(productos)}")
print()

for i, producto in enumerate(productos, 1):

    producto_id = producto.stem
    fecha = FECHAS.get(producto_id, "DESCONOCIDA")

    print(
        f"[{i:02d}/{len(productos):02d}] "
        f"{fecha} | {producto_id}"
    )

    try:

        with zipfile.ZipFile(producto, "r") as z1:

            internos = [
                n for n in z1.namelist()
                if n.lower().endswith(".zip")
            ]

            if len(internos) != 1:
                raise RuntimeError(
                    f"ZIP internos={len(internos)}"
                )

            contenido_zip = z1.read(internos[0])

            with zipfile.ZipFile(
                io.BytesIO(contenido_zip), "r"
            ) as z2:

                xmls = [
                    n for n in z2.namelist()
                    if n.startswith("Data/")
                    and n.lower().endswith("-m.xml")
                ]

                print(
                    f"    XML radiometricos/Data encontrados: "
                    f"{len(xmls)}"
                )

                for xml_nombre in sorted(xmls):

                    pol = polarizacion(xml_nombre)

                    contenido = z2.read(xml_nombre)

                    try:
                        campos = extraer_campos_xml(
                            contenido
                        )

                        seleccionados = []

                        for nombre, valor in campos:

                            texto_busqueda = (
                                nombre + " " + valor
                            ).lower()

                            if any(
                                clave in texto_busqueda
                                for clave in CLAVES
                            ):
                                seleccionados.append(
                                    (nombre, valor)
                                )

                                campos_interes_globales[
                                    nombre
                                ].add(valor)

                        # Guardamos una fila por campo
                        for nombre, valor in seleccionados:

                            filas.append({
                                "fecha": fecha,
                                "producto_id": producto_id,
                                "polarizacion": pol,
                                "xml": Path(xml_nombre).name,
                                "campo": nombre,
                                "valor": valor,
                                "estado": "OK"
                            })

                        print(
                            f"      {pol}: "
                            f"{len(campos)} campos XML, "
                            f"{len(seleccionados)} "
                            f"campos candidatos"
                        )

                    except Exception as e:

                        filas.append({
                            "fecha": fecha,
                            "producto_id": producto_id,
                            "polarizacion": pol,
                            "xml": Path(xml_nombre).name,
                            "campo": "",
                            "valor": "",
                            "estado": f"ERROR: {e}"
                        })

                        print(
                            f"      {pol}: ERROR {e}"
                        )

    except Exception as e:

        print(f"    ERROR PRODUCTO: {e}")

    print()


# ------------------------------------------------------------
# CSV COMPLETO
# ------------------------------------------------------------

columnas = [
    "fecha",
    "producto_id",
    "polarizacion",
    "xml",
    "campo",
    "valor",
    "estado"
]

with open(
    SALIDA,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=columnas
    )

    writer.writeheader()
    writer.writerows(filas)


# ------------------------------------------------------------
# RESUMEN
# ------------------------------------------------------------

print("=" * 78)
print("RESUMEN DE CAMPOS RADIOMETRICOS CANDIDATOS")
print("=" * 78)

for campo in sorted(campos_interes_globales):

    valores = sorted(
        campos_interes_globales[campo]
    )

    print()
    print(f"{campo}")

    # Evitamos imprimir listas enormes
    if len(valores) <= 8:
        for v in valores:
            print(f"    -> {v}")
    else:
        print(
            f"    -> {len(valores)} valores distintos"
        )
        for v in valores[:5]:
            print(f"       {v}")
        print("       ...")


print()
print("=" * 78)
print("CONTROL")
print("=" * 78)

conteo_pol = Counter(
    f["polarizacion"]
    for f in filas
    if f["estado"] == "OK"
)

print(f"Productos esperados : 13")
print(f"Polarizaciones       : HH, HV, VH, VV")
print(f"Filas CSV generadas  : {len(filas)}")

print()
print("CSV generado:")
print(SALIDA)

print()
print(
    "IMPORTANTE: este script NO aplica ninguna "
    "conversion radiometrica."
)
print(
    "Solo inventaria lo que declaran los XML "
    "originales de SAOCOM."
)