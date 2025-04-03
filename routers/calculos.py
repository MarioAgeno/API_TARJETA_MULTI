from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class TarjetaInput(BaseModel):
    monto: float
    tasa_interes_mensual: float
    cuotas: int

class CuotaOutput(BaseModel):
    numero_cuota: int
    monto_cuota: float

class ResultadoCuotas(BaseModel):
    cuotas: list
    total_compra: float

def calcular_cuotas(tarjeta: TarjetaInput):
    m = 1
    capital = tarjeta.monto
    nTEM = tarjeta.tasa_interes_mensual / 100  # convertir tasa de porcentaje a decimal
    nTEM = ((1 + nTEM) ** m) - 1
    cuotas = tarjeta.cuotas
    if nTEM == 0:
        nAmorti = 1
        nValCta = capital * nAmorti / cuotas
    else:
        nAmorti = ((((1 + nTEM) ** cuotas) - 1) / (nTEM * (1 + nTEM) ** cuotas)) ** -1
        nValCta = round(capital * nAmorti,2)
    
    cuotas_generadas = []
    for i in range(1, cuotas + 1):
        cuotas_generadas.append(CuotaOutput(numero_cuota=i, monto_cuota=nValCta))
    
    total_compra = round(nValCta * cuotas,2)
    return ResultadoCuotas(cuotas=cuotas_generadas, total_compra=total_compra)

@router.get("/calcular_cuotas/", tags=['Calculos'])
async def calcular_cuotas_compra(monto: float, tasa_interes_mensual: float, cuotas: int):
    tarjeta = TarjetaInput(monto=monto, tasa_interes_mensual=tasa_interes_mensual, cuotas=cuotas)
    try:
        return calcular_cuotas(tarjeta)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

# Obtener resultados de los calculo por POST y JSON
@router.post("/calcular_cuotas/", tags=['Calculos'])
async def calcular_cuotas_compra(tarjeta: TarjetaInput):
    try:
        return calcular_cuotas(tarjeta)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

