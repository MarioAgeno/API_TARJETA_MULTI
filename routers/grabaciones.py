# API_TARJETA_MULTI\routers\grabaciones.py
from fastapi import APIRouter, HTTPException, status, Depends
from models.archivos import *
from datetime import datetime
import pyodbc
from typing import Optional
from tenants import get_conn 
from .calculos import TarjetaInput, calcular_cuotas

router = APIRouter()


def get_client_connection(conn: pyodbc.Connection = Depends(get_conn)):
    conn.autocommit = False
    return conn


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


def obtener_plan_info(conn: pyodbc.Connection, idplan: int):
    """Obtiene la tasa de interés y la cantidad de cuotas para el plan `idplan`
    desde la tabla tjPlanes. Lanza HTTPException si no puede obtener los datos.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT interes, cuotas FROM tjPlanes WHERE id = ?", [idplan])
        row = cursor.fetchone()
        
        if row and row[0] is not None:
            # Normalizar tipos
            try:
                tasa = float(row[0])
            except Exception:
                tasa = 0.0
            try:
                cuotas = int(row[1]) if row[1] is not None else 1
            except Exception:
                cuotas = 1
            return tasa, cuotas
        else:
            raise HTTPException(status_code=400, detail=f"No se encontró información del plan para idplan={idplan}.")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al obtener información del plan: {str(e)}")
    finally:
        if cursor:
            cursor.close()


def obtener_limites_tarjeta(conn: pyodbc.Connection, numero_tarjeta: str):
    """Llama al SP verLimites pasando el número de tarjeta y devuelve
    los límites (totales y mensuales) como diccionario.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("exec verLimites ?", [numero_tarjeta])
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"No se encontraron límites para tarjeta {numero_tarjeta}")
        # Intentar mapear nombres de columnas si están disponibles
        cols = [c[0] for c in cursor.description] if cursor.description else []
        if cols:
            return dict(zip(cols, row))
        # si no hay descripción, devolver tupla
        return {"result": row}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener límites: {str(e)}")
    finally:
        if cursor:
            cursor.close()


