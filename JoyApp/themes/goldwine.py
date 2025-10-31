# JoyApp/themes/goldwine.py
import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import tkinter.font as tkfont


def aplicar_tema_base(root: tk.Tk):
    """Aplica colores, fuentes e iconos base para toda la app."""
    # Paleta
    COLORS = {
        "bg": "#4B0010",       # granate oscuro
        "accent": "#A3003F",   # vino intenso
        "gold": "#D4AF37",     # dorado
        "text": "#F8F8F8",     # blanco cálido
        "tree_bg": "#1A1A1A",
    }

    # Fondo de ventana raíz
    try:
        root.configure(bg=COLORS["bg"])
    except Exception:
        pass

    # Fuente global
    try:
        font_default = tkfont.nametofont("TkDefaultFont")
        font_default.configure(family="Segoe UI", size=10)
    except Exception:
        pass

    # Ícono de la app
    ico_path = os.path.join(os.path.dirname(__file__), "..", "assets", "joyapp.ico")
    if os.path.exists(ico_path):
        try:
            root.iconbitmap(ico_path)
        except Exception:
            pass

    # Estilos ttk
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "Treeview",
        background=COLORS["tree_bg"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["tree_bg"],
        bordercolor=COLORS["gold"],
        rowheight=22,
    )
    style.map("Treeview", background=[("selected", COLORS["accent"])])

    style.configure(
        "TButton",
        font=("Segoe UI", 10, "bold"),
        foreground=COLORS["text"],
        background=COLORS["accent"],
        borderwidth=0,
    )
    style.map(
        "TButton",
        background=[("active", COLORS["gold"])],
        foreground=[("active", "#1A1A1A")],
    )

    return COLORS


def crear_logo(parent):
    """Inserta el logo si existe, y devuelve el widget Label."""
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
    if not os.path.exists(logo_path):
        return None
    try:
        img = Image.open(logo_path).resize((130, 130))
        logo_img = ImageTk.PhotoImage(img)
        lbl = tk.Label(parent, image=logo_img, bg="#4B0010")
        lbl.image = logo_img  # mantener referencia
        lbl.pack(pady=(10, 6))
        return lbl
    except Exception:
        return None


def fondo_degradado(parent):
    """Coloca un fondo degradado si el archivo existe."""
    bg_path = os.path.join(os.path.dirname(__file__), "..", "assets", "bg_gradient.png")
    if os.path.exists(bg_path):
        try:
            img = Image.open(bg_path)
            bg_img = ImageTk.PhotoImage(img)
            lbl = tk.Label(parent, image=bg_img)
            lbl.place(relwidth=1, relheight=1)
            lbl.image = bg_img
            lbl.lower()
            return lbl
        except Exception:
            pass
    return None


def boton_estilo():
    """Devuelve un diccionario de estilo para usar con tk.Button"""
    return {
        "bg": "#D4AF37",
        "fg": "#1A1A1A",
        "activebackground": "#A3003F",
        "activeforeground": "#F8F8F8",
        "font": ("Segoe UI", 10, "bold"),
        "relief": "flat",
        "bd": 0,
        "cursor": "hand2",
    }


def estilizar_toplevel(toplevel):
    """Aplica fondo uniforme a ventanas emergentes."""
    try:
        toplevel.configure(bg="#4B0010")
    except Exception:
        pass
