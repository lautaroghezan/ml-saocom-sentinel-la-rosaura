from pathlib import Path
import zipfile
import io
import xml.etree.ElementTree as ET

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = sorted(carpeta.glob("EOL1DSARSAO1A*.zip"))[0]

with zipfile.ZipFile(producto) as z1:
    interno = next(
        n for n in z1.namelist()
        if n.lower().endswith(".zip")
    )

    with zipfile.ZipFile(io.BytesIO(z1.read(interno))) as z2:

        nombre = next(
            n for n in z2.namelist()
            if n.startswith("Data/")
            and n.endswith("-hh-m.xml")
        )

        raiz = ET.fromstring(z2.read(nombre))

        print("PRODUCTO:", producto.name)
        print("XML:", nombre)
        print("\nESTRUCTURA Y VALORES:")

        contador = 0

        def recorrer(elemento, nivel=0):
            global contador

            if contador >= 180:
                return

            etiqueta = elemento.tag.split("}")[-1]
            valor = (elemento.text or "").strip()

            if len(valor) > 120:
                valor = valor[:120] + "..."

            print("  " * nivel + etiqueta +
                  (f": {valor}" if valor else ""))

            contador += 1

            for hijo in elemento:
                recorrer(hijo, nivel + 1)

        recorrer(raiz)

        print("\nElementos mostrados:", contador)
