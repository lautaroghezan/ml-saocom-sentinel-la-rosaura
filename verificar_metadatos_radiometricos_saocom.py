from pathlib import Path
import zipfile
import io
import xml.etree.ElementTree as ET

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = carpeta / "EOL1DSARSAO1A14056208.zip"

terminos = [
    "sigma",
    "calibr",
    "noise",
    "nesz",
    "amplitude",
    "radiometric",
    "beta",
    "gamma"
]

with zipfile.ZipFile(producto) as exterior:

    internos = [
        n for n in exterior.namelist()
        if n.lower().endswith(".zip")
    ]

    if len(internos) != 1:
        raise ValueError("No se encontro un unico ZIP interno.")

    with zipfile.ZipFile(io.BytesIO(exterior.read(internos[0]))) as interior:

        for pol in ["hh", "hv", "vh", "vv"]:

            candidatos = [
                n for n in interior.namelist()
                if n.lower().startswith("data/")
                and n.lower().endswith(f"-{pol}-m.xml")
            ]

            if len(candidatos) != 1:
                raise ValueError(
                    f"XML {pol.upper()}: {len(candidatos)} encontrados"
                )

            print("\n" + "=" * 55)
            print("POLARIZACION:", pol.upper())
            print("XML:", candidatos[0])
            print("=" * 55)

            contenido = interior.read(candidatos[0])
            raiz = ET.fromstring(contenido)

            encontrados = []

            for elemento in raiz.iter():

                etiqueta = elemento.tag.split("}")[-1]
                valor = (elemento.text or "").strip()

                if any(
                    termino in etiqueta.lower()
                    for termino in terminos
                ):
                    if valor and len(valor) < 300:
                        encontrados.append((etiqueta, valor))

            if encontrados:
                for etiqueta, valor in encontrados:
                    print(f"{etiqueta}: {valor}")
            else:
                print("Sin campos coincidentes.")

print("\nInspeccion de metadatos finalizada.")
