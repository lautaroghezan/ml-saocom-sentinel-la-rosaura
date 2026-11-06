from pathlib import Path
import zipfile
import io
import xml.etree.ElementTree as ET

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = carpeta / "EOL1DSARSAO1A14056208.zip"

archivo_xml = "Config/ConfFile_GEC_MR_QTNBS_LA.xml"

objetivos = [
    "ExternalCalibrationFactor",
    "CalibrationConstantsConf"
]

def nombre(tag):
    return tag.split("}")[-1]

def mostrar(elemento, nivel=0, max_nivel=5):
    if nivel > max_nivel:
        return

    etiqueta = nombre(elemento.tag)
    valor = (elemento.text or "").strip()

    if len(valor) > 120:
        valor = valor[:120] + "..."

    atributos = (
        f" {elemento.attrib}"
        if elemento.attrib else ""
    )

    print(
        "  " * nivel
        + etiqueta
        + atributos
        + (f" = {valor}" if valor else "")
    )

    for hijo in elemento:
        mostrar(hijo, nivel + 1, max_nivel)

with zipfile.ZipFile(producto) as exterior:

    internos = [
        n for n in exterior.namelist()
        if n.lower().endswith(".zip")
    ]

    if len(internos) != 1:
        raise ValueError("Se esperaba un unico ZIP interno.")

    with zipfile.ZipFile(io.BytesIO(exterior.read(internos[0]))) as interior:

        raiz = ET.fromstring(interior.read(archivo_xml))

        for objetivo in objetivos:

            encontrados = [
                e for e in raiz.iter()
                if nombre(e.tag) == objetivo
            ]

            print("\n" + "=" * 60)
            print("BLOQUE:", objetivo)
            print("Cantidad:", len(encontrados))
            print("=" * 60)

            for i, elemento in enumerate(encontrados[:2], 1):
                print(f"\nEjemplo {i}")
                mostrar(elemento)

print("\nInspeccion completada.")
