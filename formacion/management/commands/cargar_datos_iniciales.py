from django.core.management.base import BaseCommand
from django.db import transaction

from formacion import contenido_inicial as datos
from formacion.models import (
    Curso, Departamento, Examen, Itinerario, ItinerarioCurso, Opcion, Pregunta, Puesto, Tema,
)


class Command(BaseCommand):
    help = "Carga departamentos, puestos, cursos de ejemplo, exámenes e itinerarios. No sobrescribe lo existente."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Crea también usuarios de prueba (admin y operarios).")

    @transaction.atomic
    def handle(self, *args, **opts):
        for i, (nombre_dep, puestos) in enumerate(datos.DEPARTAMENTOS.items()):
            dep, _ = Departamento.objects.get_or_create(nombre=nombre_dep, defaults={"orden": i})
            for j, (nombre, desc) in enumerate(puestos):
                Puesto.objects.get_or_create(departamento=dep, nombre=nombre, defaults={"descripcion": desc, "orden": j})

        for orden, c in enumerate(datos.CURSOS):
            curso, creado = Curso.objects.get_or_create(
                codigo=c["codigo"],
                defaults={
                    "titulo": c["titulo"], "descripcion": c["descripcion"], "categoria": c["categoria"],
                    "audiencia": c["audiencia"], "duracion_minutos": c["duracion"], "orden": orden,
                },
            )
            if not creado:
                continue
            for n, (titulo, texto) in enumerate(c["temas"], start=1):
                Tema.objects.create(curso=curso, orden=n, titulo=titulo, contenido=texto)
            examen = Examen.objects.create(
                curso=curso, instrucciones="Lee cada pregunta con atención y elige una sola respuesta."
            )
            for n, (enunciado, opciones, correcta, explicacion) in enumerate(c["preguntas"], start=1):
                p = Pregunta.objects.create(examen=examen, orden=n, enunciado=enunciado, explicacion=explicacion)
                for k, texto in enumerate(opciones):
                    Opcion.objects.create(pregunta=p, texto=texto, es_correcta=(k == correcta), orden=k)
            self.stdout.write(f"  Curso creado: {curso.titulo}")

        for it in datos.ITINERARIOS:
            itinerario, creado = Itinerario.objects.get_or_create(
                nombre=it["nombre"],
                defaults={
                    "descripcion": it.get("descripcion", ""), "orden": it["orden"],
                    "para_todo_interno": it.get("para_todo_interno", False),
                    "para_externos": it.get("para_externos", False),
                },
            )
            if not creado:
                continue
            itinerario.departamentos.set(Departamento.objects.filter(nombre__in=it.get("departamentos", [])))
            itinerario.puestos.set(Puesto.objects.filter(nombre__in=it.get("puestos", [])))
            for n, (codigo, dias) in enumerate(it["cursos"]):
                ItinerarioCurso.objects.create(
                    itinerario=itinerario, curso=Curso.objects.get(codigo=codigo), orden=n, dias_plazo=dias
                )
            self.stdout.write(f"  Itinerario creado: {itinerario.nombre}")

        if opts["demo"]:
            self._demo()
        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados."))

    def _demo(self):
        from django.contrib.auth import get_user_model

        from formacion.altas import dar_de_alta

        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "", "admin1234", first_name="Administración")
            self.stdout.write("  Usuario admin / admin1234 (cámbialo)")
        ejemplos = [
            ("Laura", "García Ruiz", "11111111H", "interno", "Recepción de mercancías", ""),
            ("Javier", "Martín Sanz", "22222222J", "interno", "Expediciones", ""),
            ("Pedro", "López Gil", "33333333P", "externo", None, "Transportes Ejemplo S.L."),
        ]
        for nombre, apellidos, dni, tipo, puesto, empresa in ejemplos:
            usuario, _, creado = dar_de_alta(nombre, apellidos, dni, tipo, Puesto.objects.filter(nombre=puesto).first(), empresa)
            if creado:
                usuario.perfil.set_pin("123456")
                usuario.perfil.save()
                self.stdout.write(f"  Operario {nombre}: DNI {dni} / PIN 123456")
