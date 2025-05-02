from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from routers.consultas import router as consultas_router
from routers.calculos import router as calcular_cuotas
from routers.grabaciones import router as grabaciones
from routers.usuario import router as usuario_router
from core.database import get_cliente_config
import os

#-- Cargar las variables de entorno (ya no se usa TOKEN_ACESO global)
load_dotenv()

app = FastAPI()
security = HTTPBearer()
app.title = "MAASoft - API Tarjetas de Compras"

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

# -- Registrar routers (ya tienen validación por token + CUIT en cada uno)
app.include_router(consultas_router)
app.include_router(calcular_cuotas)
app.include_router(grabaciones)
app.include_router(usuario_router)

# -- Ejecución local (opcional)
'''
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5005)
'''
