# JoyApp/main.py
import tkinter as tk
import sqlite3
import os
from datetime import datetime

from .db import init_db, get_conn
from .auth import crear_usuario
from .ui.login import Login
from .ui.dashboard import Dashboard


# 🧩 Nueva función: verificación y migración automática
def verificar_y_migrar_db():
    """Verifica la estructura de la tabla materiales y la migra si es necesario."""
    db_path = os.path.join(os.path.dirname(__file__), "data.db")

    # Crear base si no existe
    if not os.path.exists(db_path):
        print("🆕 Creando base de datos nueva...")
        conn = sqlite3.connect(db_path)
        conn.close()
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Verificar existencia de tabla materiales
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='materiales'")
    existe = c.fetchone()

    if not existe:
        print("⚙️  Creando tabla 'materiales' por primera vez...")
        c.execute("""
            CREATE TABLE materiales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                ley TEXT,
                tipo TEXT,
                precio_gramo_mayor REAL NOT NULL,
                precio_gramo_menor REAL NOT NULL,
                activo INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()
        return

    # Revisar columnas actuales
    c.execute("PRAGMA table_info(materiales)")
    columnas = [col[1] for col in c.fetchall()]

    # Si ya está actualizada, salir
    if all(col in columnas for col in ["precio_gramo_mayor", "precio_gramo_menor", "activo", "ley"]):
        conn.close()
        print("✅ Base de datos OK - estructura de 'materiales' actualizada.")
        return

    # Hacer copia de seguridad
    backup_name = f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(os.path.dirname(__file__), backup_name)
    os.system(f'copy "{db_path}" "{backup_path}"' if os.name == "nt" else f'cp "{db_path}" "{backup_path}"')
    print(f"🗃️  Copia de seguridad creada: {backup_name}")

    # Migrar tabla materiales
    c.execute("ALTER TABLE materiales RENAME TO materiales_old")
    c.execute("""
        CREATE TABLE materiales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ley TEXT,
            tipo TEXT,
            precio_gramo_mayor REAL NOT NULL,
            precio_gramo_menor REAL NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)

    # Copiar datos antiguos si existe precio_gramo
    if "precio_gramo" in columnas:
        print("🔄 Migrando materiales antiguos...")
        c.execute("SELECT id, nombre, tipo, precio_gramo FROM materiales_old")
        for row in c.fetchall():
            _id, nombre, tipo, precio = row
            c.execute("""
                INSERT INTO materiales (id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, activo)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (_id, nombre, "", tipo, precio, precio))
    else:
        print("⚠️  Tabla vieja sin columna 'precio_gramo' — no se migraron datos.")

    c.execute("DROP TABLE materiales_old")
    conn.commit()
    conn.close()
    print("✅ Migración automática completada correctamente.")


# ---- USUARIO ADMIN ----
def bootstrap_admin():
    with get_conn() as con:
        exists = con.execute(
            "SELECT 1 FROM usuarios WHERE username = 'admin' LIMIT 1"
        ).fetchone() is not None
    if not exists:
        try:
            crear_usuario("admin", "admin", "JEFE")
            print("Usuario admin creado (admin/admin).")
        except sqlite3.IntegrityError:
            pass


# ---- PROGRAMA PRINCIPAL ----
def main():
    verificar_y_migrar_db()  # 🟢 Verificación automática antes de iniciar
    init_db()
    bootstrap_admin()

    root = tk.Tk()
    root.title("Joyería App")

    def on_logged(user):
        for w in root.winfo_children():
            w.destroy()
        dash = Dashboard(root, user)
        dash.pack(fill="both", expand=True)

    Login(root, on_logged)
    root.mainloop()


if __name__ == "__main__":
    main()
