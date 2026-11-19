"""Acceso por DNI (o usuario) + PIN para personal sin cuenta corporativa."""
import secrets
from datetime import timedelta

from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from .models import PerfilEmpleado

MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 15


def generar_pin(longitud=6):
    return "".join(secrets.choice("0123456789") for _ in range(longitud))


class PinBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        dni = PerfilEmpleado.normalizar_dni(username)
        perfil = (
            PerfilEmpleado.objects.select_related("usuario").filter(dni=dni).exclude(dni="").first()
            or PerfilEmpleado.objects.select_related("usuario").filter(usuario__username__iexact=username.strip()).first()
        )
        if not perfil or not perfil.pin or perfil.bloqueado:
            return None
        if perfil.check_pin(password.strip()):
            if perfil.intentos_fallidos:
                perfil.intentos_fallidos = 0
                perfil.save(update_fields=["intentos_fallidos"])
            usuario = perfil.usuario
            return usuario if self.user_can_authenticate(usuario) else None
        perfil.intentos_fallidos += 1
        campos = ["intentos_fallidos"]
        if perfil.intentos_fallidos >= MAX_INTENTOS:
            perfil.bloqueado_hasta = timezone.now() + timedelta(minutes=MINUTOS_BLOQUEO)
            perfil.intentos_fallidos = 0
            campos.append("bloqueado_hasta")
        perfil.save(update_fields=campos)
        return None
