# tenants.py  (reemplazar completo)
from typing import Dict, Optional
import pyodbc
from fastapi import Depends, Header, HTTPException
from core.database import get_cliente_config

def _unauthorized(detail="Tenant no autorizado"):
    raise HTTPException(status_code=401, detail=detail)

def resolve_tenant(
    cuit: Optional[str] = Header(None, alias="CUIT-CLIENTE"),
    token_cliente: Optional[str] = Header(None, alias="X-Cliente-Token"),
) -> Dict:
    """
    1) Lee CUIT-CLIENTE y X-Cliente-Token
    2) Busca config del cliente (DB maestra)
    3) Valida token_cliente
    4) Devuelve dict con datos + conn_str
    """
    if not cuit:
        _unauthorized("Falta header CUIT-CLIENTE")
    if not token_cliente:
        _unauthorized("Falta header X-Cliente-Token")

    cliente = get_cliente_config(cuit)
    if token_cliente != cliente.token_acceso:
        _unauthorized("Token del cliente inválido")

    conn_str = (
        f"Driver={cliente.driver_odbc};"
        f"Server={cliente.server};"
        f"Database={cliente.data_base};"
        f"UID={cliente.user_db};"
        f"PWD={cliente.pass_udb};"
    )
    return {
        "cuit": cliente.cuit,
        "db_server": cliente.server,
        "db_name": cliente.data_base,
        "conn_str": conn_str,
    }

def get_conn(tenant: Dict = Depends(resolve_tenant)) -> pyodbc.Connection:
    """Conexión a la BD del tenant (por request)."""
    return pyodbc.connect(tenant["conn_str"])

# Alias por compatibilidad con main.py
def require_tenant(tenant: Dict = Depends(resolve_tenant)) -> Dict:
    return tenant
