# JoyApp/main.py
import tkinter as tk

from .db import init_db, get_conn
from .auth import crear_usuario
from .ui.login import Login
from .ui.dashboard import Dashboard

def bootstrap_admin():
    import sqlite3
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

def main():
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
