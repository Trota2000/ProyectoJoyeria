# JoyApp/ui_theme.py
import os
import tkinter as tk
from tkinter import ttk

# PIL es opcional: si no está instalada, el tema sigue funcionando
try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None


def _assets_path(*parts):
    # Raíz del paquete JoyApp
    base = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(base, "assets", *parts))


def aplicar_tema_base(root: tk.Tk | tk.Toplevel):
    """Aplica estilos base (colores, Treeview, ttk) y retorna un dict de colores."""
    style = ttk.Style(root)
    # Usa 'clam' si está disponible (mejor para temas personalizados)
    try:
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    colors = {
        "bg": "#1A1A1A",       # Fondo principal
        "fg": "#F8F8F8",       # Texto general
        "card": "#2A2A2A",     # Paneles / frames
        "accent": "#D4AF37",   # Dorado
        "primary": "#A3003F",  # Vino
        "muted": "#8A8A8A",
    }

    # Fondo de la ventana
    try:
        root.configure(bg=colors["bg"])
    except Exception:
        pass

    # Estilo general de ttk.Button (por si usas ttk en algunos lados)
    style.configure(
        "TButton",
        font=("Segoe UI", 10, "bold"),
        foreground=colors["fg"],
        background=colors["primary"],
        borderwidth=0,
        padding=8,
    )
    style.map("TButton", background=[("active", colors["accent"])])

    # Treeview
    style.configure(
        "Treeview",
        background=colors["card"],
        fieldbackground=colors["card"],
        foreground=colors["fg"],
        bordercolor=colors["accent"],
        rowheight=24,
    )
    style.map("Treeview", background=[("selected", colors["primary"])])
    style.configure(
        "Treeview.Heading",
        background=colors["primary"],
        foreground=colors["fg"],
        relief="flat",
        font=("Segoe UI", 10, "bold")
    )

    # LabelFrame
    style.configure(
        "TLabelframe",
        background=colors["card"],
        bordercolor=colors["accent"]
    )
    style.configure(
        "TLabelframe.Label",
        background=colors["card"],
        foreground=colors["accent"],
        font=("Segoe UI", 10, "bold")
    )

    # Labels por defecto (afecta ttk.Label)
    style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])

    return colors


def fondo_degradado(root: tk.Tk | tk.Toplevel):
    """
    Intenta colocar una imagen de fondo (bg_gradient.png) cubriendo toda la ventana.
    Si no existe o no hay PIL, se limita a dejar el color de fondo ya configurado.
    """
    if Image is None or ImageTk is None:
        return

    path = _assets_path("bg_gradient.png")
    if not os.path.exists(path):
        return

    try:
        img = Image.open(path)
        # Redimensiona al tamaño actual de la ventana
        w = max(root.winfo_screenwidth() // 2, 800)
        h = max(root.winfo_screenheight() // 2, 600)
        img = img.resize((w, h))
        photo = ImageTk.PhotoImage(img)

        lbl = tk.Label(root, image=photo, borderwidth=0)
        lbl.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Evitar recolección de basura
        root._bg_image_ref = photo
        root._bg_label_ref = lbl
    except Exception:
        pass


def crear_logo(parent: tk.Widget):
    """
    Coloca el logo (logo.png) arriba del dashboard.
    Si no existe o no hay PIL, muestra un label de texto.
    """
    # Intenta respetar colores del dashboard si los tiene
    colors = getattr(parent, "colors", {"bg": "#1A1A1A", "fg": "#F8F8F8"})

    if Image is not None and ImageTk is not None:
        path = _assets_path("logo.png")
        if os.path.exists(path):
            try:
                img = Image.open(path).resize((130, 130))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(parent, image=photo, bg=colors["bg"])
                lbl.pack(pady=10)
                # Guardar referencia para que no se libere
                parent._logo_img_ref = photo
                return
            except Exception:
                pass

    # Fallback: texto si no hay imagen
    tk.Label(
        parent,
        text="ESTELA JOYAS",
        bg=colors["bg"],
        fg=colors["accent"],
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)


def boton_estilo():
    """
    Estilo para tk.Button (no ttk) que estás usando con **btn_style.
    """
    return {
        "bg": "#D4AF37",            # accent
        "fg": "#1A1A1A",
        "activebackground": "#A3003F",
        "activeforeground": "#F8F8F8",
        "font": ("Segoe UI", 10, "bold"),
        "relief": "flat",
        "bd": 0,
        "cursor": "hand2",
    }
