from pathlib import Path
import zipfile
import io
import xml.etree.ElementTree as ET

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = sorted(carpeta.glob("EOL1DSARSAO1A*.zip"))[0]

palabras = (
    "resolution",
    "spacing",
    "look",
    "groundrange",
    "slant",
    "azimuth",
    "bandwidth",
    "incidence",
    "sampling"
)

with zipfile.ZipFile(producto) as z1:
    interno = next(
        n for n in z1.namelist()
        if n.lower().endswith(".zip")
    )

    with zipfile.ZipFile(io.BytesIO(z1.read(interno))) as z2:

        archivos = [
            n for n in z2.namelist()
            if n.lower().endswith(".xml")
            and (
                n.startswith("Data/")
                or n in (
                    "Config/L1PROCConf.xml",
                    "Config/SPConf.xml",
                    "Config/parameterFile2.xml"
                )
            )
        ]

        for nombre in archivos:
            raiz = ET.fromstring(z2.read(nombre))
            resultados = []

            for elemento in raiz.iter():
                etiqueta = elemento.tag.split("}")[-1]
                valor = (elemento.text or "").strip()

                if (
                    any(p in etiqueta.lower() for p in palabras)
                    and valor
                    and len(valor) < 150
                ):
                    resultados.append((etiqueta, valor))

            if resultados:
                print("\nARCHIVO:", nombre)

                for etiqueta, valor in resultados:
                    print(f"  {etiqueta}: {valor}")
