from flask import Flask, render_template, g
import sqlite3
from pathlib import Path
import os

app = Flask(__name__)

# Definir la ruta de la base de datos UNA VEZ
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / 'puerto.db'

def get_db_connection():
    """Conexión para uso general"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """Conexión para contexto de Flask (auth.py)"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Cerrar conexión (para Flask)"""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Crear tablas si no existen"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # CREACION TABLA ADMINISTRADOR
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS administrador (
      id_administrador INTEGER PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      fk_usuario INTEGER NOT NULL
    );
    """)

    # CREACION TABLA BARCO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS barco (
      id_barco INTEGER PRIMARY KEY,
      nombre TEXT NOT NULL,
      capacidad REAL NOT NULL,
      fecha_arribo TEXT NOT NULL,
      hora_arribo TEXT NOT NULL,
      fecha_zarpe TEXT,
      hora_zarpe TEXT,
      tarifa REAL,
      Impuesto REAL,
      fk_encargado_barcos INTEGER NOT NULL
    );
    """)

    # CREACION TABLA CONTAINER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS container (
      id_container INTEGER PRIMARY KEY,
      contenido TEXT NOT NULL,
      peso REAL NOT NULL,
      empresa TEXT NOT NULL,
      fk_barco INTEGER NOT NULL,
      fk_envio INTEGER NOT NULL
    );
    """)

    # CREACION TABLA ENCARGADO DE BARCOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encargado_barcos (
      id_encargado_barcos INTEGER PRIMARY KEY,
      turno TEXT NOT NULL,
      fk_usuario INTEGER NOT NULL
    );
    """)

    # CREACION TABLA ENCARGADO DE ENVIOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encargado_envios (
      id_encargado_envios INTEGER PRIMARY KEY,
      turno TEXT NOT NULL,
      fk_usuario INTEGER NOT NULL
    );
    """)

    # CREACION TABLA ENVIO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS envio (
      id_envio INTEGER PRIMARY KEY,
      descripcion TEXT NOT NULL,
      estado TEXT NOT NULL,
      origen TEXT NOT NULL,
      destino TEXT NOT NULL,
      fk_encargado_envios INTEGER NOT NULL,
      fk_barco INTEGER NOT NULL
    );
    """)

    # CREACION TABLA USUARIO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
      id_usuario INTEGER PRIMARY KEY,
      nombre TEXT NOT NULL,
      apellido TEXT NOT NULL,
      contrasena TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE , 
      fecha_nacimiento TEXT NOT NULL,
      direccion TEXT NOT NULL,
      telefono INTEGER NOT NULL,
      tipo_usuario TEXT NOT NULL
    );
    """)

    # INSERTS (UTILIZO OR REPLACE PARA QUE NO SE ROMPA SI SE EJECUTA DOS VECES)
    # INSERT ADMINISTRADOR
    cursor.execute("""
    INSERT OR REPLACE INTO administrador (id_administrador, email, fk_usuario)
    VALUES (1, 'nico@davinci.edu.ar', 2);
    """)

    # INSERT BARCO
    cursor.execute("""
    INSERT OR REPLACE INTO barco
    (id_barco, nombre, capacidad, fecha_arribo, hora_arribo, fecha_zarpe, hora_zarpe, tarifa, Impuesto, fk_encargado_barcos) VALUES
    (0, 'Barco Ejemplo',   150000, '2025-06-23', '09:30:00', '2025-06-26', '02:02:00', 20000, 0,    3),
    (1, 'Frigorífico Sur', 120000, '2025-06-22', '16:40:00', NULL,         NULL,       45000, 3000, 4),
    (2, 'Mar Caribe',      180000, '2023-11-10', '11:15:00', '2023-11-12', '18:30:00', 28000, NULL, 3),
    (3, 'Pesca Norte',      80000, '2025-06-21', '14:20:00', NULL,         NULL,       12000, 1500, 5),
    (4, 'PEPE',              2000, '2025-06-26', '04:03:00', NULL,         NULL,         222, NULL, 1);
    """)

    # INSERT CONTAINER
    cursor.execute("""
    INSERT OR REPLACE INTO container
    (id_container, contenido, peso, empresa, fk_barco, fk_envio) VALUES
    (1, 'Kiwis', 30000, 'Zespri',   1, 1),
    (2, 'Kiwis', 30000, 'Zespri',   1, 1),
    (3, 'Leche', 50000, 'Fonterra', 1, 1),
    (4, 'Leche', 30000, 'Fonterra', 1, 1),
    (5, 'Reliquias fragiles', 20000, 'Te Papa', 1, 1);
    """)

    # INSERT ENCARGADO BARCOS
    cursor.execute("""
    INSERT OR REPLACE INTO encargado_barcos
    (id_encargado_barcos, turno, fk_usuario) VALUES
    (1, 'Mañana', 3);
    """)

    # INSERT ENCARGADO ENVIOS
    cursor.execute("""
    INSERT OR REPLACE INTO "encargado_envios"
    (id_encargado_envios, turno, fk_usuario) VALUES
    (1, 'Mañana', 4);
    """)

    # INSERT ENVIO
    cursor.execute("""
    INSERT OR REPLACE INTO envio
    (id_envio, descripcion, estado, origen, destino, fk_encargado_envios, fk_barco) VALUES
    (1, 'El Buque llego y se esta descargando los containers', 'Entregado', 'Nueva Zelanda', 'Argentina', 4, 0),
    (2, 'Mates', 'En proceso', 'Argentina ', 'Nueva Zelanda', 1, 0);
    """)

    # INSERT USUARIO
    cursor.execute("""
    INSERT OR REPLACE INTO usuario
    (id_usuario, nombre, apellido, contrasena, email, fecha_nacimiento, direccion, telefono, tipo_usuario) VALUES
    (2, 'Nico', 'Gonzalez' , '111', 'nico@gmail.com','2005-01-22', 'Callao 2134', 11234675, 'administrador'),
    (3, 'Lucas', 'Gonzalez', '222', 'lucas@gmail.com','2005-12-22', 'Riobamba 344', 11651298, 'encargado de barcos'),
    (4, 'Maxi', 'Gonzalez','333', 'maxi@gmail.com','2005-09-25', 'Peña 1239',    11347612, 'encargado de envios'),
    (5, 'Sebas', 'Gonzalez' ,'444', 'sebas@gmail.com','2000-12-25', 'Corrientes 123',11457454, 'cliente');
    """)

    conn.commit()
    conn.close()
    print(f"Base '{DATABASE_PATH}' creada y cargada correctamente")