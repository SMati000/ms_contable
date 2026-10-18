from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections, transaction
from django.utils import timezone

from base_imponible.models import BaseImponible, ResultadoBaseImponible
from categoria_laboral.models import CategoriaLaboral
from concepto.models import Concepto, VersionConcepto
from empleado.choices import FormaPago
from empleado.models import Empleado, VersionEmpleado
from empresa.choices import TipoEmpleador
from empresa.models import Empresa
from grupo_concepto.models import GrupoConcepto
from liquidacion.choices import DebitoCredito, TipoEnvio, TipoLiquidacion, UnidadesLsd
from liquidacion.models import (
    DetalleLiquidacion,
    Liquidacion,
    LiquidacionEmpleado,
    TramoSituacionRevista,
)
from liquidacion.services.LiquidacionEmpleadoService import (
    LiquidacionEmpleadoService as InicializadorLiquidacionEmpleado,
)
from liquidacion.services.s_expresiones import (
    LiquidacionEmpleadoService as CalculadorLiquidacionEmpleado,
)
from plantilla_liquidacion.models import (
    DetallePlantillaLiquidacion,
    PlantillaLiquidacion,
)

from .catalog import BASES, CONCEPTOS, EMPLEADOS, EMPRESAS, GRUPOS
from .identifiers import desplazar_mes, generar_cbu, generar_cuil, generar_cuit


def validar_base_test():
    base = connections["default"].settings_dict
    ruta_actual = Path(base["NAME"]).resolve()
    ruta_test = (settings.BASE_DIR / "data" / "db_test.sqlite3").resolve()
    if base["ENGINE"] != "django.db.backends.sqlite3" or ruta_actual != ruta_test:
        raise ImproperlyConfigured(
            "Las herramientas de desarrollo solo pueden usar data/db_test.sqlite3."
        )


def asegurar_catalogos():
    grupos = {
        codigo: GrupoConcepto.objects.get_or_create(
            codigo=codigo,
            defaults={"denominacion": nombre},
        )[0]
        for codigo, nombre in GRUPOS
    }
    bases = {}
    for identificador, denominacion, descripcion, configurable in BASES:
        bases[identificador] = BaseImponible.objects.get_or_create(
            identificador=identificador,
            defaults={
                "denominacion": denominacion,
                "descripcion": descripcion,
                "configurable": configurable,
            },
        )[0]
    return grupos, bases


@transaction.atomic
def borrar_datos_de_negocio():
    validar_base_test()
    for model in (
        TramoSituacionRevista,
        DetalleLiquidacion,
        ResultadoBaseImponible,
        LiquidacionEmpleado,
        Liquidacion,
        DetallePlantillaLiquidacion,
        PlantillaLiquidacion,
        VersionEmpleado,
        Empleado,
    ):
        model.objects.all().delete()
    VersionConcepto.todos.all().delete()
    Concepto.todos.all().hard_delete()
    CategoriaLaboral.objects.all().delete()
    Empresa.objects.all().delete()


@transaction.atomic
def generar_datos(reemplazar=False):
    validar_base_test()
    if reemplazar:
        borrar_datos_de_negocio()
        inicio = 1
        cantidad_empresas = len(TipoEmpleador.values)
    else:
        inicio = siguiente_lote()
        cantidad_empresas = 2
    grupos, bases = asegurar_catalogos()
    empresas = []
    for numero_lote in range(inicio, inicio + cantidad_empresas):
        empresa = crear_empresa(numero_lote)
        categorias = crear_categorias(empresa)
        conceptos = crear_conceptos(empresa, grupos, bases)
        empleados = crear_empleados(empresa, categorias, numero_lote)
        plantilla = crear_plantilla(empresa, conceptos)
        crear_liquidaciones(empresa, empleados, conceptos, numero_lote)
        empresas.append({
            "empresa": empresa.nombre,
            "empleados": len(empleados),
            "conceptos": len(conceptos),
            "plantilla": plantilla.denominacion,
        })
    return {"empresas": empresas}


def siguiente_lote():
    nombres = Empresa.objects.filter(nombre__startswith="Empresa Demo Test ")
    usados = []
    for nombre in nombres.values_list("nombre", flat=True):
        try:
            usados.append(int(nombre.split()[3]))
        except (IndexError, ValueError):
            continue
    candidato = max(usados, default=0) + 1
    while Empresa.objects.filter(
        nombre__startswith=f"Empresa Demo Test {candidato:03d} "
    ).exists():
        candidato += 1
    return candidato


