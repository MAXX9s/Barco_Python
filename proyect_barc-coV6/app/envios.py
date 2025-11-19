from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.db import get_db_connection
import sqlite3

envios_bp = Blueprint('envios', __name__, template_folder='templates')

def requiere_encargado_envios(func):
    def wrapper(*args, **kwargs):
        if not hasattr(current_user, 'tipo') or current_user.tipo.strip().lower() not in ('encargado de envios', 'administrador'):
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
            fk_encargado_envios = current_user.id 
            fk_barco = request.form.get("fk_barco", "").strip()

            if not descripcion or not origen or not destino:
                flash("Descripción, origen y destino son obligatorios", "error")
                return render_template("envios/registroenvio.html")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(""" 
                INSERT INTO envio 
                (descripcion, estado, origen, destino, fk_encargado_envios, fk_barco)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (descripcion, estado, origen, destino, fk_encargado_envios, fk_barco))
            conn.commit()
            conn.close()

            flash("Envío registrado exitosamente", "success")
            return redirect(url_for('envios.listaenvios'))
            
        except Exception as e:
            flash(f"Error al registrar envío: {str(e)}", "error")
            return render_template("envios/registroenvio.html")
    
    else:
        return render_template("envios/registroenvio.html")
    

@envios_bp.route("/listaenvios", methods=["POST"])
@login_required
@requiere_encargado_envios
def modificarenvio():
    try:
        id_envio = request.form.get("id_envio")
        nuevo_estado = request.form.get("estado_nuevo").strip()
        
        if not id_envio or not nuevo_estado:
            flash("Datos incompletos", "error")
            return redirect(request.referrer)
        
        estados_validos = ["pendiente", "en_proceso", "entregado", "cancelado"]
        if nuevo_estado not in estados_validos:
            flash("Estado no válido", "error")
            return redirect(request.referrer)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE envio 
            SET estado = ?
            WHERE id_envio = ?
        """, (nuevo_estado, id_envio))
        
        conn.commit()
        conn.close()
        
        flash("Estado actualizado correctamente", "success")
        return redirect("/listaenvios")
        
    except Exception as e:
        flash(f"Error al actualizar: {str(e)}", "error")
        return redirect(request.referrer)

@envios_bp.route("/listaenvios")
@login_required
@requiere_encargado_envios
def listaenvios():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    envios = conn.execute("SELECT * FROM envio").fetchall()
    conn.close()
    return render_template("envios/listaenvios.html", envios=envios)