import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("Falta la variable MONGO_URI en el archivo .env")

client = MongoClient(MONGO_URI)
db = client["carga_mental_db"]
logs_col = db["logs_acceso"]

print("\n=== INICIANDO SIMULACIÓN DE SEGURIDAD EXTREMA: 1 MILLÓN DE LOGS ===")

ips = ["192.168.1.10", "192.168.1.11", "192.168.1.50", "192.168.1.15", "192.168.1.99", "10.0.0.5"]
usuarios_lista = ["admin", "jurni", "hector", "root", "usuario_comun", "invitado"]
estados = ["OK", "FAIL"]

TOTAL_REGISTROS = 1000000
TAMANO_LOTE = 10000
lotes_totales = TOTAL_REGISTROS // TAMANO_LOTE

print(f"Se insertarán en {lotes_totales} lotes de {TAMANO_LOTE} registros cada uno.\n")

for lote in range(lotes_totales):
    logs_masivos = []
    
    for i in range(TAMANO_LOTE):
        ip_random = random.choice(ips)
        
        if ip_random in ["192.168.1.50", "192.168.1.99"]:
            estatus = "FAIL"
            usuario = random.choice(["admin", "root"])
            intentos = random.randint(6, 15) #
        else:
            estatus = random.choices(estados, weights=[80, 20])[0] 
            usuario = random.choice(usuarios_lista)
            intentos = random.randint(1, 3)

        log = {
            "ip": ip_random,
            "usuario": usuario,
            "estatus": estatus,
            "intentos": intentos,
            "fecha_intento": datetime.now() - timedelta(minutes=random.randint(0, 500000))
        }
        
        logs_masivos.append(log)

    logs_col.insert_many(logs_masivos, ordered=False)
    
    del logs_masivos 
    
    print(f"Lote {lote + 1}/{lotes_totales} subido ({(lote + 1) * TAMANO_LOTE} logs en la nube).")

print("\nCreando índices de seguridad en Mongo...")
logs_col.create_index("ip")
logs_col.create_index("estatus")

print("\n ¡ÉXITO! 1 Millón de intentos de login inyectados en MongoDB Atlas.")