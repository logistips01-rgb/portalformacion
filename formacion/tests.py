import io

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .admin import importar_preguntas_csv
from .altas import dar_de_alta, importar_empleados_csv
from .models import Curso, Intento, Matricula, Puesto
from .services import progreso_curso


class BaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos_iniciales", stdout=io.StringIO())

    def alta(self, puesto=None, tipo="interno", dni="12345678Z"):
        with self.captureOnCommitCallbacks(execute=True):
            usuario, pin, _ = dar_de_alta("Ana", "Prueba", dni, tipo, Puesto.objects.filter(nombre=puesto).first(), "Ext S.L.")
        return usuario, pin


class AsignacionTests(BaseTest):
    def test_recepcion_recibe_acogida_comun_y_especifico(self):
        usuario, _ = self.alta("Recepción de mercancías")
        codigos = set(Matricula.objects.filter(usuario=usuario).values_list("curso__codigo", flat=True))
        self.assertEqual(
            codigos,
            {"manual-empleado", "buenas-practicas-manipulacion", "seguridad-almacen", "trazabilidad-lotes", "recepcion-mercancias"},
        )

    def test_cambio_de_puesto_anade_cursos(self):
        usuario, _ = self.alta("Recepción de mercancías")
        perfil = usuario.perfil
        perfil.puesto = Puesto.objects.get(nombre="Expediciones")
        with self.captureOnCommitCallbacks(execute=True):
            perfil.save()
        self.assertTrue(Matricula.objects.filter(usuario=usuario, curso__codigo="expediciones").exists())

    def test_externo_solo_recibe_normas_externos(self):
        usuario, _ = self.alta(tipo="externo")
        codigos = list(Matricula.objects.filter(usuario=usuario).values_list("curso__codigo", flat=True))
        self.assertEqual(codigos, ["normas-personal-externo"])


class AccesoPinTests(BaseTest):
    def test_login_con_dni_y_pin(self):
        _, pin = self.alta("Expediciones")
        r = self.client.post(reverse("login"), {"username": "12345678-z", "password": pin})
        self.assertRedirects(r, reverse("formacion:inicio"), fetch_redirect_response=False)
        r = self.client.get(reverse("formacion:inicio"))
        self.assertContains(r, "Expediciones")
        self.assertContains(r, "Acogida Aldelis")

    def test_bloqueo_tras_intentos_fallidos(self):
        usuario, pin = self.alta()
        for _ in range(5):
            self.client.post(reverse("login"), {"username": "12345678Z", "password": "000000" if pin != "000000" else "111111"})
        usuario.perfil.refresh_from_db()
        self.assertTrue(usuario.perfil.bloqueado)
        r = self.client.post(reverse("login"), {"username": "12345678Z", "password": pin})
        self.assertEqual(r.status_code, 200)  # sigue en el login

    def test_no_accede_a_curso_no_asignado(self):
        usuario, _ = self.alta(tipo="externo")
        self.client.force_login(usuario)
        r = self.client.get(reverse("formacion:curso", args=["expediciones"]))
        self.assertEqual(r.status_code, 404)


