# JoyApp/db.py
from pathlib import Path
import sqlite3

DB_PATH = Path("data.db")

def get_conn():
    # Siempre devolver una conexión nueva; habilitamos FK por si usás claves foráneas
    con = sqlite3.connect(str(DB_PATH))
    con.execute("PRAGMA foreign_keys = ON;")
    return con

def init_db():
    from textwrap import dedent

    schema = dedent("""
        -- Tablas base
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT CHECK(rol IN ('JEFE','VENDEDOR')) NOT NULL,
            activo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS materiales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ley TEXT,
            precio_gramo_mayor REAL NOT NULL,
            precio_gramo_menor REAL NOT NULL,
            activo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS extras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            activo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS caja_sesiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_apertura TEXT NOT NULL,
            usuario_apertura INTEGER NOT NULL,
            monto_inicial REAL NOT NULL,
            fecha_cierre TEXT,
            usuario_cierre INTEGER,
            monto_cierre REAL
        );

        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            modalidad TEXT CHECK(modalidad IN ('MAYOR','MENOR')) NOT NULL,
            caja_sesion_id INTEGER,
            total REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS venta_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            material_id INTEGER,
            descripcion TEXT,
            peso_gramos REAL,
            precio_por_gramo REAL,
            cantidad INTEGER DEFAULT 1,
            subtotal REAL NOT NULL,
            tipo TEXT CHECK(tipo IN ('MATERIAL','EXTRA')) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            metodo TEXT CHECK(metodo IN ('EFECTIVO','TARJETA','TRANSFERENCIA')) NOT NULL,
            monto REAL NOT NULL
        );

        -- Índices útiles
        CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);
        CREATE INDEX IF NOT EXISTS idx_items_venta ON venta_items(venta_id);
        CREATE INDEX IF NOT EXISTS idx_pagos_venta ON pagos(venta_id);
    """)

    with get_conn() as con:
        con.executescript(schema)
        # Usuario admin por defecto si no existe
        cur = con.execute("SELECT COUNT(*) FROM usuarios WHERE username = ?", ("admin",))
        if cur.fetchone()[0] == 0:
            # contraseña 'admin' hasheada simple (reemplazá por bcrypt más adelante)
            # NO usar en producción sin bcrypt
            con.execute(
                "INSERT INTO usuarios (username, password_hash, rol, activo) VALUES (?,?,?,1)",
                ("admin", "admin", "JEFE")
            )
        con.commit()
