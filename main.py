from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional


app = FastAPI()
dataset_estudiantes: list[list] = []


class Estudiante(BaseModel):
    id: int
    nombre: str
    edad: int
    programa: str


@app.get("/")
def read_root():
    return {"message": "Hola mundo"}


def buscar_por_id(id: int) -> Optional[list]:
    for registro in dataset_estudiantes:
        if registro[0] == id:
            return registro
    return None


@app.post("/estudiantes")
def agregar_estudiante(estudiante: Estudiante):
    if buscar_por_id(estudiante.id) is not None:
        return {"error": "Ya existe un estudiante con ese id"}

    estudiante_como_lista = [
        estudiante.id,
        estudiante.nombre,
        estudiante.edad,
        estudiante.programa,
    ]
    dataset_estudiantes.append(estudiante_como_lista)

    print("Dataset de estudiantes:")
    for registro in dataset_estudiantes:
        print(registro)

    return {
        "message": "Estudiante agregado correctamente",
        "estudiante": estudiante_como_lista,
        "dataset": dataset_estudiantes,
    }


@app.get("/estudiantes/{id}")
def obtener_estudiante(id: int):
    registro = buscar_por_id(id)
    if registro is None:
        return {"error": "Estudiante no encontrado"}

    return {
        "estudiante": {
            "id": registro[0],
            "nombre": registro[1],
            "edad": registro[2],
            "programa": registro[3],
        }
    }


class EstudianteActualizacion(BaseModel):
    nombre: Optional[str] = None
    edad: Optional[int] = None
    programa: Optional[str] = None


def imprimir_dataset():
    print("Dataset de estudiantes:")
    for registro in dataset_estudiantes:
        print(registro)


@app.put("/estudiantes/{indice}")
def reemplazar_estudiante(indice: int, estudiante: Estudiante):
    if indice < 0 or indice >= len(dataset_estudiantes):
        return {"error": "El estudiante no existe"}

    otro = buscar_por_id(estudiante.id)
    if otro is not None and otro is not dataset_estudiantes[indice]:
        return {"error": "Ya existe un estudiante con ese id"}

    dataset_estudiantes[indice] = [
        estudiante.id,
        estudiante.nombre,
        estudiante.edad,
        estudiante.programa,
    ]
    imprimir_dataset()

    return {
        "message": "Estudiante reemplazado correctamente",
        "estudiante": dataset_estudiantes[indice],
        "dataset": dataset_estudiantes,
    }


@app.patch("/estudiantes/{indice}")
def actualizar_estudiante_parcial(
    indice: int, estudiante: EstudianteActualizacion
):
    if indice < 0 or indice >= len(dataset_estudiantes):
        return {"error": "El estudiante no existe"}

    datos_actualizados = estudiante.model_dump(exclude_unset=True)
    campos = {"nombre": 1, "edad": 2, "programa": 3}

    for campo, valor in datos_actualizados.items():
        dataset_estudiantes[indice][campos[campo]] = valor

    imprimir_dataset()

    return {
        "message": "Estudiante actualizado correctamente",
        "estudiante": dataset_estudiantes[indice],
        "dataset": dataset_estudiantes,
    }


@app.delete("/estudiantes/{indice}")
def eliminar_estudiante(indice: int):
    if indice < 0 or indice >= len(dataset_estudiantes):
        return {"error": "El estudiante no existe"}

    estudiante_eliminado = dataset_estudiantes.pop(indice)
    imprimir_dataset()

    return {
        "message": "Estudiante eliminado correctamente",
        "estudiante": estudiante_eliminado,
        "dataset": dataset_estudiantes,
    }
