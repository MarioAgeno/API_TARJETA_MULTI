API Tarjeta (Multi-tenant + JWT) — README
🧭 Resumen

API unificada que expone:

Login multi-tenant: autentica usuarios en la base de datos del cliente que llega en headers.

Endpoints de negocio: consultas, cálculos y grabaciones aisladas por cliente.

Autorización por roles (ej.: Comercio).

Un solo servicio FastAPI/uvicorn, con documentación Swagger.

Multi-tenant: cada request debe indicar el cliente (CUIT) y su token de acceso; la API resuelve la conexión a la BD SQL correspondiente y ejecuta ahí todo el flujo.

🔐 Modelo de Autenticación

La API usa 2 niveles por request:

Tenant (cliente)

Headers requeridos:

CUIT-CLIENTE: CUIT del cliente (elige la BD SQL)

X-Cliente-Token: token del cliente (autoriza el tenant)

La API busca la configuración del cliente (server, db, usuario, pass) y abre la conexión a esa base.

Usuario

JWT (Authorization: Bearer <token>) emitido por /auth/login.

Claims obligatorios: iss, aud, sub, exp (opcional: roles, tenant).

Expiración controlada por JWT_EXPIRES_MIN.

Recomendado (y soportado): incluir en el JWT el claim tenant con el CUIT; la API rechaza tokens cuyo tenant no coincida con el header.

📚 Endpoints principales
1) Login (multi-tenant)
POST /auth/login
Headers:
  CUIT-CLIENTE: <cuit del cliente>
  X-Cliente-Token: <token_acceso del cliente>
Body (JSON):
  { "username": "usuario", "password": "secreta" }


Resp (200):

{ "access_token": "...", "token_type": "Bearer", "expires_in": 600 }

2) Quién soy (JWT)
GET /me
Headers:
  Authorization: Bearer <JWT>
  CUIT-CLIENTE: <cuit>
  X-Cliente-Token: <token_acceso>


Resp (200):

{ "sub": "123", "name": "usuario", "roles": ["Comercio"] }

3) Solo rol Comercio
GET /comercios/secret
Headers: (igual que /me)


Resp (200):

{ "ok": true, "msg": "Acceso autorizado para rol Comercio" }

4) Negocio (ejemplos)
GET /planes
GET /estados
POST /grabar_compra/
...
Headers:
  Authorization: Bearer <JWT>
  CUIT-CLIENTE: <cuit>
  X-Cliente-Token: <token_acceso>

⚙️ Configuración

Variables necesarias (preferentemente en .env):

# JWT (emisión y verificación)
JWT_SECRET=pon_una_clave_segura
JWT_ISSUER=https://api.tu-dominio
JWT_AUDIENCE=tarjeta-multi-api
JWT_EXPIRES_MIN=10  # minutos

# Opcional: nombres de headers (defaults mostrados)
TENANT_HEADER_CUIT=CUIT-CLIENTE
TENANT_HEADER_TOKEN=X-Cliente-Token

# Conexión a la BD MAESTRA (fuente de truth de los clientes)
# Debe permitir que get_cliente_config(CUIT) obtenga server, db, user, pass, token_acceso
MASTER_ODBC_CONN_STR=DRIVER={SQL Server Native Client 11.0};SERVER=PCMARIO\\SQLEXPRESS;DATABASE=MAESTRA;UID=usuario;PWD=clave;Trusted_Connection=no;


No uses más DB_DRIVER/DB_SERVER/DB_DATABASE/... fijos: cada request se conecta dinámicamente a la BD del cliente.

¿Qué debe devolver get_cliente_config(cuit)?

Un objeto con, al menos:

cuit

token_acceso

driver_odbc

server

data_base

user_db

pass_udb

La API arma el connection string del tenant así:

Driver={driver_odbc};Server={server};Database={data_base};UID={user_db};PWD={pass_udb};

▶️ Puesta en marcha
# Requisitos: Python 3.11+, SQL Server ODBC (ej. Native Client 11)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000


Documentación: http://localhost:8000/docs

La UI de Swagger permite:

Hacer Authorize con tu JWT (tras login).

Setear headers CUIT-CLIENTE y X-Cliente-Token en cada call.

🧪 Quickstart (cURL)

