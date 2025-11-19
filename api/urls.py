from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('companies/', include('companies.urls')),
    path('addresses/', include('addresses.urls')),
    path('candidates/', include('candidates.urls')), 
    #path('messages_app/', include('messages_app.urls')),
]