from pathlib import Path
import zipfile
import io

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

producto = sorted(carpeta.glob("EOL1DSARSAO1A*.zip"))[0]

print("PRODUCTO:", producto.name)

with zipfile.ZipFile(producto) as z1:
    print("\nARCHIVOS EXTERNOS:")
    for nombre in z1.namelist():
        print(" ", nombre)

    internos = [
        n for n in z1.namelist()
        if n.lower().endswith(".zip")
    ]

    if len(internos) != 1:
        raise RuntimeError(
            f"Se esperaba un ZIP interno; encontrados: {len(internos)}"
        )

    with zipfile.ZipFile(io.BytesIO(z1.read(internos[0]))) as z2:
        print("\nARCHIVOS XML INTERNOS:")
        xmls = [
            n for n in z2.namelist()
            if n.lower().endswith(".xml")
        ]

        for nombre in xmls:
            print(" ", nombre)

        print("\nTotal XML internos:", len(xmls))
