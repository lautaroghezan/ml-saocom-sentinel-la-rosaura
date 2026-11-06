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
    "pixel",
    "acquisitionmode",
    "imagingmode",
    "swath",
    "groundrange",
    "azimuth"
)

with zipfile.ZipFile(producto) as z1:
    interno = next(
        n for n in z1.namelist()
        if n.lower().endswith(".zip")
    )

    with zipfile.ZipFile(io.BytesIO(z1.read(interno))) as z2:

        seleccionados = [
            n for n in z2.namelist()
            if n in (
                "Config/L1PROCConf.xml",
                "Config/SPConf.xml"
            )
            or (
                n.startswith("Data/")
                and n.endswith("-hh-m.xml")
            )
        ]

        for nombre in seleccionados:
            print("\n" + "=" * 65)
            print("ARCHIVO:", nombre)
            print("=" * 65)

            raiz = ET.fromstring(z2.read(nombre))
            encontrados = 0

            for elemento in raiz.iter():
                etiqueta = elemento.tag.split("}")[-1]
                valor = (elemento.text or "").strip()

                if any(p in etiqueta.lower() for p in palabras):
                    if valor and len(valor) < 200:
                        print(f"{etiqueta}: {valor}")
                        encontrados += 1

            print("Parametros encontrados:", encontrados)
