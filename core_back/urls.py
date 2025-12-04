from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse  # <-- IMPORTANTE

def home(request):
    return HttpResponse("Servidor funcionando correctamente")

urlpatterns = [
    path('', home),  # <-- Ahora sí funciona
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]