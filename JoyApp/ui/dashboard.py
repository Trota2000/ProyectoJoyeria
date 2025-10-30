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
        tk.Button(self, text="Historial de Ventas", command=self.open_historial_ventas).pack(fill="x", padx=12, pady=6)
        tk.Button(self, text="Cierre de Caja", command=self.open_cierre_caja).pack(fill="x", padx=12, pady=6)

    # ---- Ventana de Nueva Venta ----
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

        # 🔇 Mantengo tu línea intacta pero anulo temporalmente el popup
        _orig_showinfo = messagebox.showinfo
        try:
            messagebox.showinfo = lambda *a, **k: None  # desactiva el cuadro solo aquí
            # Mensaje visual opcional (línea original, NO modificada)
            messagebox.showinfo("Actualizado", f"Se cargaron {len(materiales_actualizados)} materiales disponibles.")
        finally:
            messagebox.showinfo = _orig_showinfo  # restaurar para el resto de la app

    # ---- Gestión de materiales ----
    def open_gestion_materiales(self):
        ventana = tk.Toplevel(self.master)
        ventana.title("Gestión de Materiales")
        ventana.geometry("850x550")
        ventana.resizable(False, False)

        # Ruta absoluta a la base de datos
        db_path = os.path.join(os.path.dirname(__file__), "..", "data.db")
        db_path = os.path.abspath(db_path)

        # >>> ADDED: Migración suave para columna de stock
        try:
            conn_mig = sqlite3.connect(db_path)
            c_mig = conn_mig.cursor()
            cols = [r[1] for r in c_mig.execute("PRAGMA table_info(materiales)")]
            if "stock_gramos" not in cols:
                c_mig.execute("ALTER TABLE materiales ADD COLUMN stock_gramos REAL NOT NULL DEFAULT 0")
                conn_mig.commit()
            conn_mig.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo preparar la columna de stock: {e}")
            return
        # <<< ADDED

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

        # >>> ADDED: campo Stock (g) sin quitar nada
        tk.Label(frame_form, text="Stock (g):").grid(row=2, column=0, sticky="w")
        entry_stock = tk.Entry(frame_form, width=10)
        entry_stock.grid(row=2, column=1, padx=80, pady=4, sticky="w")
        # <<< ADDED

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

            # >>> ADDED: leer stock
            stock = entry_stock.get().strip()
            if stock == "":
                stock = "0"
            # <<< ADDED

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
                        activo INTEGER DEFAULT 1,
                        stock_gramos REAL NOT NULL DEFAULT 0
                    )
                """)

                if modo_edicion.get():
                    c.execute("""
                        UPDATE materiales
                        SET nombre=?, ley=?, tipo=?, precio_gramo_mayor=?, precio_gramo_menor=?, activo=?, stock_gramos=?
                        WHERE id=?
                    """, (nombre, ley, tipo, float(mayor), float(menor), activo, float(stock), id_edicion.get()))
                    messagebox.showinfo("Éxito", "✅ Material actualizado correctamente.")
                else:
                    c.execute("""
                        INSERT INTO materiales (nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, activo, stock_gramos)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (nombre, ley, tipo, float(mayor), float(menor), activo, float(stock)))
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
            # >>> ADDED: limpiar stock
            entry_stock.delete(0, tk.END)
            # <<< ADDED
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
                    SELECT id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, stock_gramos, activo
                    FROM materiales
                    WHERE LOWER(nombre) LIKE ? OR LOWER(tipo) LIKE ? OR LOWER(ley) LIKE ?
                    ORDER BY id DESC
                """, (f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"))
            else:
                c.execute("""
                    SELECT id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, stock_gramos, activo
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
            # >>> ADDED: incluye stock en el unpack
            mat_id, nombre, ley, tipo, mayor, menor, stock_tabla, activo = item["values"]
            # <<< ADDED
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
            # >>> ADDED: precargar stock desde tabla
            entry_stock.delete(0, tk.END)
            entry_stock.insert(0, stock_tabla)
            # <<< ADDED
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

        # >>> ADDED: agregamos columna "stock"
        columnas = ("id", "nombre", "ley", "tipo", "mayor", "menor", "stock", "activo")
        # <<< ADDED
        tabla = ttk.Treeview(frame_lista, columns=columnas, show="headings", height=12)
        tabla.pack(fill="both", expand=True)

        for col, text, width, anchor in [
            ("id", "ID", 40, "center"),
            ("nombre", "Nombre", 140, "w"),
            ("ley", "Ley", 80, "center"),
            ("tipo", "Tipo", 120, "center"),
            ("mayor", "Precio Mayor", 100, "e"),
            ("menor", "Precio Menor", 100, "e"),
            # >>> ADDED: header de stock
            ("stock", "Stock (g)", 100, "e"),
            # <<< ADDED
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
                    SELECT id, nombre, ley, tipo, precio_gramo_mayor, precio_gramo_menor, stock_gramos, activo
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

    # ---- Historial de ventas (con reimpresión) ----
    def open_historial_ventas(self):
        import datetime as dt

        ventana = tk.Toplevel(self.master)
        ventana.title("Historial de Ventas")
        ventana.geometry("950x600")
        ventana.resizable(False, False)

        # Ruta absoluta al mismo data.db que usás en gestión de materiales
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.db"))

        # --------- FILTROS ---------
        frame_filtros = tk.LabelFrame(ventana, text="Filtros", padx=10, pady=10)
        frame_filtros.pack(fill="x", padx=10, pady=(10, 6))

        tk.Label(frame_filtros, text="Desde (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        e_desde = tk.Entry(frame_filtros, width=12)
        e_desde.grid(row=0, column=1, padx=(5, 15))

        tk.Label(frame_filtros, text="Hasta (YYYY-MM-DD):").grid(row=0, column=2, sticky="w")
        e_hasta = tk.Entry(frame_filtros, width=12)
        e_hasta.grid(row=0, column=3, padx=(5, 15))

        tk.Label(frame_filtros, text="Texto (ID, vendedor, modalidad):").grid(row=0, column=4, sticky="w")
        e_texto = tk.Entry(frame_filtros, width=28)
        e_texto.grid(row=0, column=5, padx=(5, 10))

        lbl_total = tk.Label(frame_filtros, text="Mostrando 0 ventas | Total: 0 Gs", fg="gray")
        lbl_total.grid(row=0, column=6, padx=10)

        def normalizar_rango():
            d1 = e_desde.get().strip()
            d2 = e_hasta.get().strip()
            if not d1:
                d1 = "0001-01-01"
            if not d2:
                d2 = "9999-12-31"
            # valida formato
            try:
                dt.datetime.strptime(d1, "%Y-%m-%d")
            except Exception:
                d1 = "0001-01-01"
            try:
                dt.datetime.strptime(d2, "%Y-%m-%d")
            except Exception:
                d2 = "9999-12-31"
            return d1, d2

        def buscar(event=None):
            cargar_ventas()

        tk.Button(frame_filtros, text="Buscar", command=buscar).grid(row=0, column=7, padx=6)
        tk.Button(
            frame_filtros, text="Limpiar",
            command=lambda: [e_desde.delete(0, tk.END), e_hasta.delete(0, tk.END), e_texto.delete(0, tk.END), cargar_ventas()]
        ).grid(row=0, column=8, padx=6)

        e_texto.bind("<Return>", buscar)
        e_texto.bind("<KeyRelease>", lambda ev: cargar_ventas())

        # --------- LISTA DE VENTAS ---------
        frame_ventas = tk.LabelFrame(ventana, text="Ventas", padx=10, pady=10)
        frame_ventas.pack(fill="both", expand=True, padx=10, pady=(6, 6))

        cols_v = ("id", "fecha", "vendedor", "modalidad", "total")
        tv_ventas = ttk.Treeview(frame_ventas, columns=cols_v, show="headings", height=10)
        tv_ventas.pack(fill="both", expand=True)

        for c, t, w, a in [
            ("id", "ID", 60, "center"),
            ("fecha", "Fecha", 160, "center"),
            ("vendedor", "Vendedor", 160, "w"),
            ("modalidad", "Modalidad", 100, "center"),
            ("total", "Total (Gs)", 120, "e"),
        ]:
            tv_ventas.heading(c, text=t)
            tv_ventas.column(c, width=w, anchor=a)

        # --------- ACCIONES (Reimprimir) ---------
        frame_accion = tk.Frame(ventana)
        frame_accion.pack(fill="x", padx=10, pady=(0, 6))

        def reimprimir_ticket():
            sel = tv_ventas.selection()
            if not sel:
                messagebox.showwarning("Atención", "Selecciona una venta para reimprimir.")
                return

            venta_id = tv_ventas.item(sel[0])["values"][0]

            try:
                # Encabezado y totales
                con = sqlite3.connect(db_path)
                cur = con.cursor()
                cur.execute("""
                    SELECT v.id, v.fecha, v.modalidad, v.total, COALESCE(u.username, '(sin usuario)') AS vendedor
                    FROM ventas v
                    LEFT JOIN usuarios u ON u.id = v.usuario_id
                    WHERE v.id = ?
                """, (venta_id,))
                v = cur.fetchone()
                if not v:
                    con.close()
                    messagebox.showerror("Error", f"No se encontró la venta #{venta_id}.")
                    return
                _vid, fecha, modalidad, total, vendedor = v

                # Ítems
                cur.execute("""
                    SELECT descripcion, IFNULL(peso_gramos,0), IFNULL(precio_por_gramo,0),
                           IFNULL(cantidad,1), subtotal, tipo
                    FROM venta_items
                    WHERE venta_id = ?
                    ORDER BY id ASC
                """, (venta_id,))
                items_rows = cur.fetchall()

                # Pagos
                cur.execute("""
                    SELECT metodo, monto FROM pagos
                    WHERE venta_id = ?
                    ORDER BY id ASC
                """, (venta_id,))
                pagos_rows = cur.fetchall()
                con.close()

                # Printer
                try:
                    from ..printing import Printer
                except Exception:
                    from printing import Printer

                encabezado = {
                    "nombre": "ESTELA JOYAS",
                    "telefono": "000-000-000",
                    "ticket_id": str(venta_id) + " (reimpreso)",
                    "vendedor": vendedor,
                    "modalidad": modalidad,
                    "fecha": fecha,
                }

                items_print = [
                    {"descripcion": desc or "", "detalle": None, "subtotal": float(subt or 0)}
                    for (desc, _peso, _pgr, _cant, subt, _tipo) in items_rows
                ]
                pagos = [{"metodo": m, "monto": float(x or 0)} for (m, x) in pagos_rows]
                totales = {"total": float(total or 0)}

                salida = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), "..", f"ticket_{venta_id}_reimpreso.txt"
                ))

                printer = Printer(modo="archivo", ruta=salida)
                printer.print_ticket(encabezado, items_print, pagos, totales)

                messagebox.showinfo("OK", f"Ticket reimprimido en:\n{salida}")

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo reimprimir el ticket: {e}")

        tk.Button(frame_accion, text="🖨️ Reimprimir ticket seleccionado", command=reimprimir_ticket).pack(side="left")

        # --------- DETALLES (Ítems y Pagos) ---------
        frame_detalle = tk.Frame(ventana)
        frame_detalle.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        # Ítems
        lf_items = tk.LabelFrame(frame_detalle, text="Ítems de la venta", padx=10, pady=10)
        lf_items.pack(side="left", fill="both", expand=True, padx=(0, 5))

        cols_i = ("descripcion", "peso_g", "p_gr", "cant", "subtotal", "tipo")
        tv_items = ttk.Treeview(lf_items, columns=cols_i, show="headings", height=8)
        tv_items.pack(fill="both", expand=True)

        for c, t, w, a in [
            ("descripcion", "Descripción", 360, "w"),
            ("peso_g", "Peso (g)", 80, "e"),
            ("p_gr", "Gs/gramo", 100, "e"),
            ("cant", "Cant.", 60, "center"),
            ("subtotal", "Subtotal", 120, "e"),
            ("tipo", "Tipo", 80, "center"),
        ]:
            tv_items.heading(c, text=t)
            tv_items.column(c, width=w, anchor=a)

        # Pagos
        lf_pagos = tk.LabelFrame(frame_detalle, text="Pagos", padx=10, pady=10)
        lf_pagos.pack(side="left", fill="both", expand=True, padx=(5, 0))

        cols_p = ("metodo", "monto")
        tv_pagos = ttk.Treeview(lf_pagos, columns=cols_p, show="headings", height=8)
        tv_pagos.pack(fill="both", expand=True)

        tv_pagos.heading("metodo", text="Método")
        tv_pagos.column("metodo", width=120, anchor="center")
        tv_pagos.heading("monto", text="Monto (Gs)")
        tv_pagos.column("monto", width=140, anchor="e")

        # --------- CARGA / EVENTOS ---------
        def cargar_ventas():
            # limpiar tablas
            for it in tv_ventas.get_children():
                tv_ventas.delete(it)
            for it in tv_items.get_children():
                tv_items.delete(it)
            for it in tv_pagos.get_children():
                tv_pagos.delete(it)

            d1, d2 = normalizar_rango()
            txt = e_texto.get().strip().lower()
            like = f"%{txt}%"

            try:
                con = sqlite3.connect(db_path)
                cur = con.cursor()
                if txt:
                    cur.execute("""
                        SELECT v.id, v.fecha, COALESCE(u.username,'(sin usuario)') AS vendedor, v.modalidad, v.total
                        FROM ventas v
                        LEFT JOIN usuarios u ON u.id = v.usuario_id
                        WHERE v.fecha BETWEEN ? AND ?
                          AND (
                               LOWER(COALESCE(u.username,'')) LIKE ?
                            OR LOWER(COALESCE(v.modalidad,'')) LIKE ?
                            OR CAST(v.id AS TEXT) LIKE ?
                          )
                        ORDER BY v.id DESC
                    """, (d1, d2, like, like, like))
                else:
                    cur.execute("""
                        SELECT v.id, v.fecha, COALESCE(u.username,'(sin usuario)') AS vendedor, v.modalidad, v.total
                        FROM ventas v
                        LEFT JOIN usuarios u ON u.id = v.usuario_id
                        WHERE v.fecha BETWEEN ? AND ?
                        ORDER BY v.id DESC
                    """, (d1, d2))
                rows = cur.fetchall()
                con.close()

                total_gs = 0
                for vid, fecha, vend, mod, tot in rows:
                    total_gs += float(tot or 0)
                    tv_ventas.insert("", tk.END, values=(vid, fecha, vend, mod, f"{int(tot):,}".replace(",", ".")))
                lbl_total.config(text=f"Mostrando {len(rows)} ventas | Total: {int(total_gs):,} Gs".replace(",", "."))
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron cargar ventas: {e}")

        def cargar_detalle(event=None):
            # limpiar detalle
            for it in tv_items.get_children():
                tv_items.delete(it)
            for it in tv_pagos.get_children():
                tv_pagos.delete(it)

            sel = tv_ventas.selection()
            if not sel:
                return
            venta_id = tv_ventas.item(sel[0])["values"][0]
            try:
                con = sqlite3.connect(db_path)
                cur = con.cursor()

                # Ítems
                cur.execute("""
                    SELECT descripcion, IFNULL(peso_gramos,0), IFNULL(precio_por_gramo,0),
                           IFNULL(cantidad,1), subtotal, tipo
                    FROM venta_items
                    WHERE venta_id = ?
                    ORDER BY id ASC
                """, (venta_id,))
                for (desc, peso, pgr, cant, subt, tipo) in cur.fetchall():
                    tv_items.insert(
                        "", tk.END,
                        values=(
                            desc or "",
                            f"{float(peso):.2f}",
                            f"{int(pgr):,}".replace(",", "."),
                            int(cant),
                            f"{int(subt):,}".replace(",", "."),
                            tipo or "",
                        )
                    )

                # Pagos
                cur.execute("""
                    SELECT metodo, monto FROM pagos
                    WHERE venta_id = ?
                    ORDER BY id ASC
                """, (venta_id,))
                for (met, mon) in cur.fetchall():
                    tv_pagos.insert("", tk.END, values=(met, f"{int(mon):,}".replace(",", ".")))

                con.close()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el detalle de la venta #{venta_id}: {e}")

        tv_ventas.bind("<<TreeviewSelect>>", cargar_detalle)

        # Carga inicial
        cargar_ventas()
        # >>> ADDED: Cierre de Caja
    def open_cierre_caja(self):
        import datetime as dt

        win = tk.Toplevel(self.master)
        win.title("Cierre de Caja")
        win.geometry("520x420")
        win.resizable(False, False)

        # Ruta a la BD
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.db"))

        # Cabecera
        hoy_str = dt.date.today().isoformat()
        tk.Label(win, text=f"Cierre de Caja - {hoy_str}", font=("TkDefaultFont", 11, "bold")).pack(pady=(10, 6))

        # Contenedores
        frm_totales = tk.LabelFrame(win, text="Totales del día", padx=10, pady=10)
        frm_totales.pack(fill="x", padx=10, pady=(0, 8))

        frm_metodos = tk.LabelFrame(win, text="Desglose por método de pago", padx=10, pady=10)
        frm_metodos.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # Labels de totales
        lbl_cant = tk.Label(frm_totales, text="Ventas: 0")
        lbl_cant.grid(row=0, column=0, sticky="w", padx=4, pady=2)

        lbl_total = tk.Label(frm_totales, text="Total del día: 0 Gs", font=("TkDefaultFont", 10, "bold"))
        lbl_total.grid(row=0, column=1, sticky="e", padx=4, pady=2)

        # Tabla por método
        tv = ttk.Treeview(frm_metodos, columns=("metodo", "monto"), show="headings", height=8)
        tv.heading("metodo", text="Método")
        tv.heading("monto", text="Monto (Gs)")
        tv.column("metodo", width=180, anchor="center")
        tv.column("monto", width=160, anchor="e")
        tv.pack(fill="both", expand=True)

        def cargar_cierre():
            # limpiar
            for it in tv.get_children():
                tv.delete(it)

            try:
                con = sqlite3.connect(db_path)
                cur = con.cursor()

                # Ventas del día (fecha LIKE 'YYYY-MM-DD%')
                cur.execute("""
                    SELECT COUNT(*), COALESCE(SUM(total), 0)
                    FROM ventas
                    WHERE fecha LIKE ?
                """, (hoy_str + "%",))
                cant, total = cur.fetchone() or (0, 0)

                # Desglose por método
                cur.execute("""
                    SELECT p.metodo, COALESCE(SUM(p.monto), 0) AS monto
                    FROM pagos p
                    WHERE p.venta_id IN (
                        SELECT id FROM ventas WHERE fecha LIKE ?
                    )
                    GROUP BY p.metodo
                    ORDER BY monto DESC
                """, (hoy_str + "%",))
                desglose = cur.fetchall()
                con.close()

                # Totales
                lbl_cant.config(text=f"Ventas: {cant}")
                lbl_total.config(text=f"Total del día: {int(total):,} Gs".replace(",", "."))

                # Métodos
                for metodo, monto in desglose:
                    tv.insert("", tk.END, values=(metodo, f"{int(monto):,}".replace(",", ".")))

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo calcular el cierre: {e}")

        tk.Button(win, text="Actualizar", command=cargar_cierre).pack(pady=(0, 10))

        # Carga inicial
        cargar_cierre()
    # <<< ADDED

