from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Portal de Formación Aldelis · Administración"
admin.site.site_title = "Formación Aldelis"
admin.site.index_title = "Gestión de cursos, exámenes y empleados"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuenta/", include("django.contrib.auth.urls")),
    path("", include("formacion.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
