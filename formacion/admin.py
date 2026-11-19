import csv
import io

from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    Curso,
    Departamento,
    Examen,
    Intento,
    Itinerario,
    ItinerarioCurso,
    Matricula,
    Opcion,
    PerfilEmpleado,
    Pregunta,
    Puesto,
    RespuestaIntento,
    Tema,
)
from .auth import generar_pin
from .services import asignar_formacion, itinerarios_para

User = get_user_model()


# ---------------------------------------------------------------------------
# Estructura organizativa
# ---------------------------------------------------------------------------


class PuestoInline(admin.TabularInline):
    model = Puesto
    extra = 0
    fields = ("nombre", "orden", "descripcion")


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "orden")
    inlines = [PuestoInline]


@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "departamento", "num_empleados")
    list_filter = ("departamento",)

    @admin.display(description="empleados")
    def num_empleados(self, obj):
        return obj.empleados.count()


# ---------------------------------------------------------------------------
# Cursos, temario y exámenes
# ---------------------------------------------------------------------------


class TemaInline(admin.StackedInline):
    model = Tema
    extra = 0
    fields = (("orden", "titulo"), "contenido", ("archivo", "enlace_video"))


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "audiencia", "num_temas", "num_preguntas", "version", "activo", "orden")
    list_filter = ("categoria", "audiencia", "activo")
    list_editable = ("orden", "activo")
    search_fields = ("titulo", "codigo", "descripcion")
    prepopulated_fields = {"codigo": ("titulo",)}
    inlines = [TemaInline]
    fieldsets = (
        (None, {"fields": ("titulo", "codigo", "descripcion")}),
        ("Clasificación", {"fields": (("categoria", "audiencia"), ("duracion_minutos", "version"), ("activo", "orden"))}),
    )

    @admin.display(description="temas")
    def num_temas(self, obj):
        return obj.temas.count()

    @admin.display(description="preguntas examen")
    def num_preguntas(self, obj):
        examen = getattr(obj, "examen", None)
        if not examen:
            return format_html('<a href="{}?curso={}">Crear examen</a>', reverse("admin:formacion_examen_add"), obj.pk)
        url = reverse("admin:formacion_examen_change", args=[examen.pk])
        return format_html('<a href="{}">{}</a>', url, examen.preguntas.count())


class OpcionInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        validas = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if len(validas) < 2:
            raise ValidationError("Cada pregunta necesita al menos 2 opciones.")
        correctas = sum(1 for f in validas if f.cleaned_data.get("es_correcta"))
        if correctas != 1:
            raise ValidationError("Marca exactamente una opción como correcta.")


class OpcionInline(admin.TabularInline):
    model = Opcion
    formset = OpcionInlineFormset
    extra = 4
    fields = ("texto", "es_correcta", "orden")


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ("enunciado_corto", "examen", "orden", "num_opciones")
    list_filter = ("examen__curso",)
    search_fields = ("enunciado",)
    inlines = [OpcionInline]

    @admin.display(description="pregunta")
    def enunciado_corto(self, obj):
        return obj.enunciado[:100]

    @admin.display(description="opciones")
    def num_opciones(self, obj):
        return obj.opciones.count()

    def response_add(self, request, obj, post_url_continue=None):
        if "_addanother" in request.POST:
            return redirect(f"{reverse('admin:formacion_pregunta_add')}?examen={obj.examen_id}&orden={obj.orden + 1}")
        return super().response_add(request, obj, post_url_continue)


class PreguntaInline(admin.TabularInline):
    model = Pregunta
    extra = 0
    fields = ("orden", "enunciado", "respuesta_correcta", "editar")
    readonly_fields = ("respuesta_correcta", "editar")
    show_change_link = False

    @admin.display(description="respuesta correcta")
    def respuesta_correcta(self, obj):
        correcta = obj.opciones.filter(es_correcta=True).first() if obj.pk else None
        return correcta.texto if correcta else "—"

    @admin.display(description="")
    def editar(self, obj):
        if not obj.pk:
            return ""
        return format_html('<a href="{}">Editar opciones</a>', reverse("admin:formacion_pregunta_change", args=[obj.pk]))


class ImportarPreguntasForm(forms.Form):
    archivo = forms.FileField(
        help_text="CSV separado por «;» con columnas: pregunta;opcion_a;opcion_b;opcion_c;opcion_d;correcta;explicacion "
        "(correcta = A, B, C o D). Se puede guardar desde Excel como «CSV (delimitado por punto y coma)»."
    )
    reemplazar = forms.BooleanField(required=False, help_text="Borrar las preguntas actuales antes de importar.")


