# JoyApp/models.py
from typing import List, Tuple, Dict, Any
from .db import get_conn



# --------- MATERIALES ---------
def listar_materiales_activos() -> List[Tuple[int, str, str]]:
    """
    Devuelve [(id, nombre, ley)] de materiales activos, ordenados por nombre.
    OJO: la UI (nueva_venta) espera exactamente estas 3 columnas.
    """
    with get_conn() as con:
        rows = con.execute(
            "SELECT id, nombre, COALESCE(ley,'') "
            "FROM materiales WHERE activo=1 ORDER BY nombre"
        ).fetchall()
    return rows

def obtener_precios_material(material_id: int) -> Tuple[float, float]:
    """
    Devuelve (precio_gramo_mayor, precio_gramo_menor) para el material.
    """
    with get_conn() as con:
        row = con.execute(
            "SELECT precio_gramo_mayor, precio_gramo_menor "
            "FROM materiales WHERE id=?",
            (material_id,)
        ).fetchone()
    if not row:
        raise ValueError("Material no encontrado")
    return float(row[0]), float(row[1])

# --------- VENTAS ---------
def crear_venta(
    usuario_id: int,
    modalidad: str,
    items: List[Dict[str, Any]],
    pagos: List[Dict[str, Any]],
    caja_sesion_id: int | None = None
) -> int:
    """
    Crea venta + items + pagos en una transacción.
    fecha se guarda con datetime('now') (hora del sistema).
    Retorna venta_id.
    """
    total = sum(float(i["subtotal"]) for i in items)

    with get_conn() as con:
        cur = con.cursor()

        # Venta
        cur.execute(
            "INSERT INTO ventas (fecha, usuario_id, modalidad, caja_sesion_id, total) "
            "VALUES (datetime('now'), ?, ?, ?, ?)",
            (usuario_id, modalidad, caja_sesion_id, total)
        )
        venta_id = int(cur.lastrowid)

        # Ítems
        for it in items:
            cur.execute(
                "INSERT INTO venta_items "
                "(venta_id, material_id, descripcion, peso_gramos, precio_por_gramo, cantidad, subtotal, tipo) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    venta_id,
                    it.get("material_id"),
                    it.get("descripcion"),
                    it.get("peso_gramos"),
                    it.get("precio_por_gramo"),
                    it.get("cantidad", 1),
                    it["subtotal"],
                    it.get("tipo", "MATERIAL"),
                ),
            )

        # Pagos
        for p in pagos:
            cur.execute(
                "INSERT INTO pagos (venta_id, metodo, monto) VALUES (?,?,?)",
                (venta_id, p["metodo"], p["monto"])
            )

        con.commit()

    return venta_id
