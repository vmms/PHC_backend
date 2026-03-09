from django.db import connection
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from django.conf import settings
#from django.conf.urls.static import static

def home(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        html = f"""
        <html>
            <head>
                <title>Health Check</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: #f5f5f5;
                        padding: 40px;
                    }}
                    .card {{
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        width: 400px;
                        box-shadow: 0 2px 10px rgba(0,0,0,.1);
                    }}
                    .ok {{ color: green; }}
                    .error {{ color: red; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>Backend status</h2>
                    <p><strong>Database:</strong> <span class="ok">Connected</span></p>
                    <p><strong>Engine:</strong> {settings.DATABASES["default"]["ENGINE"]}</p>
                    <p><strong>Test query result:</strong> {result}</p>
                </div>
            </body>
        </html>
        """
        return HttpResponse(html)

    except Exception as e:
        return HttpResponse(f"""
        <html>
            <body style="font-family: Arial; padding: 40px;">
                <h2 style="color:red;">Backend status</h2>
                <p><strong>Database:</strong> ERROR</p>
                <pre>{str(e)}</pre>
            </body>
        </html>
        """, status=500)

    

urlpatterns = [
    path('', home),  
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
] #+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)