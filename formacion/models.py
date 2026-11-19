"""Modelo de datos del Portal de Formación.

Estructura:
    Departamento ─< Puesto
    Curso ─< Tema                 (temario: textos, PDF, vídeos)
    Curso ── Examen ─< Pregunta ─< Opcion   (examen tipo test)
    Itinerario ─< ItinerarioCurso >─ Curso  (packs: acogida, común de logística, específico de puesto…)
    PerfilEmpleado (interno/externo, puesto) → genera Matriculas a partir de los itinerarios
    Matricula, TemaLeido, Intento ─< RespuestaIntento  (seguimiento)
"""
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Puesto(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name="puestos")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["departamento", "orden", "nombre"]
        unique_together = [("departamento", "nombre")]

    def __str__(self):
        return f"{self.departamento} · {self.nombre}"


class Audiencia(models.TextChoices):
    INTERNO = "interno", "Personal interno"
    EXTERNO = "externo", "Personal externo"
    TODOS = "todos", "Interno y externo"


class Curso(models.Model):
    class Categoria(models.TextChoices):
        ACOGIDA = "acogida", "Acogida / nuevas incorporaciones"
        DEPARTAMENTO = "departamento", "Común de departamento"
        PUESTO = "puesto", "Específica de puesto"
        EXTERNO = "externo", "Personal externo"
        CONTINUA = "continua", "Formación continua"

    codigo = models.SlugField(max_length=60, unique=True, help_text="Identificador corto, p. ej. «manual-empleado».")
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=20, choices=Categoria.choices, default=Categoria.CONTINUA)
    audiencia = models.CharField(max_length=10, choices=Audiencia.choices, default=Audiencia.INTERNO)
    duracion_minutos = models.PositiveIntegerField("duración estimada (min)", default=30)
    version = models.CharField(max_length=20, default="1.0", help_text="Versión del temario (aparece en el certificado).")
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "titulo"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("formacion:curso", args=[self.codigo])

    @property
    def examen_activo(self):
        examen = getattr(self, "examen", None)
        if examen and examen.activo and examen.preguntas.exists():
            return examen
        return None


def ruta_material(instance, filename):
    return f"temarios/{instance.curso.codigo}/{filename}"


class Tema(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="temas")
    orden = models.PositiveIntegerField(default=1)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField(blank=True, help_text="Texto del tema. Las líneas en blanco separan párrafos; las líneas que empiezan por «- » se muestran como lista.")
    archivo = models.FileField(upload_to=ruta_material, blank=True, help_text="PDF, presentación o vídeo del temario.")
    enlace_video = models.URLField(blank=True, help_text="Enlace opcional a un vídeo (YouTube, SharePoint, Stream…).")

    class Meta:
        ordering = ["curso", "orden", "id"]

    def __str__(self):
        return f"{self.orden}. {self.titulo}"

    @property
    def es_pdf(self):
        return bool(self.archivo) and self.archivo.name.lower().endswith(".pdf")

    @property
    def es_video(self):
        return bool(self.archivo) and self.archivo.name.lower().rsplit(".", 1)[-1] in {"mp4", "webm", "ogg"}


class Examen(models.Model):
    curso = models.OneToOneField(Curso, on_delete=models.CASCADE, related_name="examen")
    instrucciones = models.TextField(blank=True)
    nota_minima = models.PositiveIntegerField(
        "nota mínima para aprobar (%)", default=70, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    preguntas_por_intento = models.PositiveIntegerField(
        default=0, help_text="0 = todas las preguntas. Si es menor que el total, se eligen al azar en cada intento."
    )
    intentos_maximos = models.PositiveIntegerField(default=3, help_text="0 = ilimitados.")
    tiempo_limite_minutos = models.PositiveIntegerField(default=0, help_text="0 = sin límite de tiempo.")
    barajar = models.BooleanField("barajar preguntas y respuestas", default=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "exámenes"

    def __str__(self):
        return f"Examen · {self.curso}"


class Pregunta(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="preguntas")
    orden = models.PositiveIntegerField(default=0)
    enunciado = models.TextField()
    explicacion = models.TextField(blank=True, help_text="Se muestra al revisar el examen.")

    class Meta:
        ordering = ["examen", "orden", "id"]

    def __str__(self):
        return self.enunciado[:80]


class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name="opciones")
    texto = models.CharField(max_length=500)
    es_correcta = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["pregunta", "orden", "id"]
        verbose_name = "opción"
        verbose_name_plural = "opciones"

    def __str__(self):
        return self.texto


class Itinerario(models.Model):
    """Pack de cursos que se asigna automáticamente según el perfil del empleado."""

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0, help_text="Orden en que se muestra en «Mi formación».")
    para_todo_interno = models.BooleanField(
        "para todo el personal interno", default=False, help_text="P. ej. el pack de acogida."
    )
    para_externos = models.BooleanField("para el personal externo", default=False)
    departamentos = models.ManyToManyField(Departamento, blank=True, related_name="itinerarios")
    puestos = models.ManyToManyField(Puesto, blank=True, related_name="itinerarios")
    cursos = models.ManyToManyField(Curso, through="ItinerarioCurso", related_name="itinerarios")
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class ItinerarioCurso(models.Model):
    itinerario = models.ForeignKey(Itinerario, on_delete=models.CASCADE, related_name="lineas")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    orden = models.PositiveIntegerField(default=0)
    dias_plazo = models.PositiveIntegerField(
        "plazo (días)", default=30, help_text="Días desde la incorporación/asignación para completarlo. 0 = sin plazo."
    )

    class Meta:
        ordering = ["itinerario", "orden"]
        unique_together = [("itinerario", "curso")]
        verbose_name = "curso del itinerario"
        verbose_name_plural = "cursos del itinerario"

    def __str__(self):
        return f"{self.itinerario} → {self.curso}"


