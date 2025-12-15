from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse 
from django.conf import settings
from django.conf.urls.static import static

def home(request):
    return HttpResponse("Servidor funcionando correctamente")

urlpatterns = [
    path('', home),  # <-- Ahora sí funciona
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)