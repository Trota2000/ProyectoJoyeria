# JoyApp/ui/login.py
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from ..auth import validar_login

# Como este archivo está dentro de JoyApp/ui/, usamos import relativo:
from ..auth import validar_login


class Login(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("Login – Joyería")
        self.resizable(False, False)

        # --- UI ---
        frm = ttk.Frame(self, padding=12)
        frm.grid(sticky="nsew")

        ttk.Label(frm, text="Usuario").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        ttk.Label(frm, text="Contraseña").grid(row=1, column=0, padx=4, pady=4, sticky="e")

        self.e_user = ttk.Entry(frm)
        self.e_pass = ttk.Entry(frm, show="*")
        self.e_user.grid(row=0, column=1, padx=4, pady=4)
        self.e_pass.grid(row=1, column=1, padx=4, pady=4)

        btn = ttk.Button(frm, text="Ingresar", command=self.login)
        btn.grid(row=2, column=0, columnspan=2, pady=(8, 0))

        # callbacks
        self.on_success = on_success

        # UX: enter para enviar y foco inicial
        self.bind("<Return>", lambda _e: self.login())
        self.e_user.focus_set()

        # Centrar la ventana sobre el master
        self.after(10, self._center_on_master)

    def _center_on_master(self):
        if self.master is None:
            return
        self.update_idletasks()
        mx = self.master.winfo_rootx()
        my = self.master.winfo_rooty()
        mw = self.master.winfo_width()
        mh = self.master.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = mx + (mw - w) // 2
        y = my + (mh - h) // 2
        self.geometry(f"+{x}+{y}")

    def login(self):
        username = self.e_user.get().strip()
        password = self.e_pass.get()
        res = validar_login(username, password)
        if res:
            # res puede ser un dict/tupla con info del usuario (id, rol, etc.)
            self.on_success(res)
            self.destroy()
        else:
            messagebox.showerror("Error", "Usuario/contraseña inválidos")
            self.e_pass.delete(0, tk.END)
            self.e_pass.focus_set()
