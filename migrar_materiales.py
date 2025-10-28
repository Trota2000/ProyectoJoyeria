# migrar_materiales.py
import sqlite3
import os
from datetime import datetime

# Ruta absoluta al data.db
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

# Backup de seguridad antes de tocar la base
backup_name = f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
backup_path = os.path.join(os.path.dirname(__file__), backup_name)

print(f"🔒 Creando copia de seguridad: {backup_name}")
os.system(f'copy "{DB_PATH}" "{backup_path}"' if os.name == "nt" else f'cp "{DB_PATH}" "{backup_path}"')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Verificar si la tabla materiales existe
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='materiales'")
existe = c.fetchone()

if not existe:
    print("⚠️ No existe la tabla 'materiales'. Nada que migrar.")
    conn.close()
    exit()

print("🔄 Iniciando migración de la tabla 'materiales'...")

# Obtener columnas actuales
c.execute("PRAGMA table_info(materiales)")
columnas = [col[1] for col in c.fetchall()]
print(f"📋 Columnas actuales: {columnas}")

# Si ya tiene las columnas nuevas, no hace nada
if "precio_gramo_mayor" in columnas and "precio_gramo_menor" in columnas:
    print("✅ La tabla 'materiales' ya tiene la estructura correcta. No se requiere migración.")
    conn.close()
    exit()

# Renombrar tabla vieja
c.execute("ALTER TABLE materiales RENAME TO materiales_old")

# Crear nueva estructura compatible
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

# Copiar datos de la tabla vieja (si tiene precio_gramo)
if "precio_gramo" in columnas:
    print("📦 Copiando datos de materiales antiguos...")
    c.execute("SELECT id, nombre, tipo, precio_gramo FROM materiales_old")
    for row in c.fetchall():
        _id, nombre, tipo, precio = row
        c.execute("""
            INSERT INTO materiales (id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, activo)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (_id, nombre, "", tipo, precio, precio))
else:
    print("⚠️ La tabla antigua no tiene columna 'precio_gramo', no se migraron datos.")

# Eliminar tabla vieja
c.execute("DROP TABLE materiales_old")

conn.commit()
conn.close()

print("\n✅ Migración completada con éxito.")
print("👉 Ahora tu tabla 'materiales' tiene columnas:")
print("   [id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, activo]")
print("🔁 Podés ejecutar tu aplicación normalmente con:")
print("   python main.py")
