from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientsViewSet,
    RecipeViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tags")
router.register(r"ingredients", IngredientsViewSet, basename="ingredients")
router.register(r"recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]
