from django.urls import path

from . import views

app_name = "formacion"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("curso/<slug:codigo>/", views.curso_detalle, name="curso"),
    path("curso/<slug:codigo>/tema/<int:tema_id>/", views.tema_detalle, name="tema"),
    path("curso/<slug:codigo>/tema/<int:tema_id>/leido/", views.tema_marcar_leido, name="tema_leido"),
    path("curso/<slug:codigo>/examen/", views.examen_iniciar, name="examen_iniciar"),
    path("curso/<slug:codigo>/certificado/", views.certificado, name="certificado"),
    path("curso/<slug:codigo>/certificado/<int:usuario_id>/", views.certificado, name="certificado_usuario"),
    path("material/<int:tema_id>/", views.material, name="material"),
    path("examen/<int:intento_id>/", views.examen_realizar, name="examen"),
    path("examen/<int:intento_id>/resultado/", views.examen_resultado, name="resultado"),
    path("seguimiento/", views.seguimiento, name="seguimiento"),
    path("seguimiento/alta/", views.alta_empleados, name="alta"),
    path("seguimiento/<int:usuario_id>/", views.seguimiento_empleado, name="seguimiento_empleado"),
]
