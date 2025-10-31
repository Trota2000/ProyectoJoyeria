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


# ─────────────────────────────────────────────────────────────────────────────
# 🎨 Tema visual JoyApp (granate + vino + dorado) — NO cambia funcionalidades
# ─────────────────────────────────────────────────────────────────────────────
def aplicar_tema(root: tk.Tk):
    """
    Aplica colores, tipografías e imágenes si existen.
    Todo es opcional: si faltan recursos o librerías, la app sigue funcionando igual.
    """
    # Colores de marca
    COLOR_BG = "#4B0010"      # granate oscuro
    COLOR_ACCENT = "#A3003F"  # vino intenso
    COLOR_GOLD = "#D4AF37"    # dorado
    COLOR_TEXT = "#F8F8F8"    # blanco suave

    # Fondo base
    try:
        root.configure(bg=COLOR_BG)
    except Exception:
        pass

    # Icono (opcional)
    try:
        ico_path = os.path.join(os.path.dirname(__file__), "assets", "joyapp.ico")
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)
    except Exception:
        pass

    # Tipografía por defecto (segura)
    try:
        import tkinter.font as tkfont
        f = tkfont.nametofont("TkDefaultFont")
        f.configure(family="Segoe UI", size=10)
    except Exception:
        pass

    # Si existe un fondo degradado, lo colocamos como imagen "cover"
    try:
        from PIL import Image, ImageTk
        bg_path = os.path.join(os.path.dirname(__file__), "assets", "bg_gradient.png")
        if os.path.exists(bg_path):
            img = Image.open(bg_path)
            bg_img = ImageTk.PhotoImage(img)
            bg_lbl = tk.Label(root, image=bg_img, borderwidth=0)
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
            # guardamos referencia para que no lo libere el GC
            root._joyapp_bg_ref = bg_img   # noqa: SLF001
            root._joyapp_bg_lbl = bg_lbl   # noqa: SLF001
    except Exception:
        # Si PIL no está, simplemente seguimos con color plano
        pass

    # Estilos ttk (si se usan) — no rompe los widgets tk existentes
    try:
        from tkinter import ttk
        style = ttk.Style()
        # Treeview oscuro con selección vino y bordes dorados
        style.configure("Treeview",
                        background="#1A1A1A", foreground=COLOR_TEXT,
                        fieldbackground="#1A1A1A",
                        bordercolor=COLOR_GOLD)
        style.map("Treeview", background=[("selected", COLOR_ACCENT)])

        # Botones (si en el proyecto hay ttk.Button)
        style.configure("TButton",
                        font=("Segoe UI", 10, "bold"),
                        foreground=COLOR_TEXT,
                        background=COLOR_ACCENT)
        style.map("TButton",
                  background=[("active", COLOR_GOLD)],
                  foreground=[("active", "#1A1A1A")])
    except Exception:
        pass

    # Guardamos colores para que otras vistas puedan leerlos si quieren
    root.joy_colors = {
        "bg": COLOR_BG,
        "accent": COLOR_ACCENT,
        "gold": COLOR_GOLD,
        "text": COLOR_TEXT,
    }


# ---- PROGRAMA PRINCIPAL ----
def main():
    verificar_y_migrar_db()  # 🟢 Verificación automática antes de iniciar
    init_db()
    bootstrap_admin()

    root = tk.Tk()
    root.title("Joyería App")

    # ✅ Solo estética (opcional). No afecta la lógica.
    aplicar_tema(root)

    def on_logged(user):
        for w in root.winfo_children():
            # mantenemos el fondo si existe (imagen colocada con place)
            # destruimos solo widgets "de contenido"
            try:
                if w is getattr(root, "_joyapp_bg_lbl", None):
                    continue
            except Exception:
                pass
            w.destroy()

        dash = Dashboard(root, user)
        dash.pack(fill="both", expand=True)

    Login(root, on_logged)
    root.mainloop()


if __name__ == "__main__":
    main()
