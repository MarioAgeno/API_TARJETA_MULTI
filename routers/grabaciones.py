from fastapi import APIRouter, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.archivos import *
from datetime import datetime
import pyodbc
from typing import Optional
from core.database import get_cliente_config

router = APIRouter()
security = HTTPBearer()

# --- Copiamos LA MISMA función de conexión que en consultas.py ---
async def get_client_connection(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_cliente_cuit: str = Header(..., alias="CUIT-CLIENTE")  # Mismo nombre de header
):
    try:
        # 1. Validar token
        token = credentials.credentials
        cliente = get_cliente_config(x_cliente_cuit)
        if token != cliente.token_acceso:
            raise HTTPException(status_code=403, detail="Token inválido")
        
        # 2. Crear conexión (igual que en consultas.py)
        conn_str = f"Driver={cliente.driver_odbc};Server={cliente.server};Database={cliente.data_base};UID={cliente.user_db};PWD={cliente.pass_udb};"
        conn = pyodbc.connect(conn_str)
        conn.autocommit = False  # Mantenemos control transaccional
        return conn
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de conexión: {str(e)}"
        )

# --- Funciones originales (iguales) ---
def generar_codigo_autorizacion():
    fecha_actual = datetime.now()
    dia_juliano = fecha_actual.strftime("%j")
    fecha_hora_actual = fecha_actual.strftime("%Y%m%d%H%M%S")
    return dia_juliano + fecha_hora_actual[-6:]

async def obtener_nuevo_numero_cupon(conn: pyodbc.Connection):  # Ahora es async
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE Numeros SET cupon = cupon + 1;')
        conn.commit()
        cursor.execute('SELECT cupon FROM Numeros;')
        return cursor.fetchone()[0]
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoints adaptados ---
# --- Grabar Compras de Tarjeta ---
@router.post("/grabar_compra/", tags=['Registros de Compras'])
async def grabar_compra_tarjeta(
    compra: Compras,
    conn: pyodbc.Connection = Depends(get_client_connection)
):
    cursor = None
    try:
        # Generar valores
        codigo_autorizacion = generar_codigo_autorizacion()
        nuevo_numero_cupon = await obtener_nuevo_numero_cupon(conn)
        
        # Configurar conexión SIN manejo de transacción (el SP lo hace internamente)
        conn.autocommit = True  # Cambio clave aquí
        
        # Ejecutar SP
        cursor = conn.cursor()
        cursor.execute("""
            DECLARE @id_compra INT;
            DECLARE @mensaje NVARCHAR(255);
            EXEC grabarCompra ?, ?, ?, ?, ?, ?, ?, ?, ?, @id_compra OUTPUT, @mensaje OUTPUT;
            SELECT @mensaje;
        """, [
            compra.idcomercio,
            compra.idtarjeta,
            compra.importe,
            compra.idplan,
            nuevo_numero_cupon,
            compra.carga or 'A',
            compra.fecha,
            codigo_autorizacion,
            compra.idcaja
        ])
        
        mensaje = cursor.fetchone()[0]
        return {"message": mensaje}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al grabar compra: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        # No cerramos la conexión aquí (la maneja FastAPI)


# --- Actualizar Saldo de Tarjeta ---
@router.put("/actualizar_saldo_tarjeta/", tags=['Tarjetas Asociados'])
async def actualizar_saldo(
    saldos_tarjeta: Saldo_Tarjeta,
    conn: pyodbc.Connection = Depends(get_client_connection)
):
    cursor = None
    try:
        conn.autocommit = True  # El SP maneja su propia transacción
        
        cursor = conn.cursor()
        cursor.execute("exec grabarSaldoTarj ?, ?", [
            saldos_tarjeta.id, 
            saldos_tarjeta.importe
        ])
        return {"message": "Saldo actualizado correctamente"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar saldo: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()


# --- Grabar Compra y Actualizar Saldo ---
# Este endpoint combina la funcionalidad de grabar una compra y actualizar el saldo de la tarjeta en una sola transacción.
# Se asegura de que ambas operaciones se realicen correctamente o ninguna de ellas se aplique.
@router.post("/grabar_compra_y_actualizar_saldo/", tags=['Registros de Compras'])
async def grabar_compra_y_actualizar_saldo_endpoint(
    compra: Compras,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_cliente_cuit: str = Header(..., alias="CUIT-CLIENTE")
):
    conn = None
    cursor = None
    try:
        # 1. Validar y conectar
        cliente = get_cliente_config(x_cliente_cuit)
        if credentials.credentials != cliente.token_acceso:
            raise HTTPException(status_code=403, detail="Token inválido")
        
        conn = pyodbc.connect(
            f"Driver={cliente.driver_odbc};"
            f"Server={cliente.server};"
            f"Database={cliente.data_base};"
            f"UID={cliente.user_db};"
            f"PWD={cliente.pass_udb};"
        )
        conn.autocommit = False

        # 2. Generar valores
        codigo_autorizacion = generar_codigo_autorizacion()
        nuevo_numero_cupon = await obtener_nuevo_numero_cupon(conn)

        # 3. Ejecutar transacción
        cursor = conn.cursor()
        cursor.execute("""
            DECLARE @id_compra INT;
            DECLARE @mensaje NVARCHAR(255);
            EXEC grabarCompra ?, ?, ?, ?, ?, ?, ?, ?, ?, @id_compra OUTPUT, @mensaje OUTPUT;
            SELECT @mensaje;
        """, [
            compra.idcomercio,
            compra.idtarjeta,
            compra.importe,
            compra.idplan,
            nuevo_numero_cupon,
            'A',
            compra.fecha,
            codigo_autorizacion,
            compra.idcaja
        ])
        mensaje = cursor.fetchone()[0]

        cursor.execute("exec grabarSaldoTarj ?, ?", [compra.idtarjeta, compra.importe])
        conn.commit()
        return {"message": mensaje}

    except HTTPException:
        raise  # Re-lanza las excepciones HTTP que ya manejamos
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()