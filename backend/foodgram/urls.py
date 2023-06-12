from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    FavoriteView,
    IngredientsView,
    RecipeView,
    ShoppingCartViewSet,
    TagView,
    download_shopping_cart,
)

router = DefaultRouter()
router.register(r"tags", TagView, basename="tags")
router.register(r"ingredients", IngredientsView, basename="ingredients")
router.register(r"recipes", RecipeView, basename="recipes")

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
        ShoppingCartViewSet.as_view(),
    ),
    path("", include(router.urls)),
]