def importar_preguntas_csv(examen, contenido: str, reemplazar=False):
    """Importa preguntas desde CSV. Devuelve (importadas, errores)."""
    muestra = contenido[:2000]
    delimitador = ";" if muestra.count(";") >= muestra.count(",") else ","
    lector = csv.reader(io.StringIO(contenido), delimiter=delimitador)
    filas = [f for f in lector if any(c.strip() for c in f)]
    if filas and filas[0] and filas[0][0].strip().lower() in {"pregunta", "enunciado"}:
        filas = filas[1:]
    errores, nuevas = [], []
    letras = "ABCDEFGH"
    for n, fila in enumerate(filas, start=1):
        fila = [c.strip() for c in fila]
        if len(fila) < 4:
            errores.append(f"Fila {n}: faltan columnas.")
            continue
        enunciado = fila[0]
        # La columna «correcta» es la última celda que contiene solo una letra A-H;
        # lo que haya detrás es la explicación (opcional).
        pos = next(
            (i for i in range(len(fila) - 1, 2, -1) if len(fila[i]) == 1 and fila[i].upper() in letras), None
        )
        if pos is None:
            errores.append(f"Fila {n}: no se encuentra la columna de respuesta correcta (A, B, C…).")
            continue
        correcta = fila[pos].upper()
        explicacion = " ".join(c for c in fila[pos + 1 :] if c)
        opciones = [o for o in fila[1:pos] if o]
        if len(opciones) < 2:
            errores.append(f"Fila {n}: se necesitan al menos 2 opciones.")
            continue
        if len(correcta) != 1 or correcta not in letras[: len(opciones)]:
            errores.append(f"Fila {n}: la respuesta correcta «{correcta}» no es válida.")
            continue
        nuevas.append((enunciado, opciones, letras.index(correcta), explicacion))
    if errores:
        return 0, errores
    with transaction.atomic():
        if reemplazar:
            examen.preguntas.all().delete()
        inicio = (examen.preguntas.order_by("-orden").values_list("orden", flat=True).first() or 0) + 1
        for i, (enunciado, opciones, idx_correcta, explicacion) in enumerate(nuevas):
            p = Pregunta.objects.create(examen=examen, enunciado=enunciado, explicacion=explicacion, orden=inicio + i)
            Opcion.objects.bulk_create(
                [Opcion(pregunta=p, texto=t, es_correcta=(j == idx_correcta), orden=j) for j, t in enumerate(opciones)]
            )
    return len(nuevas), []


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ("curso", "num_preguntas", "nota_minima", "intentos_maximos", "tiempo_limite_minutos", "activo")
    list_filter = ("activo", "curso__categoria")
    inlines = [PreguntaInline]
    change_form_template = "admin/formacion/examen/change_form.html"
    fieldsets = (
        (None, {"fields": ("curso", "instrucciones", "activo")}),
        ("Reglas", {"fields": (("nota_minima", "intentos_maximos"), ("preguntas_por_intento", "tiempo_limite_minutos"), "barajar")}),
    )

    @admin.display(description="preguntas")
    def num_preguntas(self, obj):
        return obj.preguntas.count()

    def get_urls(self):
        return [
            path("<int:pk>/importar/", self.admin_site.admin_view(self.importar_view), name="formacion_examen_importar"),
        ] + super().get_urls()

    def importar_view(self, request, pk):
        examen = get_object_or_404(Examen, pk=pk)
        form = ImportarPreguntasForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            datos = form.cleaned_data["archivo"].read()
            try:
                texto = datos.decode("utf-8-sig")
            except UnicodeDecodeError:
                texto = datos.decode("cp1252")  # CSV guardado por Excel en Windows
            n, errores = importar_preguntas_csv(examen, texto, form.cleaned_data["reemplazar"])
            if errores:
                for e in errores[:20]:
                    messages.error(request, e)
            else:
                messages.success(request, f"Se han importado {n} preguntas.")
                return redirect("admin:formacion_examen_change", examen.pk)
        contexto = {
            **self.admin_site.each_context(request),
            "title": f"Importar preguntas · {examen.curso}",
            "examen": examen,
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/formacion/examen/importar.html", contexto)


# ---------------------------------------------------------------------------
# Itinerarios (packs de formación)
# ---------------------------------------------------------------------------


class ItinerarioCursoInline(admin.TabularInline):
    model = ItinerarioCurso
    extra = 1
    autocomplete_fields = ("curso",)


@admin.register(Itinerario)
class ItinerarioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "destinatarios", "num_cursos", "orden", "activo")
    list_editable = ("orden", "activo")
    filter_horizontal = ("departamentos", "puestos")
    inlines = [ItinerarioCursoInline]
    actions = ["asignar_a_afectados"]
    fieldsets = (
        (None, {"fields": ("nombre", "descripcion", ("orden", "activo"))}),
        ("¿A quién se asigna?", {"fields": (("para_todo_interno", "para_externos"), "departamentos", "puestos")}),
    )

    @admin.display(description="cursos")
    def num_cursos(self, obj):
        return obj.lineas.count()

    @admin.display(description="se asigna a")
    def destinatarios(self, obj):
        partes = []
        if obj.para_todo_interno:
            partes.append("Todo el personal interno")
        if obj.para_externos:
            partes.append("Personal externo")
        partes += [str(d) for d in obj.departamentos.all()]
        partes += [p.nombre for p in obj.puestos.all()]
        return ", ".join(partes) or "—"

    @admin.action(description="Asignar a los empleados afectados (cursos nuevos)")
    def asignar_a_afectados(self, request, queryset):
        total = 0
        for perfil in PerfilEmpleado.objects.select_related("usuario", "puesto"):
            if set(itinerarios_para(perfil)) & set(queryset):
                total += asignar_formacion(perfil.usuario)
        self.message_user(request, f"Se han creado {total} matrículas nuevas.")


