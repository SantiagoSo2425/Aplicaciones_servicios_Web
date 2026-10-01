from fastapi import FastAPI


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hola mundo"}


@app.get("/saludo/{nombre}")
def saludar(nombre: str, idioma: str = "es"):
    saludos = {"es": "Hola", "en": "Hello", "fr": "Bonjour"}
    saludo = saludos.get(idioma, saludos["es"])
    return {"message": f"{saludo} {nombre}"}
