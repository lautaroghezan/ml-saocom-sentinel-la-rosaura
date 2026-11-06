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

            x = float(obtener("SamplesStart"))
            y = float(obtener("LinesStart"))
            dx = float(obtener("SamplesStep"))
            dy = float(obtener("LinesStep"))

            columnas = int(obtener("Samples"))
            filas = int(obtener("Lines"))

            registros.append({
                "producto": producto.stem,
                "fecha": obtener("SenseDate"),
                "origen_x": round(x, 2),
                "origen_y": round(y, 2),
                "paso_x": round(dx, 3),
                "paso_y": round(dy, 3),
                "limite_x": round(x + columnas * dx, 2),
                "limite_y": round(y + filas * dy, 2),
                "proyeccion_parametros": obtener("ProjectionParameters")
            })

df = pd.DataFrame(registros)

print("\n=== ALINEACION ESPACIAL SAOCOM ===")
print(
    df.drop(columns="proyeccion_parametros")
    .to_string(index=False)
)

print("\n=== ORIGENES ESPACIALES DISTINTOS ===")
print(df[["origen_x", "origen_y"]].drop_duplicates().shape[0])

print("\n=== PARAMETROS DE PROYECCION DISTINTOS ===")
print(df["proyeccion_parametros"].nunique())

print("\n=== PARAMETROS DE PROYECCION ===")
for valor in df["proyeccion_parametros"].drop_duplicates():
    print(valor)

salida = Path("data/metadata/alineacion_espacial_saocom.csv")
salida.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(salida, index=False, encoding="utf-8-sig")

print("\nArchivo generado:", salida)
