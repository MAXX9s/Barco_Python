import bcrypt
from flask import Blueprint, render_template, request
import sqlite3
from flask_login import login_required, current_user
from app.db import get_db_connection
from app import bcrypt

db = Blueprint("db", __name__, template_folder="templates")
main = Blueprint("main", __name__, template_folder="templates")
program = Blueprint("program", __name__, template_folder="templates")


 
@db.route("/users")
def users():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    usuario = conn.execute("SELECT * FROM usuario").fetchall()
    conn.close()
    return render_template("users_list.html", usuario=usuario)

@main.route("/")
def index():
    nombre = getattr(current_user, "username", "Invitado")
    return render_template("index.html", nombre=nombre)


@main.route("/main-program-view/<string:name_user>")
def main_program_view(name_user):
    return render_template("main-program-view.html", name_user=name_user)


@main.route("/profile")
@login_required
def profile():
    
    if not hasattr(current_user, 'tipo') or not current_user.tipo:
        return "Error: usuario sin tipo definido", 500
    
    tipo = current_user.tipo.strip().lower()


    if  tipo == "administrador":
        return render_template("admin/profileadmin.html", user_id=current_user.id)
    elif tipo == "encargado de envios":
        return render_template("envios/profileenvios.html", user_id=current_user.id)
    elif tipo == "encargado de barcos":
        return render_template("barcos/profilebarcos.html", user_id=current_user.id)
    elif tipo == "cliente":
        return render_template("index.html", user_id=current_user.id)
    else:
        return 'Rol desconocido'

# FORMULARIO (GET)
@main.route("/form", methods=["GET"])
def form():
    return render_template("form.html")




# PROCESAR FORMULARIO (POST)

@main.route("/submit", methods=["POST"])
def submit():
    name        = request.form.get("name", "").strip()
    last_name   = request.form.get("last_name", "").strip()
    email       = request.form.get("email", "").strip()
    birth_date  = request.form.get("birth_date", "").strip()
    telephone   = request.form.get("telephone", "").strip()
    address     = request.form.get("address", "").strip()
    password    = request.form.get("password", "").strip()
    tipo_usuario= request.form.get("type_user", "").strip() or "Usuario"

    if not name or not password:
        return "Faltan campos obligatorios (name / password)", 400
    try:
        tel_int = int(telephone) if telephone else 0
    except ValueError:
        return "Teléfono inválido", 400
    if not birth_date:
        birth_date = "2000-01-01"  

    try:
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    except Exception:
        hashed_pw = password
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        conn.execute("""
                INSERT INTO usuario (nombre, apellido, contrasena, email, fecha_nacimiento, direccion, telefono, tipo_usuario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, last_name, hashed_pw, email, birth_date, address, tel_int, tipo_usuario))

        conn.commit()
    except Exception as e:
        return f"Error guardando en la base de datos: {e}", 500
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    return render_template(
        "login.html",
    )
# ERROR 404
@main.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404