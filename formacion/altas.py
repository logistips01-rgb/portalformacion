"""Alta de empleados (individual o masiva desde Excel/CSV) con generación de PIN."""
import csv
import io
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import transaction

from .auth import generar_pin
from .models import PerfilEmpleado, Puesto

COLUMNAS = ["nombre", "apellidos", "dni", "tipo", "puesto", "empresa", "fecha_incorporacion"]


def _fecha(valor):
    valor = (valor or "").strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            pass
    return None


def buscar_puesto(texto):
    texto = (texto or "").strip()
    if not texto:
        return None
    return Puesto.objects.filter(nombre__iexact=texto).first() or Puesto.objects.filter(nombre__icontains=texto).first()


@transaction.atomic
def dar_de_alta(nombre, apellidos, dni, tipo="interno", puesto=None, empresa="", fecha=None, regenerar_pin=False):
    """Crea o actualiza un empleado identificado por su DNI. Devuelve (usuario, pin_o_None, creado)."""
    User = get_user_model()
    dni = PerfilEmpleado.normalizar_dni(dni)
    perfil = PerfilEmpleado.objects.select_related("usuario").filter(dni=dni).first()
    creado = perfil is None
    if creado:
        usuario = User(username=dni.lower(), first_name=nombre.strip(), last_name=apellidos.strip())
        usuario.set_unusable_password()
        usuario.save()
        perfil = PerfilEmpleado(usuario=usuario, dni=dni)
    else:
        usuario = perfil.usuario
        usuario.first_name, usuario.last_name = nombre.strip() or usuario.first_name, apellidos.strip() or usuario.last_name
        usuario.is_active = True
        usuario.save()
    perfil.tipo = tipo if tipo in PerfilEmpleado.Tipo.values else PerfilEmpleado.Tipo.INTERNO
    if puesto is not None:
        perfil.puesto = puesto
    perfil.empresa = empresa or perfil.empresa
    if fecha:
        perfil.fecha_incorporacion = fecha
    pin = None
    if creado or regenerar_pin or not perfil.pin:
        pin = generar_pin()
        perfil.set_pin(pin)
    perfil.save()
    return usuario, pin, creado


def importar_empleados_csv(contenido, regenerar_pin=False):
    """Devuelve (fichas, errores). Si hay errores no se guarda nada."""
    muestra = contenido[:2000]
    delimitador = ";" if muestra.count(";") >= muestra.count(",") else ","
    filas = [f for f in csv.reader(io.StringIO(contenido), delimiter=delimitador) if any(c.strip() for c in f)]
    if filas and filas[0] and filas[0][0].strip().lower() == "nombre":
        filas = filas[1:]
    datos, errores = [], []
    for n, fila in enumerate(filas, start=1):
        fila = [c.strip() for c in fila] + [""] * (len(COLUMNAS) - len(fila))
        nombre, apellidos, dni, tipo, puesto_txt, empresa, fecha_txt = fila[: len(COLUMNAS)]
        tipo = (tipo or "interno").lower()
        if not nombre or not dni:
            errores.append(f"Fila {n}: el nombre y el DNI son obligatorios.")
            continue
        if tipo not in PerfilEmpleado.Tipo.values:
            errores.append(f"Fila {n}: tipo «{tipo}» no válido (usa interno o externo).")
            continue
        puesto = buscar_puesto(puesto_txt)
        if puesto_txt and not puesto:
            errores.append(f"Fila {n}: no existe el puesto «{puesto_txt}».")
            continue
        fecha = _fecha(fecha_txt)
        if fecha_txt and not fecha:
            errores.append(f"Fila {n}: fecha «{fecha_txt}» no válida (usa dd/mm/aaaa).")
            continue
        datos.append((nombre, apellidos, dni, tipo, puesto, empresa, fecha))
    if errores:
        return [], errores
    fichas = []
    with transaction.atomic():
        for nombre, apellidos, dni, tipo, puesto, empresa, fecha in datos:
            usuario, pin, creado = dar_de_alta(nombre, apellidos, dni, tipo, puesto, empresa, fecha, regenerar_pin)
            fichas.append({"usuario": usuario, "perfil": usuario.perfil, "pin": pin, "creado": creado})
    return fichas, []
