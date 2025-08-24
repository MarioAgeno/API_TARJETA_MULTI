# routers/auth_login.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import pyodbc, time, uuid
from datetime import datetime, timezone
import jwt  # Usamos PyJWT como en tu auth.py

from tenants import resolve_tenant, get_conn            # DB del cliente elegida por CUIT + X-Cliente-Token
from settings import JWT_SECRET, JWT_ISSUER, JWT_AUDIENCE, JWT_EXPIRES_MIN
from security import verify_password_hash               # verificador AspNet Identity v2/v3

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(
    body: LoginIn,
    tenant: dict = Depends(resolve_tenant),             # resuelve CUIT-CLIENTE y X-Cliente-Token
    conn: pyodbc.Connection = Depends(get_conn),        # abre conexión a la DB del cliente
):
    """
    Autentica contra AspNet Identity en la base del CLIENTE (multi-tenant).
    Devuelve JWT con claims estándar y tenant=<CUIT>.
    """
    username = (body.username or "").strip()
    if not username or not body.password:
        raise HTTPException(status_code=400, detail="Usuario o contraseña vacíos")

    cursor = None
    try:
        cursor = conn.cursor()

        # Busca el usuario (ajustá campos si varían en tu esquema)
        cursor.execute("""
            SELECT TOP 1
                Id,
                UserName,
                PasswordHash,
                EmailConfirmed,
                LockoutEnabled,
                LockoutEndDateUtc,
                AccessFailedCount
            FROM AspNetUsers
            WHERE UserName = ?
        """, (username,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        user_id, user_name, password_hash, email_confirmed, lockout_enabled, lockout_end_utc, failed_count = row

        # Lockout: si corresponde
        if lockout_enabled and lockout_end_utc and isinstance(lockout_end_utc, datetime):
            if lockout_end_utc.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                raise HTTPException(status_code=423, detail="Cuenta bloqueada temporalmente")

        # Verificar contraseña (AspNet v2/v3)
        if not password_hash or not verify_password_hash(password_hash, body.password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        # Roles del usuario
        cursor.execute("""
            SELECT r.[Name]
            FROM AspNetUserRoles ur
            JOIN AspNetRoles r ON r.Id = ur.RoleId
            WHERE ur.UserId = ?
        """, (user_id,))
        roles = [r[0] for r in cursor.fetchall()]

        # Emitir JWT (compatible con tu auth.py)
        now = int(time.time())
        payload = {
            "sub": str(user_id),
            "name": user_name or username,
            "roles": roles or [],
            "tenant": tenant["cuit"],                 # atado al CUIT del request
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "iat": now,
            "exp": now + JWT_EXPIRES_MIN * 60,
            "jti": str(uuid.uuid4()),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        return {"access_token": token, "token_type": "Bearer", "expires_in": JWT_EXPIRES_MIN * 60}

    finally:
        try:
            if cursor:
                cursor.close()
        except:
            pass
