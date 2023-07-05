from django.urls import path
from django.conf.urls import include
from rest_framework.routers import DefaultRouter

app_name = 'user'

router = DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]
