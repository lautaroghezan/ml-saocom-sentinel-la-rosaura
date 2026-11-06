from pathlib import Path
import zipfile
import io
import xml.etree.ElementTree as ET

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = carpeta / "EOL1DSARSAO1A14056208.zip"

terminos = [
    "sigma0",
    "sigma",
    "calibr",
    "noise",
    "nesz",
    "amplitude",
    "radiometric",
    "beta0",
    "gamma0"
]

resultados = []

with zipfile.ZipFile(producto) as exterior:

    internos = [
        n for n in exterior.namelist()
        if n.lower().endswith(".zip")
    ]

    if len(internos) != 1:
        raise ValueError("Se esperaba un unico ZIP interno.")

    with zipfile.ZipFile(io.BytesIO(exterior.read(internos[0]))) as interior:

        archivos = [
            n for n in interior.namelist()
            if n.lower().endswith(".xml")
        ]

        print("XML encontrados:", len(archivos))

        for nombre in archivos:

            try:
                raiz = ET.fromstring(interior.read(nombre))
            except ET.ParseError:
                continue

            for elemento in raiz.iter():

                etiqueta = elemento.tag.split("}")[-1]
                valor = (elemento.text or "").strip()

                atributos = " ".join(
                    f"{k}={v}"
                    for k, v in elemento.attrib.items()
                )

                contenido = (
                    etiqueta + " " + valor + " " + atributos
                ).lower()

                if any(t in contenido for t in terminos):

                    if len(valor) > 180:
                        valor = valor[:180] + "..."

                    resultados.append(
                        (nombre, etiqueta, valor, atributos[:180])
                    )

print("\n=== COINCIDENCIAS RADIOMETRICAS ===")
print("Total de coincidencias:", len(resultados))

for nombre, etiqueta, valor, atributos in resultados[:80]:
    print("\nArchivo:", nombre)
    print("Campo:", etiqueta)
    print("Valor:", valor)

    if atributos:
        print("Atributos:", atributos)

if len(resultados) > 80:
    print(
        "\nCoincidencias adicionales no mostradas:",
        len(resultados) - 80
    )
