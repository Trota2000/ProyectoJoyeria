# JoyApp/ui/nueva_venta.py
import tkinter as tk
from tkinter import ttk, messagebox

from ..models import listar_materiales_activos, obtener_precios_material, crear_venta
from ..pricing import precio_material, MENOR, MAYOR
from ..printing import Printer

# >>> ADD: imports necesarios para leer stock desde la BD
import sqlite3, os
# <<< ADD


class NuevaVenta(tk.Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.pack(fill="both", expand=True)

        self.modalidad = tk.StringVar(value=MENOR)

        # --- Modalidad ---
        ttk.Radiobutton(self, text="Menor", variable=self.modalidad, value=MENOR).grid(row=0, column=0, padx=6, pady=6)
        ttk.Radiobutton(self, text="Mayor", variable=self.modalidad, value=MAYOR).grid(row=0, column=1, padx=6, pady=6)

        # --- Material con búsqueda y autocompletado ---
        tk.Label(self, text="Material").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.materiales = listar_materiales_activos()  # [(id, nombre, ley), ...]
        valores_materiales = [f"{m[1]} {m[2] or ''}".strip() for m in self.materiales]

        self.cbo_mat = ttk.Combobox(
            self,
            values=valores_materiales,
            state="normal",  # Permite escribir
            width=28,
        )
        self.cbo_mat.grid(row=1, column=1, padx=6, pady=6)

        # >>> ADD: etiqueta para mostrar stock del material seleccionado
        self.stock_var = tk.StringVar(value="Stock: -")
        tk.Label(self, textvariable=self.stock_var, fg="gray").grid(row=1, column=2, sticky="w", padx=6, pady=6)
        # <<< ADD

        # --- Autocompletado dinámico ---
        self._autocompletando = False

        def filtrar_y_autocompletar(event):
            if self._autocompletando:
                return

            texto = self.cbo_mat.get().strip().lower()
            filtrados = [v for v in valores_materiales if texto in v.lower()] if texto else valores_materiales
            self.cbo_mat["values"] = filtrados

            if not texto:
                return

            coincidencias = [v for v in valores_materiales if v.lower().startswith(texto)]
            if coincidencias:
                self._autocompletando = True
                self.cbo_mat.set(coincidencias[0])
                self.cbo_mat.icursor(len(texto))
                self.cbo_mat.selection_range(len(texto), tk.END)
                self._autocompletando = False

            if filtrados:
                self.cbo_mat.event_generate("<Down>")

        def seleccionar_primer_resultado(event):
            if self.cbo_mat["values"]:
                self.cbo_mat.set(self.cbo_mat["values"][0])

        self.cbo_mat.bind("<KeyRelease>", filtrar_y_autocompletar)
        self.cbo_mat.bind("<Return>", seleccionar_primer_resultado)

        # >>> ADD: helpers de stock
        def _db_path():
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.db"))

        def _leer_stock(material_id: int) -> float:
            try:
                con = sqlite3.connect(_db_path())
                cur = con.cursor()
                row = cur.execute("SELECT COALESCE(stock_gramos, 0) FROM materiales WHERE id=?", (material_id,)).fetchone()
                con.close()
                return float(row[0] if row else 0.0)
            except Exception:
                return 0.0

        def _refrescar_stock_label(event=None):
            idx = self.cbo_mat.current()
            if idx is None or idx < 0 or idx >= len(self.materiales):
                self.stock_var.set("Stock: -")
                return
            mat_id = int(self.materiales[idx][0])
            stock = _leer_stock(mat_id)
            self.stock_var.set(f"Stock: {stock:.2f} g")

        self.cbo_mat.bind("<<ComboboxSelected>>", _refrescar_stock_label)
        # <<< ADD

        # --- Peso ---
        tk.Label(self, text="Peso (g)").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.e_peso = tk.Entry(self)
        self.e_peso.grid(row=2, column=1, padx=6, pady=6)

        # >>> ADD: validar contra stock mientras escribe
        def _validar_peso_vs_stock(event=None):
            idx = self.cbo_mat.current()
            if idx is None or idx < 0 or idx >= len(self.materiales):
                return
            try:
                peso = float(self.e_peso.get().strip().replace(",", ".")) if self.e_peso.get().strip() else 0.0
            except Exception:
                peso = 0.0
            mat_id = int(self.materiales[idx][0])
            stock = _leer_stock(mat_id)
            if peso > stock > 0:
                self.stock_var.set(f"Stock: {stock:.2f} g  ⚠ Supera stock")
            else:
                self.stock_var.set(f"Stock: {stock:.2f} g")

        self.e_peso.bind("<KeyRelease>", _validar_peso_vs_stock)
        # <<< ADD

        # --- Botón agregar ---
        tk.Button(self, text="Agregar ítem", command=self.add_item).grid(row=3, column=0, columnspan=2, pady=(4, 8))

        # --- Tabla de ítems ---
        self.tree = ttk.Treeview(self, columns=("desc", "subt"), show="headings", height=6)
        self.tree.heading("desc", text="Descripción")
        self.tree.heading("subt", text="Subtotal")
        self.tree.column("desc", width=320)
        self.tree.column("subt", width=120, anchor="e")
        self.tree.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

        # >>> ADD: etiqueta de Total a la derecha de la tabla (misma fila)
        self.total_var = tk.StringVar(value="Total: 0 Gs")
        tk.Label(self, textvariable=self.total_var, font=("TkDefaultFont", 10, "bold")).grid(
            row=4, column=2, sticky="ne", padx=8, pady=(6, 0)
        )
        # <<< ADD

        # -------- Pagos: selección por clic (en lugar de carga manual) --------
        tk.Label(self, text="Método de pago").grid(row=5, column=0, sticky="e", padx=6, pady=(8, 2))
        self.metodo = tk.StringVar(value="")  # EFECTIVO / TARJETA / TRANSFERENCIA

        frm_pago = tk.Frame(self)
        frm_pago.grid(row=5, column=1, sticky="w", padx=6, pady=(8, 2))
        tk.Button(frm_pago, text="💵 Efectivo",
                  command=lambda: self.seleccionar_metodo("EFECTIVO")).pack(side="left", padx=4)
        tk.Button(frm_pago, text="💳 Tarjeta",
                  command=lambda: self.seleccionar_metodo("TARJETA")).pack(side="left", padx=4)
        tk.Button(frm_pago, text="🏦 Transferencia",
                  command=lambda: self.seleccionar_metodo("TRANSFERENCIA")).pack(side="left", padx=4)

        # Entrys de visualización (readonly)
        tk.Label(self, text="Pago efectivo").grid(row=6, column=0, sticky="e", padx=6, pady=2)
        self.e_ef = tk.Entry(self, state="readonly")
        self.e_ef.grid(row=6, column=1, padx=6, pady=2, sticky="we")

        tk.Label(self, text="Pago tarjeta").grid(row=7, column=0, sticky="e", padx=6, pady=2)
        self.e_tar = tk.Entry(self, state="readonly")
        self.e_tar.grid(row=7, column=1, padx=6, pady=2, sticky="we")

        tk.Label(self, text="Pago transferencia").grid(row=8, column=0, sticky="e", padx=6, pady=2)
        self.e_trf = tk.Entry(self, state="readonly")
        self.e_trf.grid(row=8, column=1, padx=6, pady=2, sticky="we")

        # --- Guardar venta ---
        tk.Button(self, text="Guardar + Imprimir", command=self.guardar).grid(row=9, column=0, columnspan=2, pady=10)

        # Estado interno
        self.items = []

        # Expansión
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(1, weight=1)

    # ---------- Utilidades de pago / total ----------
    def calcular_total_actual(self):
        return sum(i["subtotal"] for i in self.items)

    # >>> ADD: refrescar etiqueta de total
    def _refrescar_total_label(self):
        total = self.calcular_total_actual()
        self.total_var.set(f"Total: {int(round(total)):,} Gs".replace(",", "."))
    # <<< ADD

    def _set_entry_ro(self, entry, valor):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, "" if valor <= 0 else f"{int(round(valor))}")
        entry.config(state="readonly")

    def _refrescar_montos_segun_metodo(self):
        total = self.calcular_total_actual()
        ef = total if self.metodo.get() == "EFECTIVO" else 0
        ta = total if self.metodo.get() == "TARJETA" else 0
        tr = total if self.metodo.get() == "TRANSFERENCIA" else 0
        self._set_entry_ro(self.e_ef, ef)
        self._set_entry_ro(self.e_tar, ta)
        self._set_entry_ro(self.e_trf, tr)

    def seleccionar_metodo(self, metodo):
        self.metodo.set(metodo)
        # >>> ADD: asegura que el total esté actualizado al elegir método
        self._refrescar_total_label()
        # <<< ADD
        self._refrescar_montos_segun_metodo()

    # --- Función para agregar ítem ---
    def add_item(self):
        # >>> ADD: validación dura contra el stock antes de agregar
        idx_sel = self.cbo_mat.current()
        if idx_sel is None or idx_sel < 0 or idx_sel >= len(self.materiales):
            messagebox.showwarning("Atención", "Elegí un material.")
            return
        try:
            peso_ing = float(self.e_peso.get().strip().replace(",", "."))
            if peso_ing <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Peso inválido.")
            return

        mat_id_sel = int(self.materiales[idx_sel][0])

        # leer stock actual del material
        try:
            con = sqlite3.connect(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.db")))
            cur = con.cursor()
            row = cur.execute("SELECT COALESCE(stock_gramos, 0) FROM materiales WHERE id=?", (mat_id_sel,)).fetchone()
            con.close()
            stock_act = float(row[0] if row else 0.0)
        except Exception:
            stock_act = 0.0

        if peso_ing > stock_act:
            messagebox.showerror(
                "Stock insuficiente",
                f"El peso solicitado ({peso_ing:.2f} g) supera el stock disponible ({stock_act:.2f} g)."
            )
            try:
                self.stock_var.set(f"Stock: {stock_act:.2f} g")
            except Exception:
                pass
            return
        # <<< ADD

        idx = self.cbo_mat.current()
        if idx < 0:
            messagebox.showwarning("Atención", "Elegí un material.")
            return

        try:
            peso = float(self.e_peso.get())
            if peso <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Peso inválido.")
            return

        mat = self.materiales[idx]  # (id, nombre, ley)
        precios = obtener_precios_material(mat[0])  # (mayor, menor)
        pgr = precios[0] if self.modalidad.get() == MAYOR else precios[1]

        subtotal = precio_material(pgr, peso, self.modalidad.get())
        desc = f"{mat[1]} {mat[2] or ''} {peso} g @ {int(pgr)}"

        self.items.append({
            "material_id": mat[0],
            "descripcion": desc,
            "peso_gramos": peso,
            "precio_por_gramo": pgr,
            "cantidad": 1,
            "subtotal": subtotal,
            "tipo": "MATERIAL",
        })
        self.tree.insert("", "end", values=(desc, f"{int(subtotal):,}".replace(",", ".")))
        self.e_peso.delete(0, tk.END)

        # >>> ADD: actualizar total visible
        self._refrescar_total_label()
        # <<< ADD

        # Actualiza montos visibles según el método elegido
        if self.metodo.get():
            self._refrescar_montos_segun_metodo()

    # --- Función para guardar venta ---
    def guardar(self):
        if not self.items:
            messagebox.showwarning("Atención", "Agregá al menos un ítem.")
            return

        # Ahora el pago se selecciona por clic (un único método por venta)
        if not self.metodo.get():
            messagebox.showwarning("Atención", "Seleccioná un método de pago.")
            return

        total = self.calcular_total_actual()
        pagos = [{"metodo": self.metodo.get(), "monto": total}]

        venta_id = crear_venta(self.user["id"], self.modalidad.get(), self.items, pagos)

        printer = Printer(modo="archivo", ruta=f"ticket_{venta_id}.txt")
        encabezado = {
            "nombre": "ESTELA JOYAS",
            "telefono": "000-000-000",
            "ticket_id": str(venta_id),
            "vendedor": self.user.get("username", "Usuario"),
            "modalidad": self.modalidad.get(),
        }
        items_print = [{"descripcion": i["descripcion"], "detalle": None, "subtotal": i["subtotal"]} for i in self.items]
        totales = {"total": total}
        printer.print_ticket(encabezado, items_print, pagos, totales)

        messagebox.showinfo("OK", f"Venta #{venta_id} guardada. Ticket: ticket_{venta_id}.txt")

        # Reset general
        self.items.clear()
        for i in self.tree.get_children():
            self.tree.delete(i)

        # limpiar método/visualización
        self.metodo.set("")
        self._set_entry_ro(self.e_ef, 0)
        self._set_entry_ro(self.e_tar, 0)
        self._set_entry_ro(self.e_trf, 0)

        # >>> ADD: resetear total visible
        self._refrescar_total_label()
        # <<< ADD
