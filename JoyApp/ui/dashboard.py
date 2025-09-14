# JoyApp/ui/dashboard.py
import tkinter as tk
from .nueva_venta import NuevaVenta


class Dashboard(tk.Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user

        # Mostrar el frame
        self.pack(fill="both", expand=True)

        tk.Label(self, text=f"Bienvenido, {user['rol']}").pack(padx=12, pady=12)
        tk.Button(self, text="Nueva venta", command=self.open_nueva_venta).pack(fill="x", padx=12, pady=6)

        # TODO: Botones extra: Historial, Caja, Config (si JEFE)
        # if user['rol'] == 'JEFE':
        #     tk.Button(self, text="Config", command=self.open_config).pack(fill="x", padx=12, pady=6)

    def open_nueva_venta(self):
        win = tk.Toplevel(self.master)
        win.title("Nueva venta")
        NuevaVenta(win, self.user)