class ExamenTests(BaseTest):
    def setUp(self):
        self.usuario, _ = self.alta("Expediciones")
        self.client.force_login(self.usuario)
        self.curso = Curso.objects.get(codigo="manual-empleado")

    def leer_temario(self):
        for tema in self.curso.temas.all():
            self.client.post(reverse("formacion:tema_leido", args=[self.curso.codigo, tema.id]))

    def responder(self, correctas=True):
        r = self.client.post(reverse("formacion:examen_iniciar", args=[self.curso.codigo]))
        intento = Intento.objects.filter(usuario=self.usuario).latest("inicio")
        self.assertRedirects(r, reverse("formacion:examen", args=[intento.id]))
        datos = {}
        for p in self.curso.examen.preguntas.all():
            datos[f"p{p.id}"] = p.opciones.get(es_correcta=correctas).id if correctas else p.opciones.filter(es_correcta=False).first().id
        self.client.post(reverse("formacion:examen", args=[intento.id]), datos)
        intento.refresh_from_db()
        return intento

    def test_examen_bloqueado_sin_temario(self):
        self.client.post(reverse("formacion:examen_iniciar", args=[self.curso.codigo]))
        self.assertFalse(Intento.objects.filter(usuario=self.usuario).exists())

    def test_aprobar_completa_curso_y_da_certificado(self):
        self.leer_temario()
        intento = self.responder(correctas=True)
        self.assertTrue(intento.aprobado)
        self.assertEqual(intento.puntuacion, 100)
        m = Matricula.objects.get(usuario=self.usuario, curso=self.curso)
        self.assertTrue(m.completada)
        r = self.client.get(reverse("formacion:certificado", args=[self.curso.codigo]))
        self.assertContains(r, "Certificado de formación")

    def test_suspender_y_agotar_intentos(self):
        self.leer_temario()
        for _ in range(3):
            self.assertFalse(self.responder(correctas=False).aprobado)
        self.assertTrue(progreso_curso(self.usuario, self.curso)["intentos_agotados"])
        self.client.post(reverse("formacion:examen_iniciar", args=[self.curso.codigo]))
        self.assertEqual(Intento.objects.filter(usuario=self.usuario).count(), 3)
        self.assertEqual(self.client.get(reverse("formacion:certificado", args=[self.curso.codigo])).status_code, 404)


class ImportacionTests(BaseTest):
    def test_importar_preguntas_csv(self):
        examen = Curso.objects.get(codigo="expediciones").examen
        antes = examen.preguntas.count()
        csv = "pregunta;opcion_a;opcion_b;opcion_c;opcion_d;correcta;explicacion\n" \
              "¿Uno?;a;b;c;d;C;porque sí\n¿Dos?;sí;no;;;A;\n"
        n, errores = importar_preguntas_csv(examen, csv)
        self.assertEqual((n, errores), (2, []))
        self.assertEqual(examen.preguntas.count(), antes + 2)
        p = examen.preguntas.get(enunciado="¿Uno?")
        self.assertEqual(p.opciones.get(es_correcta=True).texto, "c")
        self.assertEqual(p.explicacion, "porque sí")
        self.assertEqual(examen.preguntas.get(enunciado="¿Dos?").opciones.count(), 2)

    def test_importar_preguntas_con_error_no_guarda(self):
        examen = Curso.objects.get(codigo="expediciones").examen
        antes = examen.preguntas.count()
        n, errores = importar_preguntas_csv(examen, "¿Uno?;a;b;Z\n")
        self.assertEqual(n, 0)
        self.assertTrue(errores)
        self.assertEqual(examen.preguntas.count(), antes)

    def test_alta_masiva(self):
        csv = "nombre;apellidos;dni;tipo;puesto;empresa;fecha_incorporacion\n" \
              "Luis;Pérez;44444444A;interno;Expediciones;;01/12/2026\n" \
              "Marta;Sol;55555555B;externo;;Limpiezas S.A.;\n"
        with self.captureOnCommitCallbacks(execute=True):
            fichas, errores = importar_empleados_csv(csv)
        self.assertEqual(errores, [])
        self.assertEqual(len(fichas), 2)
        self.assertTrue(all(f["pin"] and len(f["pin"]) == 6 for f in fichas))
        luis = get_user_model().objects.get(perfil__dni="44444444A")
        self.assertTrue(Matricula.objects.filter(usuario=luis, curso__codigo="expediciones").exists())

    def test_alta_masiva_puesto_inexistente(self):
        fichas, errores = importar_empleados_csv("Luis;Pérez;44444444A;interno;Astronauta;;\n")
        self.assertFalse(fichas)
        self.assertIn("Astronauta", errores[0])


class PanelTests(BaseTest):
    def test_seguimiento_solo_staff(self):
        usuario, _ = self.alta()
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse("formacion:seguimiento")).status_code, 302)
        admin = get_user_model().objects.create_superuser("rrhh", "", "x")
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse("formacion:seguimiento")), "Ana Prueba")
        r = self.client.get(reverse("formacion:seguimiento") + "?formato=csv")
        self.assertIn("Ana Prueba", r.content.decode("utf-8"))
        self.assertEqual(self.client.get(reverse("formacion:alta")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:formacion_examen_importar", args=[1])).status_code, 200)
