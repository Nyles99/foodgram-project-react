from django.urls import path
from django.conf.urls import include
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet

app_name = 'user'

router = DefaultRouter()
router.register(r"users", CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]
