from fastapi import APIRouter, HTTPException
from models.archivos import *
from conexion_db import Conexion

router = APIRouter()

# Función para obtener un nuevo número de cupón
# Función para obtener un nuevo número de cupón
def obtener_nuevo_numero_cupon():
    try:
        conexion = Conexion.get_connection()
        cursor = conexion.cursor()

        # Ejecutar el procedimiento almacenado para obtener el nuevo número de cupón
        cursor.execute('UPDATE Numeros SET cupon = cupon + 1;')
        cursor.execute('exec UltCupon')

        # Ejecutar una consulta SELECT por separado para obtener el valor actualizado del cupón
        cursor.execute('SELECT cupon FROM Numeros;')
        cupon_data = cursor.fetchone()
        return cupon_data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

nuevo_numero_cupon = obtener_nuevo_numero_cupon()
print(nuevo_numero_cupon)