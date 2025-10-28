import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os
from .nueva_venta import NuevaVenta


class Dashboard(tk.Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user

        self.pack(fill="both", expand=True)

        tk.Label(self, text=f"Bienvenido, {user['rol']}").pack(padx=12, pady=12)

        tk.Button(self, text="Nueva venta", command=self.open_nueva_venta).pack(fill="x", padx=12, pady=6)
        tk.Button(self, text="Gestión de Materiales", command=self.open_gestion_materiales).pack(fill="x", padx=12, pady=6)

    # ---- Ventana de Nueva Venta ----
    def open_nueva_venta(self):
        """
        Abre la ventana de Nueva Venta y actualiza el listado de materiales antes de mostrarla.
        Esto asegura que se vean los materiales agregados recientemente sin reiniciar la app.
        """
        win = tk.Toplevel(self.master)
        win.title("Nueva venta")

        try:
            from ..models import listar_materiales_activos
            materiales_actualizados = listar_materiales_activos()
            print(f"[INFO] {len(materiales_actualizados)} materiales cargados (actualizados).")
        except Exception as e:
            print(f"[ERROR] No se pudieron cargar materiales actualizados: {e}")
            materiales_actualizados = []

        venta_ui = NuevaVenta(win, self.user)

        # 🔄 Si la clase NuevaVenta tiene el atributo materiales, lo actualizamos
        if hasattr(venta_ui, "materiales"):
            venta_ui.materiales = materiales_actualizados
            venta_ui.cbo_mat["values"] = [f"{m[1]} {m[2] or ''}".strip() for m in materiales_actualizados]

        # Mensaje visual opcional (puedes comentarlo si no querés mostrarlo)
        messagebox.showinfo("Actualizado", f"Se cargaron {len(materiales_actualizados)} materiales disponibles.")

    # ---- Gestión de materiales ----
    def open_gestion_materiales(self):
        ventana = tk.Toplevel(self.master)
        ventana.title("Gestión de Materiales")
        ventana.geometry("850x550")
        ventana.resizable(False, False)

        # Ruta absoluta a la base de datos
        db_path = os.path.join(os.path.dirname(__file__), "..", "data.db")
        db_path = os.path.abspath(db_path)

        # --- FORMULARIO ---
        frame_form = tk.LabelFrame(ventana, text="Formulario de Material", padx=10, pady=10)
        frame_form.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_form, text="Nombre:").grid(row=0, column=0, sticky="w")
        entry_nombre = tk.Entry(frame_form, width=25)
        entry_nombre.grid(row=0, column=1, padx=5, pady=4)

        tk.Label(frame_form, text="Ley (pureza):").grid(row=0, column=2, sticky="w")
        entry_ley = tk.Entry(frame_form, width=10)
        entry_ley.grid(row=0, column=3, padx=5, pady=4)

        tk.Label(frame_form, text="Tipo (Oro, Plata, etc.):").grid(row=1, column=0, sticky="w")
        entry_tipo = tk.Entry(frame_form, width=25)
        entry_tipo.grid(row=1, column=1, padx=5, pady=4)

        tk.Label(frame_form, text="Precio Mayor (Gs/gr):").grid(row=1, column=2, sticky="w")
        entry_precio_mayor = tk.Entry(frame_form, width=10)
        entry_precio_mayor.grid(row=1, column=3, padx=5, pady=4)

        tk.Label(frame_form, text="Precio Menor (Gs/gr):").grid(row=2, column=2, sticky="w")
        entry_precio_menor = tk.Entry(frame_form, width=10)
        entry_precio_menor.grid(row=2, column=3, padx=5, pady=4)

        activo_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_form, text="Activo", variable=activo_var).grid(row=2, column=1, sticky="w")

        modo_edicion = tk.BooleanVar(value=False)
        id_edicion = tk.StringVar(value="")

        frame_botones = tk.Frame(frame_form)
        frame_botones.grid(row=3, column=0, columnspan=4, pady=8)

        def guardar_material():
            nombre = entry_nombre.get().strip()
            tipo = entry_tipo.get().strip()
            ley = entry_ley.get().strip()
            mayor = entry_precio_mayor.get().strip()
            menor = entry_precio_menor.get().strip()
            activo = 1 if activo_var.get() else 0

            if not nombre or not mayor or not menor:
                messagebox.showwarning("Atención", "Completa todos los campos obligatorios (nombre y precios).")
                return

            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("""
                    CREATE TABLE IF NOT EXISTS materiales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        ley TEXT,
                        tipo TEXT,
                        precio_gramo_mayor REAL NOT NULL,
                        precio_gramo_menor REAL NOT NULL,
                        activo INTEGER DEFAULT 1
                    )
                """)

                if modo_edicion.get():
                    c.execute("""
                        UPDATE materiales
                        SET nombre=?, ley=?, tipo=?, precio_gramo_mayor=?, precio_gramo_menor=?, activo=?
                        WHERE id=?
                    """, (nombre, ley, tipo, float(mayor), float(menor), activo, id_edicion.get()))
                    messagebox.showinfo("Éxito", "✅ Material actualizado correctamente.")
                else:
                    c.execute("""
                        INSERT INTO materiales (nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, activo)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (nombre, ley, tipo, float(mayor), float(menor), activo))
                    messagebox.showinfo("Éxito", "✅ Material agregado correctamente.")

                conn.commit()
                conn.close()
                limpiar_formulario()
                cargar_materiales()
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {e}")

        def limpiar_formulario():
            entry_nombre.delete(0, tk.END)
            entry_ley.delete(0, tk.END)
            entry_tipo.delete(0, tk.END)
            entry_precio_mayor.delete(0, tk.END)
            entry_precio_menor.delete(0, tk.END)
            activo_var.set(True)
            modo_edicion.set(False)
            id_edicion.set("")
            btn_guardar.config(text="Guardar")
            btn_cancelar_edicion.pack_forget()

        def cancelar_edicion():
            limpiar_formulario()

        btn_guardar = tk.Button(frame_botones, text="Guardar", command=guardar_material)
        btn_guardar.pack(side="left", padx=4)
        btn_cancelar_edicion = tk.Button(frame_botones, text="Cancelar edición", command=cancelar_edicion)

        # --- 🔍 BUSCADOR + BOTONES DE ACCIÓN ---
        frame_busqueda = tk.LabelFrame(ventana, text="Buscar Material", padx=10, pady=10)
        frame_busqueda.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_busqueda, text="Buscar por nombre, tipo o ley:").pack(side="left")
        entry_buscar = tk.Entry(frame_busqueda, width=30)
        entry_buscar.pack(side="left", padx=6)

        lbl_resultados = tk.Label(frame_busqueda, text="Mostrando todos los materiales", fg="gray")
        lbl_resultados.pack(side="left", padx=10)

        def buscar(event=None):
            filtro = entry_buscar.get().strip().lower()
            for fila in tabla.get_children():
                tabla.delete(fila)
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            if filtro:
                c.execute("""
                    SELECT id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, activo
                    FROM materiales
                    WHERE LOWER(nombre) LIKE ? OR LOWER(tipo) LIKE ? OR LOWER(ley) LIKE ?
                    ORDER BY id DESC
                """, (f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"))
            else:
                c.execute("""
                    SELECT id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, activo
                    FROM materiales
                    ORDER BY id DESC
                """)
            resultados = c.fetchall()
            conn.close()

            for row in resultados:
                item = tabla.insert("", tk.END, values=row)
                if filtro and any(filtro in str(v).lower() for v in row[1:4]):
                    tabla.item(item, tags=("resaltado",))

            tabla.tag_configure("resaltado", background="#fff7cc")
            lbl_resultados.config(
                text=f"Mostrando {len(resultados)} resultado(s)" if filtro else f"Mostrando todos los materiales ({len(resultados)} total)"
            )

        entry_buscar.bind("<Return>", buscar)
        entry_buscar.bind("<KeyRelease>", buscar)
        entry_buscar.focus()

        # 🔘 Botones de acción debajo del buscador
        frame_acciones2 = tk.Frame(ventana)
        frame_acciones2.pack(fill="x", padx=10, pady=5)

        def editar_material():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning("Atención", "Selecciona un material para editar.")
                return
            item = tabla.item(seleccion[0])
            mat_id, nombre, ley, tipo, mayor, menor, activo = item["values"]
            entry_nombre.delete(0, tk.END)
            entry_ley.delete(0, tk.END)
            entry_tipo.delete(0, tk.END)
            entry_precio_mayor.delete(0, tk.END)
            entry_precio_menor.delete(0, tk.END)
            entry_nombre.insert(0, nombre)
            entry_ley.insert(0, ley)
            entry_tipo.insert(0, tipo)
            entry_precio_mayor.insert(0, mayor)
            entry_precio_menor.insert(0, menor)
            activo_var.set(bool(activo))
            modo_edicion.set(True)
            id_edicion.set(mat_id)
            btn_guardar.config(text="Actualizar")
            btn_cancelar_edicion.pack(side="left", padx=4)

        def eliminar_material():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning("Atención", "Selecciona un material para eliminar.")
                return
            item = tabla.item(seleccion[0])
            mat_id = item["values"][0]
            if not messagebox.askyesno("Confirmar", f"¿Eliminar material ID {mat_id}?"):
                return
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("DELETE FROM materiales WHERE id=?", (mat_id,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "🗑️ Material eliminado correctamente.")
                buscar()
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {e}")

        tk.Button(frame_acciones2, text="✏️ Editar seleccionado", command=editar_material).pack(side="left", padx=6)
        tk.Button(frame_acciones2, text="🗑️ Eliminar seleccionado", command=eliminar_material).pack(side="left", padx=6)

        # --- TABLA DE MATERIALES ---
        frame_lista = tk.LabelFrame(ventana, text="Materiales registrados", padx=10, pady=10)
        frame_lista.pack(fill="both", expand=True, padx=10, pady=10)

        columnas = ("id", "nombre", "ley", "tipo", "mayor", "menor", "activo")
        tabla = ttk.Treeview(frame_lista, columns=columnas, show="headings", height=12)
        tabla.pack(fill="both", expand=True)

        for col, text, width, anchor in [
            ("id", "ID", 40, "center"),
            ("nombre", "Nombre", 140, "w"),
            ("ley", "Ley", 80, "center"),
            ("tipo", "Tipo", 120, "center"),
            ("mayor", "Precio Mayor", 100, "e"),
            ("menor", "Precio Menor", 100, "e"),
            ("activo", "Activo", 60, "center")
        ]:
            tabla.heading(col, text=text)
            tabla.column(col, width=width, anchor=anchor)

        # --- CARGAR DATOS ---
        def cargar_materiales():
            for fila in tabla.get_children():
                tabla.delete(fila)
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("""
                    SELECT id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, activo
                    FROM materiales
                    ORDER BY id DESC
                """)
                for row in c.fetchall():
                    tabla.insert("", tk.END, values=row)
                conn.close()
                lbl_resultados.config(text="Mostrando todos los materiales")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron cargar los materiales: {e}")

        cargar_materiales()
