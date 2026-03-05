import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

print("Conectando a MongoDB Atlas...")
client = MongoClient(MONGO_URI)
db = client["carga_mental_db"]

print("Destruyendo el millón de tareas (Drop)...")

db["tareas"].drop()

print("✅ ¡Limpieza completada al instante!")
print("Tu base de datos está vacía y lista para usarse de nuevo.")