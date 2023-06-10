from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientsView,
    RecipeView,
    TagView,
)

router = DefaultRouter()
router.register(r"tags", TagView, basename="tags")
router.register(r"ingredients", IngredientsView, basename="ingredients")
router.register(r"recipes", RecipeView, basename="recipes")

urlpatterns = [
    path("", include(router.urls)),
]