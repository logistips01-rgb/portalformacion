"""Lógica de negocio: asignación de itinerarios, progreso y corrección de exámenes."""
import random
from datetime import timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from .models import (
    Intento,
    Itinerario,
    Matricula,
    PerfilEmpleado,
    RespuestaIntento,
    Tema,
    TemaLeido,
)


def obtener_perfil(usuario):
    perfil, _ = PerfilEmpleado.objects.get_or_create(usuario=usuario)
    return perfil


def itinerarios_para(perfil):
    """Itinerarios que corresponden a un empleado según su tipo y puesto."""
    filtro = Q(pk__in=[])
    if perfil.tipo == PerfilEmpleado.Tipo.EXTERNO:
        filtro |= Q(para_externos=True)
    else:
        filtro |= Q(para_todo_interno=True)
    if perfil.puesto_id:
        filtro |= Q(puestos=perfil.puesto_id) | Q(departamentos=perfil.puesto.departamento_id)
    return Itinerario.objects.filter(filtro, activo=True).distinct().order_by("orden", "nombre")


def asignar_formacion(usuario):
    """Crea las matrículas que falten según los itinerarios del empleado. Devuelve cuántas se crearon."""
    if usuario.is_superuser:
        return 0  # cuentas de administración del sistema: no son alumnos
    perfil = obtener_perfil(usuario)
    base = perfil.fecha_incorporacion or timezone.localdate()
    hoy = timezone.localdate()
    creadas = 0
    for itinerario in itinerarios_para(perfil):
        for linea in itinerario.lineas.select_related("curso").filter(curso__activo=True):
            limite = None
            if linea.dias_plazo:
                # Si el itinerario se asigna tiempo después de la incorporación, el plazo cuenta desde hoy.
                limite = max(base, hoy) + timedelta(days=linea.dias_plazo)
            _, creada = Matricula.objects.get_or_create(
                usuario=usuario,
                curso=linea.curso,
                defaults={"itinerario": itinerario, "fecha_limite": limite},
            )
            creadas += int(creada)
    return creadas


def progreso_curso(usuario, curso):
    """Devuelve un dict con el estado del curso para el usuario."""
    temas = list(curso.temas.all())
    leidos = set(
        TemaLeido.objects.filter(usuario=usuario, tema__curso=curso).values_list("tema_id", flat=True)
    )
    examen = curso.examen_activo
    intentos = list(Intento.objects.filter(usuario=usuario, examen=examen, fin__isnull=False)) if examen else []
    aprobado = any(i.aprobado for i in intentos)
    pasos_total = len(temas) + (1 if examen else 0)
    pasos_hechos = len(leidos & {t.id for t in temas}) + (1 if aprobado else 0)
    temario_completo = all(t.id in leidos for t in temas)
    agotados = bool(examen and examen.intentos_maximos and len(intentos) >= examen.intentos_maximos and not aprobado)
    return {
        "temas": temas,
        "leidos": leidos,
        "examen": examen,
        "intentos": intentos,
        "aprobado": aprobado,
        "temario_completo": temario_completo,
        "intentos_agotados": agotados,
        "porcentaje": round(100 * pasos_hechos / pasos_total) if pasos_total else 100,
        "completado": temario_completo and (aprobado or not examen),
    }


def actualizar_matricula(usuario, curso):
    """Marca la matrícula como completada cuando se cumplen los requisitos."""
    prog = progreso_curso(usuario, curso)
    matricula, _ = Matricula.objects.get_or_create(usuario=usuario, curso=curso)
    if prog["completado"] and not matricula.completada:
        matricula.fecha_completado = timezone.now()
        mejor = max((i.puntuacion for i in prog["intentos"] if i.puntuacion is not None), default=None)
        matricula.nota = mejor
        matricula.save(update_fields=["fecha_completado", "nota"])
    return matricula


def marcar_tema_leido(usuario, tema: Tema):
    TemaLeido.objects.get_or_create(usuario=usuario, tema=tema)
    return actualizar_matricula(usuario, tema.curso)


def puede_iniciar_examen(usuario, examen):
    prog = progreso_curso(usuario, examen.curso)
    if not prog["temario_completo"]:
        return False, "Debes completar todos los temas antes de hacer el examen."
    if prog["aprobado"]:
        return False, "Ya has aprobado este examen."
    if prog["intentos_agotados"]:
        return False, "Has agotado los intentos. Contacta con tu responsable de formación."
    return True, ""


def iniciar_intento(usuario, examen):
    abierto = Intento.objects.filter(usuario=usuario, examen=examen, fin__isnull=True).first()
    if abierto and not intento_caducado(abierto):
        return abierto
    if abierto:
        corregir_intento(abierto, {})
    todas = list(examen.preguntas.values_list("id", flat=True))
    ids = list(todas)
    if examen.preguntas_por_intento and examen.preguntas_por_intento < len(ids):
        ids = random.sample(ids, examen.preguntas_por_intento)
    if examen.barajar:
        random.shuffle(ids)
    else:
        ids.sort(key=todas.index)
    return Intento.objects.create(usuario=usuario, examen=examen, preguntas=ids)


def intento_caducado(intento):
    # Se concede un margen de 30 s para el envío del formulario.
    return bool(intento.limite and timezone.now() > intento.limite + timedelta(seconds=30))


def corregir_intento(intento, respuestas):
    """`respuestas` es {pregunta_id: opcion_id}. Corrige, guarda y actualiza la matrícula."""
    examen = intento.examen
    preguntas = {p.id: p for p in examen.preguntas.filter(id__in=intento.preguntas).prefetch_related("opciones")}
    aciertos = 0
    for pid in intento.preguntas:
        pregunta = preguntas.get(pid)
        if not pregunta:
            continue
        opcion = next((o for o in pregunta.opciones.all() if o.id == respuestas.get(pid)), None)
        correcta = bool(opcion and opcion.es_correcta)
        aciertos += int(correcta)
        RespuestaIntento.objects.update_or_create(
            intento=intento, pregunta=pregunta, defaults={"opcion": opcion, "correcta": correcta}
        )
    total = len(preguntas) or 1
    intento.puntuacion = (Decimal(aciertos) * 100 / Decimal(total)).quantize(Decimal("0.01"))
    intento.aprobado = intento.puntuacion >= examen.nota_minima
    intento.fin = timezone.now()
    intento.save()
    actualizar_matricula(intento.usuario, examen.curso)
    return intento
