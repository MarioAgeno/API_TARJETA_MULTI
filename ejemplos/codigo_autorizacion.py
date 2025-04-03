import hashlib
from datetime import datetime

def generar_codigo_autorizacion(id_comercio, id_tarjeta):
    # Obtenemos la fecha y hora actual
    fecha_hora_actual = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Concatenamos el ID del comercio, el ID de la tarjeta y la fecha y hora actual
    datos_concatenados = f"{id_comercio}-{id_tarjeta}-{fecha_hora_actual}"
    
    # Utilizamos un algoritmo de hashing para generar un código único
    codigo_autorizacion = hashlib.sha256(datos_concatenados.encode()).hexdigest()
    
    return codigo_autorizacion

# Ejemplo de uso
id_comercio = "COMERCIO123"
id_tarjeta = "TARJETA456"
codigo_autorizacion = generar_codigo_autorizacion(id_comercio, id_tarjeta)
print("Código de autorización:", codigo_autorizacion)