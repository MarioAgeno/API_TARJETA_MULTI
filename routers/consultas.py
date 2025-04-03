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


# Leer todos los Estados 
@router.get('/estados', response_model=List[Estados], tags=['Estado de Tarjetas'])
def leer_estados(conn: pyodbc.Connection = Depends(get_client_connection)):
	estados_db = []
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = 'SELECT id, nombre FROM tjEstados'
			cursor.execute(sentenciaSQL)
			tabla = cursor.fetchall()
			if tabla:
				for row in tabla:
					estado_list = Estados(
						id = row[0],
						nombre = row[1]
					)
					estados_db.append(estado_list)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
		)
	finally:
		conn.close()
	return estados_db


# Buscar un Estados de Tarjeta segun su ID
@router.get('/estados/', tags=['Estado de Tarjetas'])
def buscar_estado(id_estado: int, conn: pyodbc.Connection = Depends(get_client_connection)):
	estado_db = None
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = 'SELECT * FROM tjEstados WHERE id = ?'
			cursor.execute(sentenciaSQL, id_estado)
			registro = cursor.fetchone()
			if registro:
				estado_db = Estados(
					id = registro[0],
					nombre = registro[1]
				)
			else:
				return {'mensaje': 'Estado No Encontrado'}
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
			)
	finally:
		conn.close()
	return estado_db


# Leer todos los planes de pagos
@router.get('/planes', response_model=List[Planes], tags=['Planes de pagos'])
def leer_planes(conn: pyodbc.Connection = Depends(get_client_connection)):
	planes_db = []
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = 'SELECT * FROM tjPlanes'
			cursor.execute(sentenciaSQL)
			plan = cursor.fetchall()
			if plan:
				for row in plan:
					plan_list = Planes(
						id = row[0],
						nombre = row[1],
						cuotas = row[2],
						interes = row[3],
						costofin = row[4],
						vencimento = row[5],
						activo = row[6]
					)
					planes_db.append(plan_list)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
		)
	finally:
		conn.close()
	return planes_db


# Buscar un plan de pagos segun su ID
@router.get('/planes/', tags=['Planes de pagos'])
def buscar_plan(id_plan: int, conn: pyodbc.Connection = Depends(get_client_connection)):
	planes_db = None
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = 'SELECT * FROM tjPlanes WHERE id = ?'
			cursor.execute(sentenciaSQL, id_plan)
			plan = cursor.fetchone()
			if plan:
				planes_db = Planes(
					id = plan[0],
					nombre = plan[1],
					cuotas = plan[2],
					interes = plan[3],
					costofin = plan[4],
					vencimento = plan[5],
					activo = plan[6]
				)
			else:
				return {'mensaje': 'Plan No Encontrado'}
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
		)
	finally:
		conn.close()
	return planes_db


# Buscar los planes habilitados de un Comercio
@router.get('/planesComercios/', response_model=List[Planes_Comercios], tags=['Planes de pagos'])
def planes_comercios(id_comercio: int, conn: pyodbc.Connection = Depends(get_client_connection)):
	planes_db	= []
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = '''
						select * from tjPlanes where tjPlanes.id in 
						(select idPlan from tjPlanComercio where idComercio=?) and tjPlanes.activo = 1 
						and tjPlanes.vencimiento >= getdate()
						'''
			cursor.execute(sentenciaSQL, id_comercio)
			registros = cursor.fetchall()
			if registros:
				for row in registros:
					ultimas_compras_list = Planes_Comercios(
						id = row[0],
						nombre = row[1],
						cuotas = row[2],
						interes = row[3],
						costofin = row[4]
					)
					planes_db.append(ultimas_compras_list)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
		)
	finally:
		conn.close()
	return planes_db


# Leer ultimas 5 compras con una tarjeta
@router.get('/compras/', response_model=List[Ultimas_Compras], tags=['Registros de Compras'])
def ultimas_compras(id_tarjeta: int = 'ID Tarjeta', conn: pyodbc.Connection = Depends(get_client_connection)):
	ultimas_compras_db = []
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = 'EXEC UltComprasSocios_App ?'
			cursor.execute(sentenciaSQL, id_tarjeta)
			compras = cursor.fetchall()
			if compras:
				for row in compras:
					ultimas_compras_list = Ultimas_Compras(
						fecha = row[0],
						cupon = row[1],
						idcomercio = row[2],
						comercio = row[3],
						importe = row[4],
						idplan = row[5],
						id = row[6]
					)
					ultimas_compras_db.append(ultimas_compras_list)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
		)
	finally:
		conn.close()
	return ultimas_compras_db


