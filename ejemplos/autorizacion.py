from datetime import datetime

# Obtenemos la fecha actual
fecha_actual = datetime.now()

# Obtenemos el día juliano utilizando strftime para formatear la fecha como "%j"
dia_juliano = fecha_actual.strftime("%j")

print("Día Juliano:", dia_juliano)

# Obtenemos la fecha y hora actual
fecha_hora_actual = datetime.now().strftime("%Y%m%d%H%M%S")
print("Fecha hora actual:", fecha_hora_actual)

codigo_autorizacion = dia_juliano+fecha_hora_actual[-6:]
print("Autorización", codigo_autorizacion)

