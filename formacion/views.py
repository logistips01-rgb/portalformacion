import csv
from collections import OrderedDict

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .altas import dar_de_alta, importar_empleados_csv
from .forms import AltaEmpleadoForm, AltaMasivaForm
from .models import Curso, Intento, Matricula, PerfilEmpleado, Puesto, Tema
from .services import (
    actualizar_matricula,
    asignar_formacion,
    corregir_intento,
    iniciar_intento,
    intento_caducado,
    marcar_tema_leido,
    obtener_perfil,
    progreso_curso,
    puede_iniciar_examen,
)


def _curso_accesible(request, codigo):
    curso = get_object_or_404(Curso, codigo=codigo, activo=True)
    if not request.user.is_staff and not Matricula.objects.filter(usuario=request.user, curso=curso).exists():
        raise Http404("No tienes asignado este curso.")
    return curso


def _resumen_usuario(usuario):
    """Matrículas del usuario agrupadas por itinerario con su progreso."""
    grupos = OrderedDict()
    matriculas = (
        Matricula.objects.filter(usuario=usuario, curso__activo=True)
        .select_related("curso", "itinerario")
        .order_by("itinerario__orden", "itinerario__nombre", "curso__orden")
    )
    total = completados = 0
    for m in matriculas:
        clave = m.itinerario.nombre if m.itinerario else "Otros cursos asignados"
        grupo = grupos.setdefault(
            clave, {"itinerario": m.itinerario, "elementos": [], "completados": 0}
        )
        prog = progreso_curso(usuario, m.curso)
        grupo["elementos"].append({"matricula": m, "curso": m.curso, "progreso": prog})
        grupo["completados"] += int(m.completada)
        total += 1
        completados += int(m.completada)
    for grupo in grupos.values():
        n = len(grupo["elementos"])
        grupo["porcentaje"] = round(100 * grupo["completados"] / n) if n else 0
    return {
        "grupos": grupos,
        "total": total,
        "completados": completados,
        "porcentaje": round(100 * completados / total) if total else 0,
        "vencidas": [m for m in matriculas if m.vencida],
    }


@login_required
def inicio(request):
    perfil = obtener_perfil(request.user)
    asignar_formacion(request.user)  # por si se han añadido itinerarios nuevos
    contexto = {"perfil": perfil, **_resumen_usuario(request.user)}
    return render(request, "formacion/inicio.html", contexto)


@login_required
def curso_detalle(request, codigo):
    curso = _curso_accesible(request, codigo)
    prog = progreso_curso(request.user, curso)
    matricula = Matricula.objects.filter(usuario=request.user, curso=curso).first()
    siguiente = next((t for t in prog["temas"] if t.id not in prog["leidos"]), None)
    return render(
        request,
        "formacion/curso.html",
        {"curso": curso, "p": prog, "matricula": matricula, "siguiente": siguiente},
    )


@login_required
def tema_detalle(request, codigo, tema_id):
    curso = _curso_accesible(request, codigo)
    tema = get_object_or_404(Tema, pk=tema_id, curso=curso)
    prog = progreso_curso(request.user, curso)
    temas = prog["temas"]
    idx = next(i for i, t in enumerate(temas) if t.id == tema.id)
    return render(
        request,
        "formacion/tema.html",
        {
            "curso": curso,
            "tema": tema,
            "p": prog,
            "anterior": temas[idx - 1] if idx > 0 else None,
            "posterior": temas[idx + 1] if idx + 1 < len(temas) else None,
            "leido": tema.id in prog["leidos"],
            "numero": idx + 1,
        },
    )


@login_required
@require_POST
def tema_marcar_leido(request, codigo, tema_id):
    curso = _curso_accesible(request, codigo)
    tema = get_object_or_404(Tema, pk=tema_id, curso=curso)
    marcar_tema_leido(request.user, tema)
    posterior = curso.temas.filter(orden__gt=tema.orden).first() or curso.temas.filter(
        orden=tema.orden, id__gt=tema.id
    ).first()
    if posterior:
        return redirect("formacion:tema", codigo=curso.codigo, tema_id=posterior.id)
    messages.success(request, "Has completado el temario.")
    return redirect("formacion:curso", codigo=curso.codigo)


@login_required
def material(request, tema_id):
    tema = get_object_or_404(Tema, pk=tema_id)
    _curso_accesible(request, tema.curso.codigo)
    if not tema.archivo:
        raise Http404
    descarga = request.GET.get("descargar") == "1"
    return FileResponse(tema.archivo.open("rb"), as_attachment=descarga, filename=tema.archivo.name.rsplit("/", 1)[-1])


