from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)
app.secret_key = "secreto"


# ARCHIVOS
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MONGO

MONGO_URI = "mongodb+srv://admin_clod:15dpr1843W@pruebas.wxrrszb.mongodb.net/?appName=pruebas"
client = MongoClient(MONGO_URI)

db = client["carga_mental_db"]
usuarios_col = db["usuarios"]
tareas_col = db["tareas"]
mensajes_col = db["mensajes"]
documentos_col = db["documentos"]

# LOGIN

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = usuarios_col.find_one({
            "nombre_usuario": request.form["usuario"],
            "contrasena": request.form["contrasena"],
            "activo": True
        })

        if not user:
            return render_template("login.html", error="Credenciales incorrectas")

        session.clear()
        session["usuario"] = user["nombre_usuario"]
        session["rol"] = user["rol"]

        return redirect(
            url_for("admin_panel" if user["rol"] == "admin" else "usuario_panel")
        )

    return render_template("login.html")

# ADMIN

@app.route("/admin")
def admin_panel():
    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    return render_template(
        "admin_panel.html",
        usuarios=list(usuarios_col.find({"rol": "usuario"})),
        tareas=list(tareas_col.find()),
        total_usuarios=usuarios_col.count_documents({"rol": "usuario"}),
        total_tareas=tareas_col.count_documents({}),
        tareas_pendientes=tareas_col.count_documents({"estado": "Pendiente"}),
        tareas_completadas=tareas_col.count_documents({"estado": "Completada"})
    )


# CREAR / ELIMINAR USUARIO

@app.route("/crear_usuario", methods=["POST"])
def crear_usuario():
    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    password = request.form["contrasena"]
    
    # REGLA: Mínimo 8 caracteres, 1 Mayúscula, 1 Número y 1 Caracter Especial
    regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    
    if not re.match(regex, password):
        flash("La contraseña debe tener: 8 caracteres, una mayúscula, un número y un símbolo (@$!%*?&).")
        return redirect(url_for("admin_panel"))

    usuarios_col.insert_one({
        "nombre_usuario": request.form["usuario"],
        "contrasena": password,
        "rol": "usuario",
        "activo": True,
        "solicitud_reset": False # Nueva bandera para recuperación
    })
    return redirect(url_for("admin_panel"))

@app.route("/eliminar_usuario/<id>")
def eliminar_usuario(id):
    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    usuario = usuarios_col.find_one({"_id": ObjectId(id)})
    if usuario:
        tareas_col.update_many(
            {},
            {"$pull": {"usuarios": usuario["nombre_usuario"]}}
        )
        usuarios_col.delete_one({"_id": ObjectId(id)})

    return redirect(url_for("admin_panel"))


# ASIGNAR TAREA
@app.route("/asignar_tarea", methods=["POST"])
def asignar_tarea():
    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    usuarios = request.form.getlist("usuarios")
    if not (1 <= len(usuarios) <= 2):
        flash("Selecciona 1 o 2 usuarios")
        return redirect(url_for("admin_panel"))

    tareas_col.insert_one({
        "titulo": request.form["titulo"],
        "descripcion": request.form["descripcion"],
        "usuarios": usuarios,
        "estado": "Pendiente",
        "prioridad": "Media",
        "fecha_creacion": datetime.now()
    })

    return redirect(url_for("admin_panel"))


# USUARIO

@app.route("/usuario")
def usuario_panel():
    if session.get("rol") != "usuario":
        return redirect(url_for("login"))

    tareas = list(tareas_col.find({"usuarios": session["usuario"]}))

    pendientes = sum(1 for t in tareas if t["estado"] == "Pendiente")
    completadas = sum(1 for t in tareas if t["estado"] == "Completada")
    total = len(tareas)

    progreso = int((completadas / total) * 100) if total > 0 else 0

    #calendario
    for t in tareas:
        if isinstance(t.get("fecha_creacion"), datetime):
            t["fecha_creacion"] = t["fecha_creacion"].strftime("%Y-%m-%d")

    return render_template(
        "usuario_panel.html",
        tareas=tareas,
        pendientes=pendientes,
        completadas=completadas,
        progreso=progreso
    )
# CALENDARIO USUARIO

@app.route("/usuario/calendario")
def usuario_calendario():

    if session.get("rol") != "usuario":
        return redirect(url_for("login"))

    tareas = list(tareas_col.find({
        "usuarios": session["usuario"]
    }))

    eventos = []

    for t in tareas:

        fecha = t.get("fecha_creacion")

        if fecha:

            # convertir datetime Mongo a string YYYY-MM-DD
            fecha_str = fecha.strftime("%Y-%m-%d")

            eventos.append({
                "title": t.get("titulo", "Sin título"),
                "start": fecha_str,
                "allDay": True,
                "color": "#22c55e" if t.get("estado") == "Completada" else "#3b82f6"
            })

    print(eventos)  # DEBUG

    return render_template(
        "usuario_calendario.html",
        eventos=eventos
    )

# ESTADISTICAS USUARIO

@app.route("/usuario/estadisticas")
def usuario_estadisticas():

    if session.get("rol") != "usuario":
        return redirect(url_for("login"))

    tareas = list(tareas_col.find({"usuarios": session["usuario"]}))

    completadas = sum(1 for t in tareas if t.get("estado") == "Completada")
    pendientes = sum(1 for t in tareas if t.get("estado") != "Completada")
    total = len(tareas)

    return render_template(
        "usuario_estadisticas.html",
        completadas=completadas,
        pendientes=pendientes,
        total=total
    )

# CAMBIOS DE TAREA

