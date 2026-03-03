import random
from datetime import datetime, timedelta
from pymongo import MongoClient

print("Conectando a MongoDB Atlas...")

# Tu cadena de conexión exacta
MONGO_URI = "mongodb+srv://admin_clod:15dpr1843W@pruebas.wxrrszb.mongodb.net/?appName=pruebas"
client = MongoClient(MONGO_URI)
db = client["carga_mental_db"]

usuarios_col = db["usuarios"]
tareas_col = db["tareas"]

# 1. Obtener los usuarios reales que ya tienes creados
usuarios_db = list(usuarios_col.find({"rol": "usuario"}))
nombres_usuarios = [u["nombre_usuario"] for u in usuarios_db]

if not nombres_usuarios:
    print("❌ Error: No tienes usuarios creados. Crea al menos un usuario normal en el panel admin primero.")
    exit()

print(f"Usuarios encontrados: {nombres_usuarios}")
print("Generando 100 tareas aleatorias...")

# Datos falsos para combinar
titulos = [
    "Revisar métricas de carga", "Optimización de base de datos", "Auditoría de seguridad",
    "Redactar reporte mensual", "Reunión de planificación", "Actualizar servidores",
    "Evaluación de estrés laboral", "Mantenimiento preventivo", "Soporte a cliente",
    "Documentación técnica", "Revisión de inventario", "Configuración de red"
]
estados = ["Pendiente", "Completada"]
prioridades = ["Baja", "Media", "Alta"]

nuevas_tareas = []

for i in range(1, 101):
    # Seleccionar 1 o 2 usuarios al azar
    num_usuarios = random.randint(1, min(2, len(nombres_usuarios)))
    asignados = random.sample(nombres_usuarios, num_usuarios)
    
    # Generar una fecha aleatoria dentro de los últimos 30 días (para llenar el calendario)
    dias_restar = random.randint(0, 30)
    horas_restar = random.randint(0, 23)
    fecha_random = datetime.now() - timedelta(days=dias_restar, hours=horas_restar)
    
    # Hacemos que haya más completadas (60%) que pendientes (40%) para que la gráfica se vea positiva
    estado_random = random.choices(estados, weights=[40, 60])[0]

    tarea = {
        "titulo": f"{random.choice(titulos)} - {i}",
        "descripcion": "Tarea generada automáticamente para pruebas de volumen y visualización de carga mental.",
        "usuarios": asignados,
        "estado": estado_random,
        "prioridad": random.choice(prioridades),
        "fecha_creacion": fecha_random
    }
    
    nuevas_tareas.append(tarea)

# 2. Inyectar todo de golpe a MongoDB
tareas_col.insert_many(nuevas_tareas)

print("✅ ¡Éxito! 100 tareas han sido inyectadas en la nube.")
print("Ve a tu panel de administrador de Tassflow y recarga la página.")