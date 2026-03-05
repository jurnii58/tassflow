import os
import sys


os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
os.environ['SPARK_LOCAL_IP'] = '127.0.0.1'

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder \
    .appName("MonitoreoSeguridadTaskFlow") \
    .master("local[*]") \
    .config("spark.driver.host", "127.0.0.1") \
    .config("spark.driver.bindAddress", "127.0.0.1") \
    .getOrCreate()

datos = [
    ("192.168.1.10", "admin", "OK", 1),
    ("192.168.1.11", "hector", "FAIL", 3),
    ("192.168.1.11", "hector", "FAIL", 4),
    ("192.168.1.50", "root", "FAIL", 6),       
    ("192.168.1.50", "admin", "FAIL", 7),      
    ("192.168.1.15", "usuario_comun", "OK", 1),
    ("192.168.1.99", "admin", "FAIL", 8),      
    ("192.168.1.10", "admin", "OK", 1)
]

columnas = ["ip", "usuario", "estatus", "intentos"]
df = spark.createDataFrame(datos, columnas)

print("\n=== LOGS GENERADOS (ACCESOS A TASKFLOW) ===")
df.show()

fallidos = df.filter(col("estatus") == "FAIL")
print("\n=== INTENTOS FALLIDOS ===")
fallidos.show()

sospechosos = fallidos.filter(col("intentos") > 5)
print("\n=== POSIBLES ATAQUES DETECTADOS (ALERTA DE SEGURIDAD) ===")
sospechosos.show()

print("\n=== CLASIFICACIÓN DE RIESGO ===")
print("Las IPs mostradas arriba deben ser bloqueadas por el Firewall de TaskFlow.")