def crear_empresa(numero_lote):
    nombre = (
        f"Empresa Demo Test {numero_lote:03d} - "
        f"{EMPRESAS[(numero_lote - 1) % len(EMPRESAS)]}"
    )
    serial = 70000000 + numero_lote
    while True:
        cuit = generar_cuit("30", serial)
        if not Empresa.objects.filter(cuit=cuit).exists():
            break
        serial += 1
    empresa = Empresa(
        cuit=cuit,
        nombre=nombre,
        tipo_empleador=list(TipoEmpleador.values)[
            (numero_lote - 1) % len(TipoEmpleador.values)
        ],
        domicilio=f"Av. Test {numero_lote * 100} - Ciudad Demo",
    )
    empresa.full_clean()
    empresa.save()
    return empresa


def crear_categorias(empresa):
    return [
        CategoriaLaboral.objects.create(empresa=empresa, denominacion=nombre)
        for nombre in ("Administrativo", "Operativo", "Supervisión")
    ]


def crear_conceptos(empresa, grupos, bases):
    conceptos = []
    for numero, datos in enumerate(CONCEPTOS, start=1):
        nombre, categoria, tipo, unidad, grupo, bases_ids, unidades, formula = datos
        concepto = Concepto(empresa=empresa)
        concepto.full_clean()
        concepto.save()
        version = VersionConcepto(
            concepto=concepto,
            grupo=grupos.get(grupo),
            denominacion=nombre,
            codigo_arca=f"T{numero:05d}",
            categoria=categoria,
            tipo=tipo,
            unidad=unidad,
        )
        version.full_clean()
        version.save()
        version.bases_imponibles.set([bases[identificador] for identificador in bases_ids])
        conceptos.append({
            "concepto": concepto,
            "version": version,
            "nombre": nombre,
            "categoria": categoria,
            "tipo": tipo,
            "unidad": unidad,
            "unidades": Decimal(unidades),
            "formula": formula,
        })
    return conceptos


def crear_empleados(empresa, categorias, numero_lote):
    empleados = []
    for indice in range(4):
        nombre, apellido = EMPLEADOS[(numero_lote * 3 + indice) % len(EMPLEADOS)]
        serial = numero_lote * 1000 + indice + 1
        dni = str(40000000 + serial)
        while Empleado.objects.filter(dni=dni).exists():
            serial += 1
            dni = str(40000000 + serial)
        cuil = generar_cuil(dni, 20 if indice % 2 == 0 else 27)
        empleado = Empleado(
            empresa=empresa,
            dni=dni,
            cuil=cuil,
            apellidos=apellido,
            nombres=nombre,
            legajo=f"TEST-{numero_lote:03d}-{indice + 1:02d}",
            fecha_ingreso=timezone.localdate() - timedelta(days=365 * (indice + 1)),
        )
        empleado.full_clean()
        empleado.save()
        version = VersionEmpleado(
            empleado=empleado,
            conyuge=indice % 2 == 0,
            cantidad_hijos=indice % 3,
            codigo_obra_social="123456",
            categoria_laboral=categorias[indice % len(categorias)],
            dependencia_revista="Jornada completa",
            banco_de_cobro="Banco de Pruebas",
            forma_de_pago=list(FormaPago)[indice % len(FormaPago)],
            cbu=generar_cbu(serial) if indice % len(FormaPago) == 2 else "",
            cct=indice % 2 == 1,
            cobertura_scvo=True,
            corresponde_reduccion=False,
        )
        version.full_clean()
        version.save()
        empleados.append((empleado, version))
    return empleados


def crear_plantilla(empresa, conceptos):
    plantilla = PlantillaLiquidacion.objects.create(
        empresa=empresa,
        denominacion="Plantilla mensual de prueba",
    )
    detalles = []
    for datos in conceptos:
        detalle = DetallePlantillaLiquidacion(
            plantilla=plantilla,
            concepto=datos["concepto"],
            unidades=datos["unidades"],
            formula_base=datos["formula"],
            cantidad=Decimal("5") if datos["nombre"] == "Horas extra" else None,
            unidades_lsd=unidad_lsd(datos["unidad"]),
            debito_credito=debito_credito(datos["tipo"]),
        )
        detalle.full_clean()
        detalles.append(detalle)
    DetallePlantillaLiquidacion.objects.bulk_create(detalles)
    return plantilla


