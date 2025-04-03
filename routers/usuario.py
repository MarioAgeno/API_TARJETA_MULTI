from fastapi import APIRouter, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  
from typing import List
from models.archivos import *
from core.database import get_cliente_config
import pyodbc

router = APIRouter()
security = HTTPBearer()

# Dependencia para obtener la conexión del cliente
async def get_client_connection(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_cliente_cuit: str = Header(..., alias="CUIT-CLIENTE")
):
    try:
        # 1. Obtener token del header
        token = credentials.credentials
        
        # 2. Obtener configuración del cliente (implementa esta función)
        cliente = get_cliente_config(x_cliente_cuit)
        
        # 3. Validar token
        if token != cliente.token_acceso:
            raise HTTPException(status_code=403, detail="Token inválido")
        
        # 4. Crear conexión
        conn_str = f"Driver={cliente.driver_odbc};Server={cliente.server};Database={cliente.data_base};UID={cliente.user_db};PWD={cliente.pass_udb};"
        conn = pyodbc.connect(conn_str)
        return conn
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de autenticación: {str(e)}"
        )


# buscar un usuario por su login
# necesitamos el nombre de usuario
# para obtener el id del usuario y hacer la siguiente consulta
@router.get('/usuario/', tags=['Usuarios'])
def buscar_usuario(user_name: str, conn: pyodbc.Connection = Depends(get_client_connection)):
    user_db = None
    try:
        with conn.cursor() as cursor:
            sentenciaSQL = """
                SELECT u.Id, u.Email, u.EmailConfirmed, u.PasswordHash, 
                    u.SecurityStamp, u.PhoneNumber, u.PhoneNumberConfirmed, 
                    u.TwoFactorEnabled, u.LockoutEndDateUtc, u.LockoutEnabled, 
                    u.AccessFailedCount, u.UserName
                FROM AspNetUsers u
                WHERE UserName = ?
            """
            cursor.execute(sentenciaSQL, (user_name,))
            user = cursor.fetchone()
            if user:
                user_db = AspNetUsers(
                    Id=user[0],
                    Email=user[1],
                    EmailConfirmed=user[2],
                    PasswordHash=user[3],
                    SecurityStamp=user[4],
                    PhoneNumber=user[5],
                    PhoneNumberConfirmed=user[6],
                    TwoFactorEnabled=user[7],
                    LockoutEndDateUtc=user[8],
                    LockoutEnabled=user[9],
                    AccessFailedCount=user[10],
                    UserName=user[11]
                )
            else:
                return {'Mensaje': "Usuario no encontrado"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo establecer la conexión con el servidor!"
        )
    finally:
        conn.close()
    return user_db


# buscar un usuario Tarjeta Comercio
# con el ID del usuario que se obtuvo en la consulta anterior
@router.get('/TarjetaComercio/', tags=['Usuarios'])
def identificar_usuario(User_id: str, conn: pyodbc.Connection = Depends(get_client_connection)):
    user_db = None
    try:
        with conn.cursor() as cursor:
            sentenciaSQL = """
                SELECT socioid, tarjetaid, titular, comercioid, comercio, aspnetuserid
                FROM vwSociosTarjetasYComercios
                WHERE AspNetUserId = ?
            """
            cursor.execute(sentenciaSQL, (User_id,))
            user = cursor.fetchone()
            if user:
                user_db = Socio_Tarjeta_Comercio(
                    SocioId=user[0],
                    TarjetaId=user[1],
                    Titular=user[2],
                    ComercioId=user[3],
                    Comercio=user[4],
                    AspNetUserId=user[5]
                )
            else:
                return {'Mensaje': "Usuario no encontrado"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo establecer la conexión con el servidor!"
        )
    finally:
        conn.close()
    return user_db