# ---------------------------------------------------------------------------
# Empleados
# ---------------------------------------------------------------------------


class PerfilForm(forms.ModelForm):
    nuevo_pin = forms.CharField(
        label="Nuevo PIN", required=False, max_length=8,
        help_text="Solo números (4 a 8 cifras). Déjalo vacío para no cambiarlo. "
        "También puedes usar la acción «Generar PIN nuevo» del listado.",
    )

    class Meta:
        model = PerfilEmpleado
        fields = "__all__"

    def clean_nuevo_pin(self):
        pin = self.cleaned_data["nuevo_pin"].strip()
        if pin and (not pin.isdigit() or not 4 <= len(pin) <= 8):
            raise ValidationError("El PIN debe tener entre 4 y 8 números.")
        return pin

    def save(self, commit=True):
        perfil = super().save(commit=False)
        if self.cleaned_data.get("nuevo_pin"):
            perfil.set_pin(self.cleaned_data["nuevo_pin"])
        if commit:
            perfil.save()
        return perfil


class PerfilInline(admin.StackedInline):
    model = PerfilEmpleado
    form = PerfilForm
    can_delete = False
    fk_name = "usuario"
    fields = (
        ("tipo", "puesto"), ("empresa", "dni"), ("fecha_incorporacion", "responsable"),
        ("nuevo_pin", "tiene_pin", "bloqueado_hasta"),
    )
    readonly_fields = ("tiene_pin",)
    autocomplete_fields = ("responsable",)

    @admin.display(description="¿Tiene PIN?", boolean=True)
    def tiene_pin(self, obj):
        return bool(obj and obj.pin)


class MatriculaInline(admin.TabularInline):
    model = Matricula
    extra = 0
    fields = ("curso", "itinerario", "fecha_limite", "fecha_completado", "nota")
    readonly_fields = ("fecha_completado", "nota")
    autocomplete_fields = ("curso",)


admin.site.unregister(User)


@admin.register(User)
class EmpleadoAdmin(UserAdmin):
    inlines = [PerfilInline, MatriculaInline]
    list_display = ("username", "first_name", "last_name", "tipo", "puesto", "avance", "is_staff", "is_active")
    list_filter = ("perfil__tipo", "perfil__puesto", "is_staff", "is_active")
    search_fields = ("username", "first_name", "last_name", "email", "perfil__empresa", "perfil__dni")
    actions = ["reasignar_formacion", "generar_pines"]

    @admin.display(description="tipo", ordering="perfil__tipo")
    def tipo(self, obj):
        return obj.perfil.get_tipo_display() if hasattr(obj, "perfil") else "—"

    @admin.display(description="puesto", ordering="perfil__puesto")
    def puesto(self, obj):
        return obj.perfil.puesto.nombre if hasattr(obj, "perfil") and obj.perfil.puesto else "—"

    @admin.display(description="avance")
    def avance(self, obj):
        total = obj.matriculas.count()
        hechos = obj.matriculas.filter(fecha_completado__isnull=False).count()
        if not total:
            return "—"
        url = reverse("formacion:seguimiento_empleado", args=[obj.pk])
        return format_html('<a href="{}">{}/{}</a>', url, hechos, total)

    @admin.action(description="Generar PIN nuevo e imprimir fichas de acceso")
    def generar_pines(self, request, queryset):
        fichas = []
        for usuario in queryset.select_related("perfil"):
            perfil, _ = PerfilEmpleado.objects.get_or_create(usuario=usuario)
            pin = generar_pin()
            perfil.set_pin(pin)
            perfil.save()
            fichas.append({"usuario": usuario, "perfil": perfil, "pin": pin})
        return render(request, "formacion/fichas_acceso.html", {"fichas": fichas})

    @admin.action(description="Asignar la formación que les corresponde")
    def reasignar_formacion(self, request, queryset):
        total = sum(asignar_formacion(u) for u in queryset)
        self.message_user(request, f"Se han creado {total} matrículas nuevas.", messages.SUCCESS)


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "curso", "itinerario", "fecha_asignacion", "fecha_limite", "fecha_completado", "nota")
    list_filter = ("curso", "itinerario", ("fecha_completado", admin.EmptyFieldListFilter))
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name", "curso__titulo")
    autocomplete_fields = ("usuario", "curso")
    date_hierarchy = "fecha_asignacion"


class RespuestaIntentoInline(admin.TabularInline):
    model = RespuestaIntento
    extra = 0
    can_delete = False
    readonly_fields = ("pregunta", "opcion", "correcta")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Intento)
class IntentoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "examen", "inicio", "fin", "puntuacion", "aprobado")
    list_filter = ("aprobado", "examen__curso")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name")
    readonly_fields = ("usuario", "examen", "inicio", "fin", "preguntas", "puntuacion", "aprobado")
    inlines = [RespuestaIntentoInline]

    def has_add_permission(self, request):
        return False
