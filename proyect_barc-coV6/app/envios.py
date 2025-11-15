from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.db import get_db_connection
import sqlite3

envios_bp = Blueprint('envios', __name__, template_folder='templates')

def requiere_encargado_envios(func):
    def wrapper(*args, **kwargs):
        if not hasattr(current_user, 'tipo') or current_user.tipo.strip().lower() != 'encargado de envios':
            return "No autorizado", 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@envios_bp.route("/registroenvio", methods=["GET", "POST"])
@login_required
@requiere_encargado_envios
def registroenvio():
    if request.method == "POST":
        try:
            descripcion = request.form.get("descripcion","").strip()
            estado = request.form.get("estado", "").strip()
            origen = request.form.get("origen", "").strip()
            destino = request.form.get("destino", "").strip()
            fk_encargado_envios = current_user.id  # ← USA EL ID DEL USUARIO LOGUEADO
            fk_barcos = request.form.get("barco", "").strip()

            if not descripcion or not origen or not destino:
                flash("Descripción, origen y destino son obligatorios", "error")
                return render_template("envios/registroenvio.html")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(""" 
                INSERT INTO envio 
                (descripcion, estado, origen, destino, fk_encargado_envios, fk_barcos)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (descripcion, estado, origen, destino, fk_encargado_envios, fk_barcos))
            conn.commit()
            conn.close()

            flash("Envío registrado exitosamente", "success")
            return redirect(url_for('envios.listaenvios'))
            
        except Exception as e:
            flash(f"Error al registrar envío: {str(e)}", "error")
            return render_template("envios/registroenvio.html")
    
    else:
        return render_template("envios/registroenvio.html")

@envios_bp.route("/listaenvios")
@login_required
@requiere_encargado_envios
def listaenvios():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    envios = conn.execute("SELECT * FROM envio").fetchall()
    conn.close()
    return render_template("envios/listaenvios.html", envios=envios)