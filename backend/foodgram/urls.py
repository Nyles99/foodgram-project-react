from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    FavoriteView,
    IngredientsViewSet,
    RecipeViewSet,
    ShoppingCartView,
    TagViewSet,
    download_shopping_cart,
)

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tags")
router.register(r"ingredients", IngredientsViewSet, basename="ingredients")
router.register(r"recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path(
        "recipes/download_shopping_cart/",
        download_shopping_cart,
        name="download",
    ),
    path(
        "recipes/<int:recipe_id>/favorite/",
        FavoriteView.as_view(),
    ),
    path(
        "recipes/<int:recipe_id>/shopping_cart/",
        ShoppingCartView.as_view(),
    ),
    path("", include(router.urls)),
]