def crear_liquidaciones(empresa, empleados, conceptos, numero_lote):
    periodo_actual = timezone.localdate().replace(day=1)
    estados = (
        (-2, Liquidacion.Estado.CERRADA),
        (-1, Liquidacion.Estado.EN_RECTIFICACION),
        (0, Liquidacion.Estado.BORRADOR),
    )
    for desplazamiento, estado_final in estados:
        periodo = desplazar_mes(periodo_actual, desplazamiento)
        fecha_pago = desplazar_mes(periodo, 1).replace(day=5)
        liquidacion = Liquidacion(
            empresa=empresa,
            periodo=periodo,
            fecha_pago=fecha_pago,
            estado=Liquidacion.Estado.BORRADOR,
            tipo_envio=TipoEnvio.SJ,
            tipo_liquidacion=TipoLiquidacion.M,
            domicilio_empresa=empresa.domicilio,
        )
        liquidacion.full_clean()
        liquidacion.save()
        for indice, (empleado, version_empleado) in enumerate(empleados):
            entrada = LiquidacionEmpleado(
                liquidacion=liquidacion,
                empleado=empleado,
                version_empleado=version_empleado,
                observaciones_recibo="Recibo ficticio para pruebas",
                observaciones_lsd=f"Lote de test {numero_lote}",
                cantidad_dias_proporcionar_tope=30,
                unidad_tiempo_trabajado=LiquidacionEmpleado.UnidadTiempoTrabajado.D,
                tiempo_trabajado=30,
            )
            InicializadorLiquidacionEmpleado(entrada).crear()
            crear_detalles(entrada, conceptos, indice)
            CalculadorLiquidacionEmpleado(entrada).liquidar()
            crear_tramos(entrada)
        if estado_final != Liquidacion.Estado.BORRADOR:
            liquidacion.cerrar()
            if estado_final == Liquidacion.Estado.EN_RECTIFICACION:
                liquidacion.rectificar()


def crear_detalles(entrada, conceptos, variacion):
    factor = Decimal(1) + Decimal(variacion) / Decimal(20)
    detalles = []
    for datos in conceptos:
        detalle = DetalleLiquidacion(
            liquidacion_empleado=entrada,
            concepto=datos["version"],
            unidades=datos["unidades"],
            formula_base=str(Decimal(datos["formula"]) * factor),
            cantidad=Decimal("5") if datos["nombre"] == "Horas extra" else None,
            unidades_lsd=unidad_lsd(datos["unidad"]),
            debito_credito=debito_credito(datos["tipo"]),
        )
        detalle.full_clean()
        detalles.append(detalle)
    DetalleLiquidacion.objects.bulk_create(detalles)


def crear_tramos(entrada):
    tramos = [
        TramoSituacionRevista(
            liquidacion_empleado=entrada,
            codigo_situacion="01",
            dia_inicio=dia,
        )
        for dia in (1, 16)
    ]
    for tramo in tramos:
        tramo.full_clean()
    TramoSituacionRevista.objects.bulk_create(tramos)


def unidad_lsd(unidad):
    from concepto.choices import Unidad

    return UnidadesLsd.PORCENTAJE if unidad == Unidad.PORCENTAJE else UnidadesLsd.MONEDA


def debito_credito(tipo):
    from concepto.choices import Tipo

    return DebitoCredito.DEBITO if tipo == Tipo.DESCUENTO else DebitoCredito.CREDITO


def resumen_datos():
    validar_base_test()
    modelos = (
        ("Empresas", Empresa.objects),
        ("Categorías laborales", CategoriaLaboral.objects),
        ("Grupos de conceptos", GrupoConcepto.objects),
        ("Bases imponibles", BaseImponible.objects),
        ("Conceptos", Concepto.todos),
        ("Versiones de conceptos", VersionConcepto.todos),
        ("Empleados", Empleado.objects),
        ("Versiones de empleados", VersionEmpleado.objects),
        ("Plantillas", PlantillaLiquidacion.objects),
        ("Detalles de plantillas", DetallePlantillaLiquidacion.objects),
        ("Liquidaciones", Liquidacion.objects),
        ("Liquidaciones por empleado", LiquidacionEmpleado.objects),
        ("Detalles de liquidación", DetalleLiquidacion.objects),
        ("Tramos de situación de revista", TramoSituacionRevista.objects),
        ("Resultados de bases imponibles", ResultadoBaseImponible.objects),
    )
    return [
        {"nombre": nombre, "cantidad": manager.count(), "sistema": nombre in {
            "Grupos de conceptos", "Bases imponibles"
        }}
        for nombre, manager in modelos
    ]
