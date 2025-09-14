# JoyApp/auth.py
import bcrypt
from .db import get_conn

VALID_ROLES = {"JEFE", "VENDEDOR"}

def crear_usuario(username: str, password: str, rol: str):
    """
    Crea un usuario con contraseña hasheada (bcrypt).
    """
    if rol not in VALID_ROLES:
        raise ValueError("Rol inválido. Use 'JEFE' o 'VENDEDOR'.")
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    with get_conn() as con:
        con.execute(
            "INSERT INTO usuarios (username, password_hash, rol, activo) VALUES (?,?,?,1)",
            (username, pw_hash, rol),
        )
        con.commit()

def validar_login(username: str, password: str):
    """
    Valida el login y MIGRA automáticamente contraseñas legacy en texto plano a bcrypt.
    Devuelve dict {id, username, rol} si ok; si no, None.
    """
    with get_conn() as con:
        row = con.execute(
            "SELECT id, username, password_hash, rol, activo FROM usuarios WHERE username=?",
            (username,),
        ).fetchone()

    if not row or row[4] == 0:
        return None

    uid, uname, pw_hash, rol, _ = row

    # Aseguramos bytes para bcrypt
    stored = pw_hash.encode("utf-8") if isinstance(pw_hash, str) else pw_hash

    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), stored)
    except ValueError:
        # Hash inválido (probable texto plano). Intentar migrar si coincide.
        try:
            legacy = stored.decode("utf-8", "ignore")
        except Exception:
            legacy = str(stored)

        if password == legacy:
            new_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            with get_conn() as con:
                con.execute("UPDATE usuarios SET password_hash=? WHERE id=?", (new_hash, uid))
                con.commit()
            ok = True
        else:
            ok = False

    if ok:
        return {"id": uid, "username": uname, "rol": rol}
    return None
