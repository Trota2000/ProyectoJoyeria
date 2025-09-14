        # JoyApp/pricing.py
from math import ceil
from typing import Literal

MENOR: Literal["MENOR"] = "MENOR"
MAYOR: Literal["MAYOR"] = "MAYOR"

def precio_material(precio_gramo: float, peso_gramos: float, modalidad: str) -> int:
    """
    - MAYOR: usa el precio por gramo tal cual.
    - MENOR: redondea el precio por gramo al alza a múltiplos de 1000.
    Devuelve el subtotal redondeado a entero (Gs).
    """
    if modalidad == MENOR:
        precio_aj = ceil(precio_gramo / 1000) * 1000
    else:
        precio_aj = precio_gramo
    subtotal = precio_aj * float(peso_gramos)
    return int(round(subtotal))

__all__ = ["MENOR", "MAYOR", "precio_material"]