@login_required
@require_POST
def examen_iniciar(request, codigo):
    curso = _curso_accesible(request, codigo)
    examen = curso.examen_activo
    if not examen:
        raise Http404
    ok, motivo = puede_iniciar_examen(request.user, examen)
    if not ok:
        messages.warning(request, motivo)
        return redirect("formacion:curso", codigo=curso.codigo)
    intento = iniciar_intento(request.user, examen)
    return redirect("formacion:examen", intento_id=intento.id)


@login_required
def examen_realizar(request, intento_id):
    intento = get_object_or_404(Intento, pk=intento_id, usuario=request.user)
    if intento.finalizado:
        return redirect("formacion:resultado", intento_id=intento.id)
    if request.method == "POST" or intento_caducado(intento):
        respuestas = {}
        for pid in intento.preguntas:
            valor = request.POST.get(f"p{pid}")
            if valor and valor.isdigit():
                respuestas[pid] = int(valor)
        corregir_intento(intento, respuestas)
        if not request.method == "POST":
            messages.warning(request, "Se agotó el tiempo del examen.")
        return redirect("formacion:resultado", intento_id=intento.id)

    examen = intento.examen
    por_id = {p.id: p for p in examen.preguntas.filter(id__in=intento.preguntas).prefetch_related("opciones")}
    preguntas = []
    for pid in intento.preguntas:
        p = por_id.get(pid)
        if not p:
            continue
        opciones = list(p.opciones.all())
        if examen.barajar:
            # Orden estable por intento para que no cambie al recargar la página.
            opciones.sort(key=lambda o: hash((intento.id, o.id)))
        preguntas.append({"pregunta": p, "opciones": opciones})
    segundos = None
    if intento.limite:
        segundos = max(0, int((intento.limite - timezone.now()).total_seconds()))
    return render(
        request,
        "formacion/examen.html",
        {"intento": intento, "examen": examen, "curso": examen.curso, "preguntas": preguntas, "segundos": segundos},
    )


@login_required
def examen_resultado(request, intento_id):
    filtro = {"pk": intento_id} if request.user.is_staff else {"pk": intento_id, "usuario": request.user}
    intento = get_object_or_404(Intento, **filtro)
    if not intento.finalizado:
        return redirect("formacion:examen", intento_id=intento.id)
    respuestas = {r.pregunta_id: r for r in intento.respuestas.select_related("opcion")}
    preguntas = []
    examen = intento.examen
    por_id = {p.id: p for p in examen.preguntas.filter(id__in=intento.preguntas).prefetch_related("opciones")}
    for pid in intento.preguntas:
        if pid in por_id:
            preguntas.append({"pregunta": por_id[pid], "respuesta": respuestas.get(pid)})
    prog = progreso_curso(intento.usuario, examen.curso)
    return render(
        request,
        "formacion/resultado.html",
        {
            "intento": intento,
            "examen": examen,
            "curso": examen.curso,
            "preguntas": preguntas,
            "aciertos": sum(1 for r in respuestas.values() if r.correcta),
            # Solo se revelan las respuestas correctas cuando el examen ya no se puede repetir.
            "mostrar_solucion": prog["aprobado"] or prog["intentos_agotados"],
            "p": prog,
        },
    )


@login_required
def certificado(request, codigo, usuario_id=None):
    usuario = request.user
    if usuario_id and request.user.is_staff:
        usuario = get_object_or_404(get_user_model(), pk=usuario_id)
    curso = get_object_or_404(Curso, codigo=codigo)
    matricula = actualizar_matricula(usuario, curso) if Matricula.objects.filter(usuario=usuario, curso=curso).exists() else None
    if not matricula or not matricula.completada:
        raise Http404("Curso no completado.")
    return render(
        request,
        "formacion/certificado.html",
        {"curso": curso, "matricula": matricula, "alumno": usuario, "perfil": obtener_perfil(usuario)},
    )


# ---------------------------------------------------------------------------
# Panel de seguimiento para responsables / RR. HH.
# ---------------------------------------------------------------------------