Login (contra la BD del cliente):

curl -s -X POST http://localhost:8000/auth/login \
  -H "CUIT-CLIENTE: 30-12345678-9" \
  -H "X-Cliente-Token: TOKEN_CLIENTE" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo"}'


Usar JWT:

TOKEN=... # pegal el access_token de arriba

curl -s http://localhost:8000/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "CUIT-CLIENTE: 30-12345678-9" \
  -H "X-Cliente-Token: TOKEN_CLIENTE"


Negocio:

curl -s http://localhost:8000/planes \
  -H "Authorization: Bearer $TOKEN" \
  -H "CUIT-CLIENTE: 30-12345678-9" \
  -H "X-Cliente-Token: TOKEN_CLIENTE"

🚦 Errores comunes

401 Falta encabezado Authorization
No enviaste el JWT o está vencido.

401 Falta header CUIT-CLIENTE/X-Cliente-Token
Recordá que el tenant se resuelve en cada request.

401 Token del cliente inválido
X-Cliente-Token no coincide con el registrado para ese CUIT.

403 No autorizado
El rol del usuario no alcanza (ej. acceso a /comercios/secret sin rol Comercio).

423 Cuenta bloqueada
Usuario con lockout vigente en AspNetUsers.

🔧 Debug & soporte

Ver vencimiento del JWT: agregar temporalmente un endpoint de debug que muestre now, iat, exp.

Timeouts / conexión: revisar ODBC y credenciales del cliente.

CORS: si hay front web en otro dominio, habilitar CORSMiddleware.

🧩 Extender la API

Nuevos endpoints: usá el patrón actual:

from fastapi import APIRouter, Depends
import pyodbc
from tenants import get_conn
from auth import require_user

router = APIRouter()

def get_client_connection(conn: pyodbc.Connection = Depends(get_conn)):
    return conn

@router.get("/mi-endpoint")
def handler(conn: pyodbc.Connection = Depends(get_client_connection)):
    # usar conn.cursor() contra la BD del cliente
    ...


Proteger routers en main.py:

app.include_router(mi_router, dependencies=[Depends(require_tenant), Depends(require_user)])

🔐 Seguridad (recomendaciones)

Usar hash de contraseña (bcrypt/argon2) en AspNetUsers.

Considerar revocación de JWT por jti (Redis denylist) para “logout real” sin esperar exp.

Mantener JWT_SECRET fuera del repo (env/secret manager).

No loguear tokens ni credenciales; obscurizar IDs en logs.

🗺️ Migración desde modo Legacy

Antes: Authorization traía el token del cliente.

Ahora: Authorization trae JWT de usuario; el token del cliente va en X-Cliente-Token.

Todos los endpoints heredan tenant + JWT automáticamente vía include_router(..., dependencies=[...]).

📂 Estructura (resumen)
main.py
tenants.py                # resolve_tenant + get_conn (multi-tenant)
routers/
  auth_login.py           # login en la BD del cliente
  consultas.py
  calculos.py
  grabaciones.py
  usuario.py
core/
  database.py             # get_cliente_config(cuit) => credenciales del cliente
models/
  archivos.py             # modelos pydantic (según negocio)
auth.py                   # require_user (verifica JWT)
security.py               # helpers de hashing (si aplica)
settings.py               # constantes JWT / config

## 📘 Documentación Técnica

La documentación técnica (endpoints, parámetros, formatos de respuesta, errores comunes, etc.) está disponible para desarrolladores.  
Solicitá acceso escribiendo a: [mario@maasoft.com.ar](mailto:mario@maasoft.com.ar)

---

## 📞 Contacto

Si tenés dudas, problemas o querés comenzar a utilizar la API, podés comunicarte con:

**Mario Andrés Ageno**  
**MAASoft – Soluciones en Software**  
📧 Email: [mario@maasoft.com.ar](mailto:mario@maasoft.com.ar)  
🌐 Sitio web: [www.maasoft.com.ar](https://www.maasoft.com.ar)  
📱 Tel / WhatsApp: +54 3498 680413

---

> ⚠️ Esta API es parte del sistema de gestión de tarjetas de una entidad mutual. El uso indebido o no autorizado puede ser penalizado según los términos establecidos.
