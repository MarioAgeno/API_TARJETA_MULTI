import pyodbc

conn_str = (
    "DRIVER=ODBC Driver 11 for SQL Server;"
    "SERVER=SERVIDOR-APLICA\SQLEXPRESS;"
    "DATABASE=TarjetasInedity;"
    "UID=usrMAASoft;"
    "PWD=pswMAAS_!9G9"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✅ Conexión exitosa")
except Exception as e:
    print("❌ Error de conexión:", e)