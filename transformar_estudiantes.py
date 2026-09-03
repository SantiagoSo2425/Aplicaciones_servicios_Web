import csv
import json
from pathlib import Path

# Definir la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Definir rutas de los archivos
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"
RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"


def transformar_estudiante(fila: dict) -> dict:
    """Transforma un registro individual del CSV a la estructura de salida requerida."""
    # Convertir 'true'/'false' (texto) a 'Activo'/'Inactivo'
    activo_str = fila.get("activo", "").strip().lower()
    estado = "Activo" if activo_str in ("true", "1", "yes") else "Inactivo"

    return {
        "id": fila.get("codigo"),
        "nombre_completo": f"{fila.get('nombre', '').strip()} {fila.get('apellido', '').strip()}",
        "semestre": int(fila["semestre"]) if fila.get("semestre") and fila["semestre"].isdigit() else 0,
        "promedio": float(fila["promedio"]) if fila.get("promedio") else 0.0,
        "estado": estado
        # Nota: 'correo' se excluye deliberadamente
    }


def leer_y_transformar_csv(ruta: Path) -> list[dict]:
    """Lee el CSV completo y transforma todos sus registros en una lista de diccionarios."""
    estudiantes_transformados = []

    if not ruta.exists():
        print(f"Error: No se encontró el archivo CSV en {ruta}")
        return estudiantes_transformados

    with open(ruta, mode="r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            estudiante_procesado = transformar_estudiante(fila)
            estudiantes_transformados.append(estudiante_procesado)

    return estudiantes_transformados


def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)


def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


# --- FLUJO PRINCIPAL DE EJECUCIÓN ---
if __name__ == "__main__":
    print("Hola, Aplicaciones y Servicios Web")

    # 1 y 2. Leer CSV y 3, 4, 5. Transformar registros
    estudiantes_transformados = leer_y_transformar_csv(RUTA_CSV)

    if estudiantes_transformados:
        # 6. Serializar y guardar el JSON
        serializar_estudiantes(RUTA_JSON, estudiantes_transformados)
        print(f"Archivo JSON generado: {RUTA_JSON}")

        # 7. Deserializar el JSON generado y mostrar resultados
        estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)

        print("\nDatos recuperados desde el JSON:")
        print(estudiantes_recuperados[0])
        print(f"Total recuperado: {len(estudiantes_recuperados)}")
    else:
        print("No se procesaron registros. Verifica el contenido de tu archivo CSV.")