def obtener_consumido_tarjeta(conn: pyodbc.Connection, numero_tarjeta: str):
    """Llama al SP verConsumido pasando el número de tarjeta y devuelve
    las compras realizadas en el periodo actual como lista de dicts.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("exec verConsumido ?", [numero_tarjeta])
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description] if cursor.description else []
        if cols:
            return [dict(zip(cols, r)) for r in rows]
        return [tuple(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener consumido: {str(e)}")
    finally:
        if cursor:
            cursor.close()


@router.get("/ver_limites/{numero_tarjeta}", tags=["Tarjetas"])
async def ver_limites_endpoint(numero_tarjeta: str, conn: pyodbc.Connection = Depends(get_client_connection)):
    return obtener_limites_tarjeta(conn, numero_tarjeta)


@router.get("/ver_consumido/{numero_tarjeta}", tags=["Tarjetas"])
async def ver_consumido_endpoint(numero_tarjeta: str, conn: pyodbc.Connection = Depends(get_client_connection)):
    return obtener_consumido_tarjeta(conn, numero_tarjeta)


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
        cursor.execute("exec grabarSaldoTarjNuevo ?, ?, ?", [
            saldos_tarjeta.id, 
            saldos_tarjeta.importe,
            saldos_tarjeta.importe_cuota
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
    conn: pyodbc.Connection = Depends(get_client_connection)    
):
    cursor = None
    try:
        # Conexión y transacción ya gestionadas por get_client_connection

        # 2. Generar valores
        codigo_autorizacion = generar_codigo_autorizacion()
        nuevo_numero_cupon = await obtener_nuevo_numero_cupon(conn)

        # 3. Validaciones antes de grabar
        # Valido importe
        if compra.importe is None or compra.importe <= 0:
            raise HTTPException(status_code=400, detail="El importe de la compra debe ser mayor a cero")

        cursor = conn.cursor()

        # Validar que el comercio exista
        try:
            cursor.execute('SELECT id FROM tjComercios WHERE id = ?', [compra.idcomercio])
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Comercio id={compra.idcomercio} no existe")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al validar comercio: {str(e)}")

        # Validar plan exista y esté activo, y obtener tasa/cuotas
        try:
            cursor.execute('SELECT activo, interes, cuotas FROM tjPlanes WHERE id = ?', [compra.idplan])
            plan_row = cursor.fetchone()
            if not plan_row:
                raise HTTPException(status_code=400, detail=f"Plan id={compra.idplan} no existe")
            activo_plan = plan_row[0]
            tasa_interes_mensual = float(plan_row[1]) if plan_row[1] is not None else 0.0
            cantidad_cuotas = int(plan_row[2]) if plan_row[2] is not None else 1
            if not activo_plan:
                raise HTTPException(status_code=400, detail=f"Plan id={compra.idplan} no está activo")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al validar plan: {str(e)}")

        # Calcular importe de cuota
        tarjeta_input = TarjetaInput(monto=compra.importe, tasa_interes_mensual=tasa_interes_mensual, cuotas=cantidad_cuotas)
        resultado_cuotas = calcular_cuotas(tarjeta_input)
        importe_cuota = 0.0
        if resultado_cuotas and getattr(resultado_cuotas, 'cuotas', None):
            importe_cuota = float(resultado_cuotas.cuotas[0].monto_cuota)

        # Validar tarjeta (estado, saldo total y saldo mes)
        try:
            cursor.execute('''
                SELECT t.id, tjLimites.tope, tjLimites.saldo, tjLimites.topemes, tjLimites.saldomes, t.estado
                FROM tjTarjetas t INNER JOIN tjLimites ON t.idtitular = tjLimites.idTarjeta
                WHERE t.id = ?
            ''', [compra.idtarjeta])
            tarjeta_row = cursor.fetchone()
            if not tarjeta_row:
                raise HTTPException(status_code=400, detail=f"Tarjeta id={compra.idtarjeta} no encontrada")
            saldo_total = float(tarjeta_row[2]) if tarjeta_row[2] is not None else 0.0
            topemes = float(tarjeta_row[3]) if tarjeta_row[3] is not None else 0.0
            saldomes = float(tarjeta_row[4]) if tarjeta_row[4] is not None else 0.0
            estado_tarjeta = int(tarjeta_row[5]) if tarjeta_row[5] is not None else 0
            if estado_tarjeta != 1:
                raise HTTPException(status_code=400, detail=f"Tarjeta id={compra.idtarjeta} no está activa")
            if saldo_total < compra.importe:
                raise HTTPException(status_code=400, detail=f"Saldo insuficiente en tarjeta: saldo={saldo_total}, importe={compra.importe}")
            if saldomes < importe_cuota:
                raise HTTPException(status_code=400, detail=f"Saldo mensual insuficiente: saldomes={saldomes}, cuota={importe_cuota}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al validar tarjeta: {str(e)}")

        # Validar que el consumido del periodo + compra no supere topemes
        try:
            # Ejecutar SP verConsumido y sumar importe
            cursor.execute('exec verConsumido ?', [compra.idtarjeta])
            consumos = cursor.fetchall()
            consumido_total = 0.0
            cols = [c[0].lower() for c in cursor.description] if cursor.description else []
            # Detectar columna de importe
            idx_importe = None
            for i, col in enumerate(cols):
                if 'importe' in col or 'monto' in col:
                    idx_importe = i
                    break
            for row in consumos:
                if idx_importe is not None:
                    val = row[idx_importe]
                else:
                    # buscar primer valor numérico
                    val = next((v for v in row if isinstance(v, (int, float))), 0)
                try:
                    consumido_total += float(val or 0)
                except Exception:
                    continue
            if (consumido_total + compra.importe) > topemes:
                raise HTTPException(status_code=400, detail=f"Límite mensual excedido: consumido={consumido_total}, importe={compra.importe}, topeMes={topemes}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al validar consumo mensual: {str(e)}")

        # 4. Ejecutar transacción: grabarCompra
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
        # Obtener datos del plan (tasa y cantidad de cuotas)
        tasa_interes_mensual, cantidad_cuotas = obtener_plan_info(conn, compra.idplan)

        # Calcular la cuota usando la función local (no vía HTTP)
        tarjeta_input = TarjetaInput(monto=compra.importe, tasa_interes_mensual=tasa_interes_mensual, cuotas=cantidad_cuotas)
        resultado_cuotas = calcular_cuotas(tarjeta_input)
        importe_cuota = 0.0
        if resultado_cuotas and getattr(resultado_cuotas, 'cuotas', None):
            # Tomamos la primera cuota (todas son iguales en la generación actual)
            importe_cuota = float(resultado_cuotas.cuotas[0].monto_cuota)

        # Ejecutar actualización de saldo pasando ahora el importe de la cuota
        cursor.execute("exec grabarSaldoTarjNuevo ?, ?, ?", [compra.idtarjeta, compra.importe, importe_cuota])
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