# Obtener las cuotas de una compra segun ID de Compras
@router.get('/cuotas/', response_model=List[Detalle_Cuotas], tags=['Registros de Compras'])
def detalle_cuotas(id_compra: int, conn: pyodbc.Connection = Depends(get_client_connection)):
	detalle_cuotas_db = []
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = 'EXEC DetalleCuotas_App ?'
			cursor.execute(sentenciaSQL, id_compra)
			cuotas = cursor.fetchall()
			if cuotas:
				for row in cuotas:
					cuotas_list = Detalle_Cuotas(
						cuota = row[0],
						vencimento = row[1],
						importe = row[2],
						liquidacion = row[3]
					)
					detalle_cuotas_db.append(cuotas_list)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
		)
	finally:
		conn.close()
	return detalle_cuotas_db


# Buscar un Comercio segun su ID
@router.get('/comercios/', tags=['Registros de Compras'])
def buscar_comercio(id_comercio: int, conn: pyodbc.Connection = Depends(get_client_connection)):
	comercio_db = None
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = '''
			SELECT id, pin, comercio, nombre, domicilio, localidad, provincia, mail, sucursal, socio, cuit
				FROM tjComercios WHERE id = ?
			'''
			cursor.execute(sentenciaSQL, id_comercio)
			registro = cursor.fetchone()
			if registro:
				comercio_db = Comercios(
					id = registro[0],
					pin = registro[1],
					comercio = registro[2],
					nombre = registro[3],
					domicilio = registro[4],
					localidad = registro[5],
					provincia = registro[6],
					mail = registro[7],
					sucursal = registro[8],
					socio = registro[9],
					cuit = registro[10]
				)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
		)
	finally:
		conn.close()
	return comercio_db


# Buscar los cajas habilitados de un Comercio
@router.get('/cajasComercios/', response_model=List[Cajas_Comercio], tags=['Registros de Compras'])
def cajas_comercios(id_comercio: int, conn: pyodbc.Connection = Depends(get_client_connection)):
	caja_db = []
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = 'SELECT * FROM tjCajaComercios where idComercio = ?'
			cursor.execute(sentenciaSQL, (id_comercio,),)  # Agregar coma para formar tupla
			registros = cursor.fetchall()
			if registros:
				for row in registros:
					cajas_comercios_list = Cajas_Comercio(
						idCaja=row[0],
						idComercio=row[1],
						nombre_caja=row[2],
						fecha_creacion=row[3]
					)
					caja_db.append(cajas_comercios_list)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Error en la conexión: {str(e)}"  # Mostrar mensaje de error real
		)
	finally:
		conn.close()
	return caja_db


# Buscar una Tarjeta segun su ID
@router.get('/tarjetas/', tags=['Tarjetas Asociados'])
def buscar_tarjeta(id_tarjeta: int = 'ID Tarjeta', conn: pyodbc.Connection = Depends(get_client_connection)):
	tarjeta_db = None
	try:
		with conn.cursor() as cursor:
			sentenciaSQL = '''
			SELECT id, sucursal, socio, adicional, verificador, nombre, domicilio, localidad, provincia, mail, tope, saldo, estado, baja, vencimiento 
				from tjTarjetas WHERE id = ?
			'''
			cursor.execute(sentenciaSQL, id_tarjeta)
			registro = cursor.fetchone()
			if registro:
				tarjeta_db = Tarjetas(
					id = registro[0],
					sucursal = registro[1],
					socio = registro[2],
					adicional = registro[3],
					verificador = registro[4],
					nombre = registro[5],
					domicilio = registro[6],
					localidad = registro[7],
					provincia = registro[8],
					mail = registro[9],
					tope = registro[10],
					saldo = registro[11],
					estado = registro[12],
					baja = registro[13],
					vencimento = registro[14]
				)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="No se pudo establecer la conexión con el servidor!"
		)
	finally:
		conn.close()
	return tarjeta_db
