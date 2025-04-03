import jwt 
import datetime

# Función para generar un token JWT
def generar_token(usuario_id, clave_secreta):
    # Definir los datos del payload (información del usuario)
    payload = {
        'usuario_id': usuario_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Expira en 1 día
    }
    # Generar el token con el payload y la clave secreta
    token = jwt.encode(payload, clave_secreta, algorithm='HS256')
    return token

# Función para verificar un token JWT
def verificar_token(token, clave_secreta):
    try:
        # Decodificar el token con la clave secreta
        payload = jwt.decode(token, clave_secreta, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        # Token expirado
        return 'Token expirado. Por favor inicia sesión nuevamente.'
    except jwt.InvalidTokenError:
        # Token inválido
        return 'Token inválido. Por favor inicia sesión nuevamente.'

# Ejemplo de uso
usuario_id = 'AMOREMIO'
clave_secreta = 'Esta_es_mi_clave_secreta'

# Generar un token para el usuario
token_generado = generar_token(usuario_id, clave_secreta)
print("Token generado:", token_generado)

# Verificar el token
resultado_verificacion = verificar_token(token_generado, clave_secreta)
print("Resultado de la verificación:", resultado_verificacion)
