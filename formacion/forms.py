from django import forms

from .models import PerfilEmpleado, Puesto


class AltaEmpleadoForm(forms.Form):
    nombre = forms.CharField(max_length=150)
    apellidos = forms.CharField(max_length=150, required=False)
    dni = forms.CharField(label="DNI/NIE", max_length=20)
    tipo = forms.ChoiceField(choices=PerfilEmpleado.Tipo.choices)
    puesto = forms.ModelChoiceField(Puesto.objects.select_related("departamento"), required=False)
    empresa = forms.CharField(max_length=150, required=False, help_text="Solo personal externo.")
    fecha_incorporacion = forms.DateField(
        label="Fecha de incorporación", required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    regenerar_pin = forms.BooleanField(label="Generar PIN nuevo si ya existe", required=False)

    def clean_dni(self):
        dni = PerfilEmpleado.normalizar_dni(self.cleaned_data["dni"])
        if len(dni) < 5:
            raise forms.ValidationError("DNI/NIE no válido.")
        return dni


class AltaMasivaForm(forms.Form):
    archivo = forms.FileField(label="Archivo CSV")
    regenerar_pin = forms.BooleanField(label="Generar PIN nuevo a los que ya existen", required=False)
