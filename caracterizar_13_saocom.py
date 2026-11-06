from pathlib import Path
import zipfile
import io
import xml.etree.ElementTree as ET
import pandas as pd

carpeta = Path(
    r"C:\Users\Usuario\OneDrive\Documentos\La_Rosaura_SAOCOM_2024_25"
)

registros = []

for producto in sorted(carpeta.glob("EOL1DSARSAO1A*.zip")):
    with zipfile.ZipFile(producto) as z1:
        interno = next(
            n for n in z1.namelist()
            if n.lower().endswith(".zip")
        )

        with zipfile.ZipFile(io.BytesIO(z1.read(interno))) as z2:
            nombre = next(
                n for n in z2.namelist()
                if n.startswith("Data/")
                and n.lower().endswith("-hh-m.xml")
            )

            raiz = ET.fromstring(z2.read(nombre))

            def obtener(etiqueta):
                for elemento in raiz.iter():
                    if elemento.tag.split("}")[-1] == etiqueta:
                        return (elemento.text or "").strip()
                return None

            registros.append({
                "producto": producto.stem,
                "fecha": obtener("SenseDate"),
                "modo": obtener("AcquisitionMode"),
                "swath": obtener("Swath"),
                "paso_x_m": obtener("SamplesStep"),
                "paso_y_m": obtener("LinesStep"),
                "filas": obtener("Lines"),
                "columnas": obtener("Samples"),
                "proyeccion": obtener("Projection")
            })

df = pd.DataFrame(registros)

print("\n=== INVENTARIO ESPACIAL SAOCOM ===")
print(df.to_string(index=False))

print("\n=== MODOS DE ADQUISICION ===")
print(df["modo"].value_counts(dropna=False))

print("\n=== ESPACIAMIENTOS DISTINTOS ===")
print(
    df[["paso_x_m", "paso_y_m"]]
    .drop_duplicates()
    .to_string(index=False)
)

salida = Path("data/metadata/caracterizacion_espacial_saocom.csv")
salida.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(salida, index=False, encoding="utf-8-sig")

print("\nArchivo generado:", salida)