@app.route("/cambiar_prioridad/<id>", methods=["POST"])
def cambiar_prioridad(id):
    tareas_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"prioridad": request.form["prioridad"]}}
    )
    return redirect(url_for("usuario_panel"))

@app.route("/completar_tarea/<id>")
def completar_tarea(id):
    tareas_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": "Completada"}}
    )
    return redirect(url_for("usuario_panel"))


# CHAT

@app.route("/chat/<tarea_id>")
def ver_chat(tarea_id):
    tarea = tareas_col.find_one({"_id": ObjectId(tarea_id)})
    mensajes = list(
        mensajes_col.find({"tarea_id": ObjectId(tarea_id)})
        .sort("fecha", 1)
    )

    return render_template("chat.html", tarea=tarea, mensajes=mensajes)

@app.route("/enviar_mensaje/<tarea_id>", methods=["POST"])
def enviar_mensaje(tarea_id):
    archivo = request.files.get("archivo")

    mensaje = {
        "tarea_id": ObjectId(tarea_id),
        "usuario": session["usuario"],
        "texto": request.form.get("mensaje"),
        "fecha": datetime.now(),
        "archivo": None
    }

    if archivo and archivo.filename:
        nombre = secure_filename(archivo.filename)
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre)
        archivo.save(ruta)
        mensaje["archivo"] = {
            "nombre": nombre,
            "tipo": archivo.content_type,
            "url": f"/static/uploads/{nombre}"
        }

    mensajes_col.insert_one(mensaje)
    return redirect(url_for("ver_chat", tarea_id=tarea_id))


# DOCUMENTOS

@app.route("/solicitar_documento/<tarea_id>", methods=["POST"])
def solicitar_documento(tarea_id):
    documentos_col.insert_one({
        "tarea_id": ObjectId(tarea_id),
        "nombre_documento": request.form["nombre_documento"],
        "descripcion": request.form["descripcion"],
        "usuario": session["usuario"],
        "estado": "Pendiente",
        "archivo": None,
        "fecha": datetime.now()
    })
    return redirect(url_for("usuario_panel"))

@app.route("/mis_documentos")
def mis_documentos():
    docs = list(documentos_col.find({"usuario": session["usuario"]}))
    return render_template("mis_documentos.html", documentos=docs)

@app.route("/subir_documento/<id>", methods=["POST"])
def subir_documento(id):
    archivo = request.files["archivo"]
    nombre = secure_filename(archivo.filename)
    ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre)
    archivo.save(ruta)

    documentos_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "archivo": nombre,
            "estado": "Subido",
            "fecha_subida": datetime.now()
        }}
    )

    return redirect(url_for("mis_documentos"))


@app.route("/obtener_mensajes/<tarea_id>")
def obtener_mensajes(tarea_id):
    # Usar la colección ya inicializada y convertir ObjectId/fechas
    try:
        mensajes = list(
            mensajes_col.find({"tarea_id": ObjectId(tarea_id)}).sort("fecha", 1)
        )
    except Exception:
        mensajes = list(
            mensajes_col.find({"tarea_id": tarea_id}).sort("fecha", 1)
        )

    lista = []

    for m in mensajes:
        archivo = None
        if m.get("archivo"):
            if isinstance(m["archivo"], dict):
                archivo = {
                    "url": m["archivo"].get("url"),
                    "nombre": m["archivo"].get("nombre"),
                    "tipo": m["archivo"].get("tipo")
                }
            else:
                archivo = {
                    "url": f"/static/uploads/{m['archivo']}",
                    "nombre": m["archivo"],
                    "tipo": None
                }

        fecha = m.get("fecha")
        if isinstance(fecha, datetime):
            fecha = fecha.isoformat()

        lista.append({
            "usuario": m.get("usuario"),
            "texto": m.get("texto"),
            "archivo": archivo,
            "fecha": fecha
        })

    return jsonify(lista)

@app.route("/olvide_password", methods=["GET", "POST"])
def olvide_password():
    if request.method == "POST":
        username = request.form["usuario"]
        user = usuarios_col.find_one({"nombre_usuario": username})
        if user:
            usuarios_col.update_one({"_id": user["_id"]}, {"$set": {"solicitud_reset": True}})
            flash("Solicitud enviada al administrador.")
        return redirect(url_for("login"))
    return render_template("olvide_password.html")

@app.route("/resetear_password/<id>", methods=["POST"])
def resetear_password(id):
    if session.get("rol") != "admin": return redirect(url_for("login"))
    
    nueva_clave = request.form["nueva_clave"]
    
    regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    if not re.match(regex, nueva_clave):
        flash("Error: La nueva contraseña debe tener 8 caracteres, una mayúscula, un número y un símbolo.")
        return redirect(url_for("admin_panel"))

    usuarios_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"contrasena": nueva_clave, "solicitud_reset": False}}
    )
    flash("Contraseña actualizada con éxito.")
    return redirect(url_for("admin_panel"))

@app.route('/eliminar_tarea/<tarea_id>')
def eliminar_tarea(tarea_id):
    if session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    from bson.objectid import ObjectId
    # Eliminamos la tarea de la colección 'tareas'
    db.tareas.delete_one({'_id': ObjectId(tarea_id)})
    
    # Opcional: También podrías eliminar los mensajes asociados a esa tarea
    db.mensajes.delete_many({'tarea_id': tarea_id})
    
    flash("Tarea eliminada correctamente.")
    return redirect(url_for('admin_panel'))


# LOGOUT

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# RUN
if __name__ == "__main__":
    import os
    port=int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
