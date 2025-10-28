# JoyApp/ui/nueva_venta.py
import tkinter as tk
from tkinter import ttk, messagebox

from ..models import listar_materiales_activos, obtener_precios_material, crear_venta
from ..pricing import precio_material, MENOR, MAYOR
from ..printing import Printer


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

        # --- Peso ---
        tk.Label(self, text="Peso (g)").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.e_peso = tk.Entry(self)
        self.e_peso.grid(row=2, column=1, padx=6, pady=6)

        # --- Botón agregar ---
        tk.Button(self, text="Agregar ítem", command=self.add_item).grid(row=3, column=0, columnspan=2, pady=(4, 8))

        # --- Tabla de ítems ---
        self.tree = ttk.Treeview(self, columns=("desc", "subt"), show="headings", height=6)
        self.tree.heading("desc", text="Descripción")
        self.tree.heading("subt", text="Subtotal")
        self.tree.column("desc", width=320)
        self.tree.column("subt", width=120, anchor="e")
        self.tree.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

        # --- Pagos ---
        tk.Label(self, text="Pago efectivo").grid(row=5, column=0, sticky="e", padx=6, pady=2)
        self.e_ef = tk.Entry(self)
        self.e_ef.grid(row=5, column=1, padx=6, pady=2)

        tk.Label(self, text="Pago tarjeta").grid(row=6, column=0, sticky="e", padx=6, pady=2)
        self.e_tar = tk.Entry(self)
        self.e_tar.grid(row=6, column=1, padx=6, pady=2)

        tk.Label(self, text="Pago transferencia").grid(row=7, column=0, sticky="e", padx=6, pady=2)
        self.e_trf = tk.Entry(self)
        self.e_trf.grid(row=7, column=1, padx=6, pady=2)

        # --- Guardar venta ---
        tk.Button(self, text="Guardar + Imprimir", command=self.guardar).grid(row=8, column=0, columnspan=2, pady=10)

        # Estado interno
        self.items = []

        # Expansión
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(1, weight=1)

    # --- Función para agregar ítem ---
    def add_item(self):
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

    # --- Función para guardar venta ---
    def guardar(self):
        if not self.items:
            messagebox.showwarning("Atención", "Agregá al menos un ítem.")
            return

        pagos = []
        for metodo, entry in [("EFECTIVO", self.e_ef), ("TARJETA", self.e_tar), ("TRANSFERENCIA", self.e_trf)]:
            try:
                val = float(entry.get()) if entry.get() else 0.0
            except Exception:
                val = 0.0
            if val > 0:
                pagos.append({"metodo": metodo, "monto": val})

        total = sum(i["subtotal"] for i in self.items)
        pagado = sum(p["monto"] for p in pagos)
        if pagado < total:
            if not messagebox.askyesno("Confirmar", f"Pagos ({int(pagado)}) menores al total ({int(total)}). ¿Continuar?"):
                return

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
        for e in (self.e_ef, self.e_tar, self.e_trf):
            e.delete(0, tk.END)
