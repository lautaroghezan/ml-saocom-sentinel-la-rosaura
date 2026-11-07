from pathlib import Path
import nbformat
from nbclient import NotebookClient

ruta = Path("notebooks/analisis_final_L15_L16.ipynb")

print("\n=== PASO 20B: VALIDACION DEL NOTEBOOK ===")

if not ruta.exists():
    raise FileNotFoundError(f"No existe: {ruta}")

notebook = nbformat.read(ruta, as_version=4)

nbformat.validate(notebook)

print("Estructura del notebook: VALIDA")
print("Celdas:", len(notebook.cells))

cliente = NotebookClient(
    notebook,
    timeout=300,
    kernel_name="python3",
    resources={
        "metadata": {
            "path": str(Path.cwd().resolve())
        }
    }
)

print("\nEjecutando todas las celdas...")
cliente.execute()

errores = []

for i, celda in enumerate(notebook.cells, start=1):
    if celda.cell_type != "code":
        continue

    for salida in celda.get("outputs", []):
        if salida.output_type == "error":
            errores.append({
                "celda": i,
                "error": salida.get("ename"),
                "mensaje": salida.get("evalue")
            })

if errores:
    print("\nERRORES DETECTADOS:")
    for error in errores:
        print(error)
    raise RuntimeError("El notebook contiene errores.")

nbformat.write(notebook, ruta)

print("\n=== VALIDACION FINAL ===")
print("Notebook ejecutado: SI")
print("Errores:", len(errores))
print("Archivo actualizado:", ruta)
print("Estado: APROBADO")
