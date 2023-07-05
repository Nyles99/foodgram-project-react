from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    CustomUserViewSet
)

router = DefaultRouter()
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("users", CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]
