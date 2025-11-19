from flask import Blueprint, abort, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
from flask import g, current_app
from . import login_manager, bcrypt
import requests


from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENTE_GOOGLE_ID")
CLIENT_SECRET = os.getenv("CLIENTE_GOOGLE_SECRETO")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


auth = Blueprint("auth", __name__, template_folder="templates")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db

@auth.teardown_app_request
def close_db(exc):
    db = g.pop("db", None)
    if db: db.close()

class User(UserMixin):
    def __init__(self, id_usuario, nombre, contrasena, tipo_usuario):
        self.id = id_usuario
        self.username = nombre
        self.password_hash = contrasena
        self.tipo = tipo_usuario.strip().lower() if tipo_usuario else "cliente"

    @staticmethod
    def from_row(row):
        if row:
            return User(
                row["id_usuario"], 
                row["nombre"], 
                row["contrasena"], 
                row["tipo_usuario"]
            )
        return None

@login_manager.user_loader
def load_user(user_id):
    row = get_db().execute(
        "SELECT id_usuario, nombre, contrasena, tipo_usuario FROM usuario WHERE id_usuario = ?",
        (user_id,)
    ).fetchone()
    return User.from_row(row)

# --- Vistas GET (formularios) ---
@auth.get("/login")
def login_get():
    logout_user()
    return render_template("login.html")

@auth.get("/register")
def register_get():
    return render_template("register.html")

# --- POST login/registro ---
@auth.post("/register")
def register_post():
    username = request.form["username"].strip()
    password = request.form["password"]

    if not username or not password:
        flash("Todos los campos son obligatorios", "error")
        return render_template("register.html")

    exists = get_db().execute(
        "SELECT 1 FROM usuario WHERE nombre = ?",
        (username,)
    ).fetchone()

    if exists:
        flash("El usuario ya existe", "error")
        return render_template("register.html")

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    get_db().execute("""
        INSERT INTO usuario (nombre, contrasena, fecha_nacimiento, direccion, telefono, tipo_usuario)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, hashed_pw, "2000-01-01", "Sin dirección", 0, "cliente"))
    get_db().commit()

    flash("Cuenta creada exitosamente", "success")

    row = get_db().execute(
        "SELECT id_usuario, nombre, contrasena, tipo_usuario FROM usuario WHERE nombre = ?",
        (username,)
    ).fetchone()

    login_user(User.from_row(row))
    return redirect(url_for("main.index"))



#Login normal
@auth.post("/login")
def login_post():
    username = request.form["username"].strip()
    password = request.form["password"]

    row = get_db().execute(
        "SELECT id_usuario, nombre, contrasena, tipo_usuario FROM usuario WHERE nombre = ?",
        (username,)
    ).fetchone()

    if not row:
        flash("Usuario no encontrado", "error")
        return render_template("login.html")

    user = User.from_row(row)

    stored = user.password_hash or ""
    is_bcrypt = stored.startswith("$2")
    ok = bcrypt.check_password_hash(stored, password) if is_bcrypt else (stored == password)

    if not ok:
        flash("Usuario o contraseña incorrectos", "error")
        return render_template("login.html")

    login_user(user)
    return redirect(url_for("main.profile"))




# Login Google
@auth.route("/login/google")
def login_google():
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
        "&access_type=offline"
    )
    return redirect(auth_url)

@auth.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: falta el código de autorización", 400

    token_data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    token_response = requests.post("https://oauth2.googleapis.com/token", data=token_data).json()
    access_token = token_response.get("access_token")
    if not access_token:
        return "Error al obtener el token", 400

    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email = user_info.get("email")
    name = user_info.get("name")

    if not email or not name:
        return "Error al obtener datos del usuario", 400

    db = get_db()
    
    
    row = db.execute(
        "SELECT id_usuario, nombre, contrasena, tipo_usuario FROM usuario WHERE email = ?",
        (email,)
    ).fetchone()

    if not row:
        
        cursor = db.execute(
            "INSERT INTO usuario (nombre, apellido, contrasena, email, fecha_nacimiento, direccion, telefono, tipo_usuario) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                name,
                "",  
                "",  
                email,
                "1900-01-01", 
                "",  
                0,  
                "Cliente" 
            )
        )
        db.commit()
        
        
        row = db.execute(
            "SELECT id_usuario, nombre, contrasena, tipo_usuario FROM usuario WHERE id_usuario = ?",
            (cursor.lastrowid,)
        ).fetchone()

   
    user = User.from_row(row)
    login_user(user)
    return redirect(url_for("main.profile"))

@auth.route("/")
def index():
    
    if current_user.is_authenticated:
        nombre = current_user.username
    else:
        nombre = "Invitado"
    return render_template("index.html", nombre=nombre)



@auth.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login_get"))