# JoyApp/printing.py
from datetime import datetime

class Printer:
    def __init__(self, modo="archivo", ruta="ticket.txt", escpos_device=None):
        """
        modo: 'archivo' (genera .txt) o 'escpos' (impresora térmica)
        ruta: nombre del archivo si modo = 'archivo'
        escpos_device: instancia de printer (python-escpos) si modo = 'escpos'
        """
        self.modo = modo
        self.ruta = ruta
        self.escpos_device = escpos_device

    def print_ticket(self, encabezado, items, pagos, totales):
        """
        encabezado: dict(nombre, telefono, ticket_id, vendedor, modalidad)
        items: lista de dict(descripcion, detalle, subtotal)
        pagos: lista de dict(metodo, monto)
        totales: dict(total)
        """
        lines = []
        lines.append(encabezado.get("nombre", "TIENDA"))
        if encabezado.get("telefono"):
            lines.append(f"Tel: {encabezado['telefono']}")
        lines.append("-" * 30)

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines.append(f"Ticket: {encabezado.get('ticket_id','')} {now}")
        lines.append(f"Vendedor: {encabezado.get('vendedor','')}")
        lines.append(f"Modalidad: {encabezado.get('modalidad','')}")
        lines.append("-" * 30)

        # Ítems
        for it in items:
            lines.append(it["descripcion"])
            if it.get("detalle"):
                lines.append(it["detalle"])
            lines.append(f"Subt: $ {int(it['subtotal']):,}".replace(",", "."))
            lines.append("-" * 30)

        # Totales
        lines.append(f"TOTAL: $ {int(totales['total']):,}".replace(",", "."))

        # Pagos
        for p in pagos:
            lines.append(f"Pago {p['metodo']}: $ {int(p['monto']):,}".replace(",", "."))

        output = "\n".join(lines) + "\n"

        if self.modo == "archivo":
            with open(self.ruta, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            # En producción: usar escpos
            if not self.escpos_device:
                raise RuntimeError("No hay impresora ESC/POS configurada")
            self.escpos_device.text(output)
            self.escpos_device.cut()

        return output
    