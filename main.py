from fastapi import FastAPI, HTTPException, Depends, Request
from tenants import require_tenant, resolve_tenant
from auth import require_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from routers.consultas import router as consultas_router
from routers.calculos import router as calcular_cuotas
from routers.grabaciones import router as grabaciones
from routers.usuario import router as usuario_router
from routers.auth_login import router as auth_login_router
from core.database import get_cliente_config
import os
import time

from typing import Annotated


#-- Cargar las variables de entorno (ya no se usa TOKEN_ACESO global)
load_dotenv()

app = FastAPI()
security = HTTPBearer()
app.title = "MAASoft - API Tarjetas de Compras"

@app.get("/_debug/tenant", dependencies=[Depends(require_tenant), Depends(require_user)])
def debug_tenant(tenant: dict = Depends(resolve_tenant)):
    return {"cuit": tenant["cuit"], "db_name": tenant["db_name"]}

@app.get("/_debug/token")
def debug_token(user: dict = Depends(require_user)):
    return {
        "now": int(time.time()),
        "iat": user.get("iat"),
        "exp": user.get("exp"),
        "sub": user.get("sub"),
    }

# -- Validar acceso solo si el token + CUIT coinciden
async def validar_acceso_docs(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    cuit = request.headers.get("CUIT-CLIENTE")
    
    if not cuit:
        raise HTTPException(status_code=400, detail="CUIT no provisto")

    cliente = get_cliente_config(cuit)
    if token != cliente.token_acceso:
        raise HTTPException(status_code=403, detail="Token inválido")

# -- Documentación protegida por token y CUIT
@app.get("/docs", response_class=HTMLResponse, include_in_schema=False, dependencies=[Depends(validar_acceso_docs)])
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Documentación")


@app.get("/openapi.json", include_in_schema=False, dependencies=[Depends(validar_acceso_docs)])
async def get_custom_openapi():
    openapi_schema = get_openapi(
        title="API Tarjetas de Compras",
        version="1.0.0",
        description="API para gestión de tarjetas y cálculos financieros",
        routes=app.routes,
        contact={"name": "MAASoft", "url": "http://maasoft.com.ar"},
    )
    return JSONResponse(openapi_schema)

# Página de bienvenida
@app.get('/', response_class=HTMLResponse, tags=['Inicio'])
async def mensaje():
    return '''
        <h1><a href='http://www.maasoft.com.ar'>MAASoft WEB</a></h1>
        <a href='/docs'>Documentación protegida</a>
    '''

# Alias útil para inyectar el usuario autenticado (claims del JWT)
User = Annotated[dict, Depends(require_user)]

# Helper de chequeo de rol (igual que en tu API Login)
def require_role(role: str):
    def _check(user: dict = Depends(require_user)):
        roles = user.get("roles", [])
        if role not in roles:
            raise HTTPException(status_code=403, detail="No autorizado")
        return user
    return _check

# /me -> quién soy (JWT)
@app.get("/me", tags=["auth"], dependencies=[Depends(require_tenant)])
def me(user: User):
    return {"sub": user["sub"], "name": user.get("name"), "roles": user.get("roles", [])}

# /comercios/secret -> requiere rol "Comercio"
@app.get("/comercios/secret", tags=["auth"], dependencies=[Depends(require_tenant)])
def solo_comercios(user: dict = Depends(require_role("Comercio"))):
    return {"ok": True, "msg": "Acceso autorizado para rol Comercio"}

# Login multi-tenant
app.include_router(auth_login_router, dependencies=[Depends(require_tenant)])

# -- Registrar routers (ya tienen validación por token + CUIT en cada uno)
app.include_router(consultas_router,  dependencies=[Depends(require_tenant), Depends(require_user)])
app.include_router(calcular_cuotas,   dependencies=[Depends(require_tenant), Depends(require_user)])
app.include_router(grabaciones,       dependencies=[Depends(require_tenant), Depends(require_user)])
app.include_router(usuario_router,    dependencies=[Depends(require_tenant), Depends(require_user)])


# -- Ejecución local (opcional)
'''
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5005)
'''