class PerfilEmpleado(models.Model):
    class Tipo(models.TextChoices):
        INTERNO = "interno", "Interno"
        EXTERNO = "externo", "Externo"

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.INTERNO)
    puesto = models.ForeignKey(Puesto, on_delete=models.SET_NULL, null=True, blank=True, related_name="empleados")
    empresa = models.CharField(max_length=150, blank=True, help_text="Para personal externo: empresa a la que pertenece.")
    dni = models.CharField("DNI/NIE", max_length=20, blank=True)
    fecha_incorporacion = models.DateField(default=timezone.localdate)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="equipo"
    )
    # Acceso sencillo para operarios sin cuenta corporativa: DNI + PIN numérico.
    pin = models.CharField("PIN (cifrado)", max_length=128, blank=True, editable=False)
    intentos_fallidos = models.PositiveIntegerField(default=0, editable=False)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "perfil de empleado"
        verbose_name_plural = "perfiles de empleado"

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} ({self.get_tipo_display()})"

    @property
    def departamento(self):
        return self.puesto.departamento if self.puesto_id else None

    @staticmethod
    def normalizar_dni(valor):
        return "".join(c for c in (valor or "").upper() if c.isalnum())

    def save(self, *args, **kwargs):
        self.dni = self.normalizar_dni(self.dni)
        super().save(*args, **kwargs)

    def set_pin(self, pin):
        self.pin = make_password(pin)
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None

    def check_pin(self, pin):
        return bool(self.pin) and check_password(pin, self.pin)

    @property
    def bloqueado(self):
        return bool(self.bloqueado_hasta and self.bloqueado_hasta > timezone.now())


class Matricula(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="matriculas")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="matriculas")
    itinerario = models.ForeignKey(Itinerario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_asignacion = models.DateTimeField(default=timezone.now)
    fecha_limite = models.DateField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [("usuario", "curso")]
        ordering = ["fecha_asignacion"]
        verbose_name = "matrícula"

    def __str__(self):
        return f"{self.usuario} · {self.curso}"

    @property
    def completada(self):
        return self.fecha_completado is not None

    @property
    def vencida(self):
        return not self.completada and self.fecha_limite and self.fecha_limite < timezone.localdate()


class TemaLeido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="temas_leidos")
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name="lecturas")
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("usuario", "tema")]
        verbose_name = "tema leído"
        verbose_name_plural = "temas leídos"


class Intento(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="intentos")
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="intentos")
    inicio = models.DateTimeField(default=timezone.now)
    fin = models.DateTimeField(null=True, blank=True)
    preguntas = models.JSONField(default=list, help_text="IDs de las preguntas en el orden mostrado.")
    puntuacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    aprobado = models.BooleanField(default=False)

    class Meta:
        ordering = ["-inicio"]

    def __str__(self):
        return f"{self.usuario} · {self.examen} · {self.inicio:%d/%m/%Y %H:%M}"

    @property
    def finalizado(self):
        return self.fin is not None

    @property
    def limite(self):
        if self.examen.tiempo_limite_minutos:
            return self.inicio + timezone.timedelta(minutes=self.examen.tiempo_limite_minutos)
        return None


class RespuestaIntento(models.Model):
    intento = models.ForeignKey(Intento, on_delete=models.CASCADE, related_name="respuestas")
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    opcion = models.ForeignKey(Opcion, on_delete=models.SET_NULL, null=True, blank=True)
    correcta = models.BooleanField(default=False)

    class Meta:
        unique_together = [("intento", "pregunta")]
