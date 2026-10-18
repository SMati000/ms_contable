from calendar import monthrange
from datetime import date


def generar_cuit(prefijo, serial):
    while True:
        cuerpo = f"{prefijo}{serial:08d}"
        digito = digito_verificador(cuerpo)
        if digito is not None:
            return f"{cuerpo}{digito}"
        serial += 1


def generar_cuil(dni, prefijo):
    for candidato in (prefijo, 23, 20, 27):
        cuerpo = f"{candidato}{dni}"
        digito = digito_verificador(cuerpo)
        if digito is not None:
            return f"{cuerpo}{digito}"
    raise ValueError("No se pudo generar un CUIL ficticio válido.")


def generar_cbu(serial):
    entidad_y_sucursal = f"285{serial % 10000:04d}"
    primer_digito = digito_cbu(entidad_y_sucursal, (7, 1, 3, 9, 7, 1, 3))
    cuenta = f"{serial:013d}"
    segundo_digito = digito_cbu(cuenta, (3, 9, 7, 1, 3, 9, 7, 1, 3, 9, 7, 1, 3))
    return f"{entidad_y_sucursal}{primer_digito}{cuenta}{segundo_digito}"


def digito_cbu(bloque, ponderadores):
    suma = sum(int(digito) * peso for digito, peso in zip(bloque, ponderadores))
    return (10 - suma % 10) % 10


def digito_verificador(cuerpo):
    ponderadores = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    suma = sum(int(digito) * peso for digito, peso in zip(cuerpo, ponderadores))
    digito = 11 - (suma % 11)
    if digito == 11:
        return 0
    return None if digito == 10 else digito


def desplazar_mes(fecha, desplazamiento):
    mes_cero = fecha.year * 12 + fecha.month - 1 + desplazamiento
    anio, mes_cero = divmod(mes_cero, 12)
    mes = mes_cero + 1
    dia = min(fecha.day, monthrange(anio, mes)[1])
    return date(anio, mes, dia)
