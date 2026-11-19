from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def temario(texto):
    """Convierte texto simple en HTML: párrafos, listas con «- » y títulos con «## »."""
    if not texto:
        return ""
    html = []
    for bloque in texto.replace("\r\n", "\n").split("\n\n"):
        lineas = [l for l in bloque.split("\n") if l.strip()]
        if not lineas:
            continue
        if all(l.lstrip().startswith(("- ", "* ")) for l in lineas):
            items = "".join(f"<li>{escape(l.lstrip()[2:])}</li>" for l in lineas)
            html.append(f"<ul>{items}</ul>")
        elif lineas[0].startswith("## "):
            html.append(f"<h3>{escape(lineas[0][3:])}</h3>")
            resto = lineas[1:]
            if resto:
                html.append(temario("\n".join(resto)))
        else:
            html.append("<p>" + "<br>".join(escape(l) for l in lineas) + "</p>")
    return mark_safe("".join(html))


@register.filter
def get(dic, clave):
    return dic.get(clave) if dic else None
