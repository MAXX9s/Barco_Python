from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.db import get_db_connection
import sqlite3

barcos_bp = Blueprint('barcos', __name__, template_folder='templates')

def requiere_encargado_barcos(func):
    def wrapper(*args, **kwargs):
        if not hasattr(current_user, 'tipo') or current_user.tipo.strip().lower()  not in ('encargado de barcos', 'administrador'):
            return "No autorizado", 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@barcos_bp.route("/registrobarco", methods=["GET", "POST"])
@login_required
@requiere_encargado_barcos
def registrobarco():
    if request.method == "POST":
        try:
            nombre = request.form.get("nombre","").strip()
            capacidad = request.form.get("capacidad", "").strip()
            fecha_arribo = request.form.get("fecha_arribo", "").strip()
            hora_arribo = request.form.get("hora_arribo", "").strip()  
            fk_encargado_barcos = current_user.id 

            if not nombre or not capacidad or not fecha_arribo or not hora_arribo:
                flash("Todos los campos son obligatorios", "error")
                return render_template("barcos/registrobarco.html")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(""" 
                INSERT INTO barco 
                (nombre, capacidad, fecha_arribo, hora_arribo, fk_encargado_barcos)
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, capacidad, fecha_arribo, hora_arribo, fk_encargado_barcos))
            conn.commit()
            conn.close()

            flash("Barco registrado exitosamente", "success")
            return redirect(url_for('barcos.listabarcos'))
            
        except Exception as e:
            flash(f"Error al registrar barco: {str(e)}", "error")
            return render_template("barcos/registrobarco.html")
    else:
        return render_template("barcos/registrobarco.html")

@barcos_bp.route("/listabarcos", methods=["GET", "POST"])
@login_required
@requiere_encargado_barcos
def listabarcos():
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id_barco, nombre, capacidad, fecha_arribo, hora_arribo, fecha_zarpe, hora_zarpe, tarifa, Impuesto FROM barco"
    )
    barcos = cursor.fetchall()
    conn.close()
    
    return render_template('barcos/listabarcos.html', barcos=barcos)

@barcos_bp.route("/registrosalidabarco", methods=["GET", "POST"])
@login_required
@requiere_encargado_barcos
def registrosalidabarco():
    if request.method == "POST":
        try:
            print("Datos del formulario:", request.form)
            id_barco = request.form.get("id_barco")
            tarifa = request.form.get("tarifa", "").strip()
            impuesto = request.form.get("Impuesto", "").strip()
            fecha_zarpe = request.form.get("fecha_zarpe", "").strip()
            hora_zarpe = request.form.get("hora_zarpe", "").strip()

            if not id_barco or not fecha_zarpe or not hora_zarpe:
                flash("Barco, fecha y hora de zarpe son obligatorios", "error")
                return redirect(url_for('barcos.registrosalidabarco'))

            conn = get_db_connection()
            cursor = conn.cursor()
            
            #verificar que el barco existe y no tiene salida registrada
            cursor.execute("SELECT fecha_zarpe FROM barco WHERE id_barco = ?", (id_barco,))
            barco = cursor.fetchone()
            
            if not barco:
                flash("Barco no encontrado", "error")
                return redirect(url_for('barcos.registrosalidabarco'))
                
            if barco[0] is not None:
                flash("Este barco ya tiene salida registrada", "warning")
                return redirect(url_for('barcos.registrosalidabarco'))

            # registrar salida
            cursor.execute(
                """
                UPDATE barco SET
                tarifa = ?, Impuesto = ?, fecha_zarpe = ?, hora_zarpe = ?
                WHERE id_barco = ?
                """,
                (tarifa or None, impuesto or None, fecha_zarpe, hora_zarpe, id_barco)
            )
            conn.commit()
            conn.close()

            flash("Salida registrada correctamente", "success")
            return redirect(url_for('barcos.listabarcos'))

        except Exception as e:
            flash(f"Error al registrar salida: {str(e)}", "error")
            return redirect(url_for('barcos.registrosalidabarco'))

    # mostrar barcos en puerto
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_barco, nombre FROM barco WHERE fecha_zarpe IS NULL")
    barcos_en_puerto = cursor.fetchall()
    conn.close()
    
    return render_template('barcos/registrosalidabarco.html', barcos_en_puerto=barcos_en_puerto)

@barcos_bp.route("/eliminarbarco/<int:id_barco>")
@login_required
@requiere_encargado_barcos
def eliminarbarco(id_barco):
    try:
    
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM barco WHERE id_barco = ?", (id_barco,))
        conn.commit()
        conn.close()
        
        flash("Barco eliminado exitosamente", "success")
        return redirect(url_for('barcos.listabarcos'))
        
    except Exception as e:
        flash(f"Error al eliminar el Barco: {str(e)}", "error")
        return redirect(url_for('barcos.listabarcos'))
