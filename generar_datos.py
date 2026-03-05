import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["carga_mental_db"]
tareas_col = db["tareas"]
usuarios_col = db["usuarios"]

usuarios_db = list(usuarios_col.find({"rol": "usuario"}))
nombres_usuarios = [u["nombre_usuario"] for u in usuarios_db]

if not nombres_usuarios:
    nombres_usuarios = ['juan', 'israel', 'luis', 'Sara']

print(f"Usuarios encontrados: {nombres_usuarios}")
print("\n=== INICIANDO INGESTA MASIVA: 1 MILLÓN DE REGISTROS ===")

titulos = ["Revisar métricas", "Optimización BD", "Auditoría", "Reporte mensual", "Actualizar servidores"]
estados = ["Pendiente", "En Proceso", "Completada"]
prioridades = ["Alta", "Media", "Baja"]

TOTAL_REGISTROS = 1000000
TAMANO_LOTE = 10000
lotes_totales = TOTAL_REGISTROS // TAMANO_LOTE

print(f"Se insertarán en {lotes_totales} lotes de {TAMANO_LOTE} registros cada uno para no asfixiar la RAM.\n")

for lote in range(lotes_totales):
    lote_tareas = []
    
    for i in range(TAMANO_LOTE):
        tarea = {
            "titulo": f"{random.choice(titulos)} #{i + (lote * TAMANO_LOTE)}",
            "descripcion": "Tarea generada por script de estrés masivo.",
            "usuarios": [random.choice(nombres_usuarios)],
            "estado": random.choice(estados),
            "prioridad": random.choice(prioridades),
            "fecha_creacion": datetime.now() - timedelta(days=random.randint(0, 365))
        }
        lote_tareas.append(tarea)
    
    tareas_col.insert_many(lote_tareas, ordered=False)
    
    del lote_tareas 
    
    print(f" Lote {lote + 1}/{lotes_totales} subido ({(lote + 1) * TAMANO_LOTE} tareas en la nube).")

print("\nCreando índices para búsquedas rápidas...")
tareas_col.create_index("estado")
tareas_col.create_index("prioridad")

print("\n ¡ÉXITO! 1 Millón de tareas inyectadas en MongoDB Atlas.")