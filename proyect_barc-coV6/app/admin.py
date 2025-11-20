from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.db import get_db_connection
import sqlite3
import bcrypt
from werkzeug.security import generate_password_hash
admin_bp = Blueprint('admin', __name__, template_folder='templates')
#Validacion de administrador 
def requiere_administrador(func):
    def wrapper(*args, **kwargs):
        if not hasattr(current_user, 'tipo') or current_user.tipo.strip().lower() != 'administrador':
            return "No autorizado", 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper
#Atraves de un Form crear un usuario 
@admin_bp.route("/gestionusuarios", methods=["GET", "POST"])
@login_required
@requiere_administrador
def gestionusuarios():
    if request.method == "POST":
        try:
            nombre = request.form.get("nombre", "").strip()
            apellido = request.form.get("apellido", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            tipo_usuario = request.form.get("tipo_usuario", "").strip()
            fecha_nacimiento = request.form.get("fecha_nacimiento", "").strip()
            direccion = request.form.get("direccion", "").strip()
            telefono = request.form.get("telefono", "").strip()

            if not nombre or not email or not password:
                flash("Nombre, email y contraseña son obligatorios", "error")
                return render_template("admin/gestionusuarios.html")

          
            conn = get_db_connection()
            exists = conn.execute(
                "SELECT 1 FROM usuario WHERE email = ? OR nombre = ?",
                (email, nombre)
            ).fetchone()
            
            if exists:
                flash("El usuario ya existe", "error")
                conn.close()
                return render_template("admin/gestionusuarios.html")

       
            hashed_pw = generate_password_hash(password)

       
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuario 
                (nombre, apellido, email, contrasena, tipo_usuario, fecha_nacimiento, direccion, telefono)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nombre, apellido, email, hashed_pw, tipo_usuario, fecha_nacimiento, direccion, telefono))
            
            conn.commit()
            conn.close()

            flash("Usuario registrado exitosamente", "success")
            return redirect(url_for('admin.listausuarios'))
            
        except Exception as e:
            flash(f"Error al registrar usuario: {str(e)}", "error")
            return render_template("admin/gestionusuarios.html")
    
    else:
        return render_template("admin/gestionusuarios.html")
#Def Editar Cargo del Usuario 
@admin_bp.route("/modificarusuario", methods=["POST"])
@login_required
@requiere_administrador
def modificarusuario():
    try:
        id_usuario = request.form.get("id_usuario")
        nuevo_tipo = request.form.get("tipo_nuevo", "").strip()
        nuevo_estado = request.form.get("estado_nuevo", "").strip()
        
        if not id_usuario:
            flash("ID de usuario requerido", "error")
            return redirect(request.referrer)
        
       
        tipos_validos = ["administrador", "encargado de envios", "encargado de barcos", "Cliente"]
        if nuevo_tipo and nuevo_tipo not in tipos_validos:
            flash("Tipo de usuario no válido", "error")
            return redirect(request.referrer)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        
        update_fields = []
        update_values = []
        
        if nuevo_tipo:
            update_fields.append("tipo_usuario = ?")
            update_values.append(nuevo_tipo)
        
        if nuevo_estado:
            update_fields.append("estado = ?")
            update_values.append(nuevo_estado)
        
        if not update_fields:
            flash("No se proporcionaron campos para actualizar", "error")
            conn.close()
            return redirect(request.referrer)
        
        update_values.append(id_usuario)
        
        cursor.execute(f"""
            UPDATE usuario 
            SET {', '.join(update_fields)}
            WHERE id_usuario = ?
        """, update_values)
        
        conn.commit()
        conn.close()
        
        flash("Usuario actualizado correctamente", "success")
        return redirect(url_for('admin.listausuarios'))
        
    except Exception as e:
        flash(f"Error al actualizar usuario: {str(e)}", "error")
        return redirect(request.referrer)
#Def Visualizar Lista de usuarios 
@admin_bp.route("/listausuarios")
@login_required
@requiere_administrador
def listausuarios():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    usuarios = conn.execute("SELECT * FROM usuario").fetchall()
    conn.close()
    return render_template("admin/listausuarios.html", usuarios=usuarios)
#Def Eliminar con id 
@admin_bp.route("/eliminarusuario/<int:user_id>")
@login_required
@requiere_administrador
def eliminarusuario(user_id):
    try:
     
        if user_id == current_user.id:
            flash("No puedes eliminar tu propio usuario", "error")
            return redirect(url_for('admin.listausuarios'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM usuario WHERE id_usuario = ?", (user_id,))
        conn.commit()
        conn.close()
        
        flash("Usuario eliminado exitosamente", "success")
        return redirect(url_for('admin.listausuarios'))
        
    except Exception as e:
        flash(f"Error al eliminar usuario: {str(e)}", "error")
        return redirect(url_for('admin.listausuarios'))

@admin_bp.route("/dashboard")
@login_required
@requiere_administrador
def dashboard():
    conn = get_db_connection()

    total_usuarios = conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0]
    total_envios = conn.execute("SELECT COUNT(*) FROM envio").fetchone()[0]
    total_barcos = conn.execute("SELECT COUNT(*) FROM barco").fetchone()[0]
    

    usuarios_por_tipo = conn.execute("""
        SELECT tipo_usuario, COUNT(*) as count 
        FROM usuario 
        GROUP BY tipo_usuario
    """).fetchall()
    
    conn.close()
    
    return render_template("admin/dashboard.html", 
                         total_usuarios=total_usuarios,
                         total_envios=total_envios,
                         total_barcos=total_barcos,
                         usuarios_por_tipo=usuarios_por_tipo)