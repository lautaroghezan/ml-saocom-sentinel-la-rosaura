from pathlib import Path
import zipfile
import io
import xml.etree.ElementTree as ET

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = carpeta / "EOL1DSARSAO1A14056208.zip"

archivos_objetivo = [
    "Config/L1PROCConf.xml",
    "Config/ConfFile_GEC_MR_QTNBS_LA.xml"
]

terminos = [
    "Sigma0Type",
    "ExternalCalibrationFactor",
    "CalibrationConstantsConf",
    "Radiometric",
    "Scale",
    "Offset",
    "CalibrationFactor"
]

def nombre_corto(tag):
    return tag.split("}")[-1]

with zipfile.ZipFile(producto) as exterior:

    internos = [
        n for n in exterior.namelist()
        if n.lower().endswith(".zip")
    ]

    if len(internos) != 1:
        raise ValueError("Se esperaba un unico ZIP interno.")

    with zipfile.ZipFile(io.BytesIO(exterior.read(internos[0]))) as interior:

        for archivo in archivos_objetivo:

            if archivo not in interior.namelist():
                print("No encontrado:", archivo)
                continue

            raiz = ET.fromstring(interior.read(archivo))

            print("\n" + "=" * 60)
            print("ARCHIVO:", archivo)
            print("=" * 60)

            encontrados = 0

            for elemento in raiz.iter():

                etiqueta = nombre_corto(elemento.tag)

                if not any(
                    termino.lower() in etiqueta.lower()
                    for termino in terminos
                ):
                    continue

                encontrados += 1

                print("\nCAMPO:", etiqueta)
                print("VALOR:", (elemento.text or "").strip())
                print("ATRIBUTOS:", elemento.attrib)

                hijos = list(elemento)

                for hijo in hijos[:12]:
                    print(
                        "  ",
                        nombre_corto(hijo.tag),
                        "=",
                        (hijo.text or "").strip()[:120],
                        "| atributos:",
                        hijo.attrib
                    )

            print("\nCampos encontrados:", encontrados)

print("\nInspeccion finalizada.")