def _empleados_filtrados(request):
    usuarios = (
        get_user_model()
        .objects.filter(is_active=True, is_superuser=False, perfil__isnull=False)
        .select_related("perfil", "perfil__puesto", "perfil__puesto__departamento")
        .order_by("perfil__tipo", "last_name", "first_name", "username")
    )
    tipo = request.GET.get("tipo")
    puesto = request.GET.get("puesto")
    estado = request.GET.get("estado")
    q = request.GET.get("q", "").strip()
    if tipo:
        usuarios = usuarios.filter(perfil__tipo=tipo)
    if puesto:
        usuarios = usuarios.filter(perfil__puesto_id=puesto)
    if q:
        from django.db.models import Q

        usuarios = usuarios.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) | Q(perfil__empresa__icontains=q)
        )
    filas = []
    hoy = timezone.localdate()
    for u in usuarios:
        mats = list(u.matriculas.filter(curso__activo=True))
        total = len(mats)
        hechos = sum(1 for m in mats if m.completada)
        vencidos = sum(1 for m in mats if not m.completada and m.fecha_limite and m.fecha_limite < hoy)
        fila = {
            "usuario": u,
            "perfil": u.perfil,
            "total": total,
            "hechos": hechos,
            "vencidos": vencidos,
            "porcentaje": round(100 * hechos / total) if total else 0,
        }
        if estado == "pendiente" and (total == 0 or hechos == total):
            continue
        if estado == "completo" and (total == 0 or hechos < total):
            continue
        if estado == "vencido" and not vencidos:
            continue
        filas.append(fila)
    return filas


@staff_member_required
def seguimiento(request):
    filas = _empleados_filtrados(request)
    if request.GET.get("formato") == "csv":
        respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = 'attachment; filename="seguimiento_formacion.csv"'
        respuesta.write("﻿")  # BOM para que Excel abra bien los acentos
        w = csv.writer(respuesta, delimiter=";")
        w.writerow(["Usuario", "Nombre", "Tipo", "Empresa", "Puesto", "Incorporación", "Cursos", "Completados", "Vencidos", "% avance"])
        for f in filas:
            u, p = f["usuario"], f["perfil"]
            w.writerow([
                u.username, u.get_full_name(), p.get_tipo_display(), p.empresa, p.puesto or "",
                p.fecha_incorporacion.strftime("%d/%m/%Y") if p.fecha_incorporacion else "",
                f["total"], f["hechos"], f["vencidos"], f["porcentaje"],
            ])
        return respuesta
    return render(
        request,
        "formacion/seguimiento.html",
        {
            "filas": filas,
            "puestos": Puesto.objects.select_related("departamento"),
            "tipos": PerfilEmpleado.Tipo.choices,
            "filtros": request.GET,
        },
    )


@staff_member_required
def seguimiento_empleado(request, usuario_id):
    usuario = get_object_or_404(get_user_model(), pk=usuario_id)
    intentos = Intento.objects.filter(usuario=usuario, fin__isnull=False).select_related("examen__curso")
    return render(
        request,
        "formacion/seguimiento_empleado.html",
        {"alumno": usuario, "perfil": obtener_perfil(usuario), "intentos": intentos, **_resumen_usuario(usuario)},
    )


@staff_member_required
def alta_empleados(request):
    """Alta individual o masiva. Muestra las fichas con el PIN (solo se ven una vez)."""
    form = AltaEmpleadoForm(request.POST if request.POST.get("modo") == "individual" else None)
    form_masiva = AltaMasivaForm(
        request.POST if request.POST.get("modo") == "masiva" else None,
        request.FILES if request.POST.get("modo") == "masiva" else None,
    )
    if request.method == "POST":
        if request.POST.get("modo") == "individual" and form.is_valid():
            d = form.cleaned_data
            usuario, pin, creado = dar_de_alta(
                d["nombre"], d["apellidos"], d["dni"], d["tipo"], d["puesto"], d["empresa"],
                d["fecha_incorporacion"], d["regenerar_pin"],
            )
            fichas = [{"usuario": usuario, "perfil": usuario.perfil, "pin": pin, "creado": creado}]
            return render(request, "formacion/fichas_acceso.html", {"fichas": fichas})
        if request.POST.get("modo") == "masiva" and form_masiva.is_valid():
            datos = form_masiva.cleaned_data["archivo"].read()
            try:
                texto = datos.decode("utf-8-sig")
            except UnicodeDecodeError:
                texto = datos.decode("cp1252")
            fichas, errores = importar_empleados_csv(texto, form_masiva.cleaned_data["regenerar_pin"])
            if errores:
                for e in errores[:20]:
                    messages.error(request, e)
            else:
                return render(request, "formacion/fichas_acceso.html", {"fichas": fichas})
    return render(request, "formacion/alta.html", {"form": form, "form_masiva": form_masiva})
