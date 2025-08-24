# API_TARJETA_MULTI\core\database.py
import pyodbc
from fastapi import HTTPException, status
from models.archivos import ClienteConfig  # Importas el modelo existente
from typing import Optional
import os
from dotenv import load_dotenv

# Carga variables de entorno (opcional, pero recomendado)
load_dotenv()

# Configuración de la DB Maestra (desde variables de entorno o directamente)
MASTER_DB_CONFIG = {
    "driver": os.getenv("DB_MASTER_DRIVER", "{SQL Server}"),  # Default si no está en .env
    "server": os.getenv("DB_MASTER_SERVER", "TU_SERVER_MAESTRO"),
    "database": os.getenv("DB_MASTER_DATABASE", "TarjetasClientes"),
    "user": os.getenv("DB_MASTER_USER", "tu_user"),
    "password": os.getenv("DB_MASTER_PASSWORD", "tu_pass")
}

def get_cliente_config(cuit: str) -> ClienteConfig:
    """Obtiene configuración del cliente desde la DB maestra."""
    try:
        master_conn_str = (
            f"Driver={MASTER_DB_CONFIG['driver']};"
            f"Server={MASTER_DB_CONFIG['server']};"
            f"Database={MASTER_DB_CONFIG['database']};"
            f"UID={MASTER_DB_CONFIG['user']};"
            f"PWD={MASTER_DB_CONFIG['password']};"
        )
        
        with pyodbc.connect(master_conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, cuit, cliente, server, data_base, user_db, pass_udb, driver_odbc, token_acceso, activo "
                "FROM clientes WHERE cuit = ? AND activo = 1",
                cuit
            )
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente no registrado o inactivo"
                )
                
            # Convertir fila a diccionario (asumiendo que ClienteConfig en models/archivos.py tiene los mismos campos)
            columns = [column[0] for column in cursor.description]
            cliente_data = dict(zip(columns, row))
            return ClienteConfig(**cliente_data)
    
    except pyodbc.Error as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error al conectar a la DB maestra: {str(e)}"
        )

def get_db_connection(cliente: ClienteConfig) -> pyodbc.Connection:
    """Conecta a la base de datos específica del cliente."""
    try:
        conn_str = (
            f"Driver={cliente.driver_odbc};"
            f"Server={cliente.server};"
            f"Database={cliente.data_base};"
            f"UID={cliente.user_db};"
            f"PWD={cliente.pass_udb};"
        )
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al conectar a la DB del cliente {cliente.cuit}: {str(e)}"
        )