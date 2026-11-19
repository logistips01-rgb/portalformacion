from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PerfilEmpleado
from .services import asignar_formacion


@receiver(post_save, sender=PerfilEmpleado)
def asignar_al_guardar_perfil(sender, instance, **kwargs):
    """Al dar de alta o cambiar de puesto a un empleado se le asigna su pack de formación."""
    usuario = instance.usuario
    transaction.on_commit(lambda: asignar_formacion(usuario))
