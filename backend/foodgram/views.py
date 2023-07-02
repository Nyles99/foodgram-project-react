from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticatedOrReadOnly,
                                        IsAdminOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (Tag, Ingredient, Recipe,
                     ShoppingCart, Favorite, IngredientInRecipe)
from .mixins import ListRetrieveMixin
from users.pagination import CustomPaginator
from .permissions import IsAuthorOrReadOnly
from .filters import IngredientFilter, RecipeFilter
from . serializers import (CreateRecipeSerializer, ShowRecipeSerializer,
                           TagSerializer, IngredientSerializer,
                           ShoppingCartSerializer, FavoriteSerializer)


class TagViewSet(ListRetrieveMixin):
    """Теги."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(ListRetrieveMixin):
    """Ингредиенты"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly]
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        method = self.request.method
        if method == "POST" or method == "PATCH":
            return CreateRecipeSerializer
        return ShowRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class FavoriteView(APIView):
    permissions = [IsAuthenticatedOrReadOnly, ]

    @action(
        methods=[
            "post",
        ],
        detail=True,
    )
    def post(self, request, recipe_id):
        user = request.user
        data = {
            "user": user.id,
            "recipe": recipe_id,
        }
        if Favorite.objects.filter(
            user=user, recipe__id=recipe_id
        ).exists():
            return Response(
                {"Ошибка": "Уже в избранном!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = FavoriteSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=[
            "DELETE",
        ],
        detail=True,
    )
    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if not Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly, ]
    pagination_class = None

    @action(
        methods=[
            "post"
        ],
        detail=True,
    )
    def post(self, request, recipe_id):
        user = request.user
        data = {
            "user": user.id,
            "recipe": recipe_id,
        }
        if ShoppingCart.objects.filter(
                user=user, recipe__id=recipe_id
        ).exists():
            return Response(
                {"Ошибка": "Уже есть в корзине"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ShoppingCartSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        method=[
            "delete",
        ],
        detail=True,
    )
    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if not ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def download_shopping_cart(request):
    """Формирует текстовый файл ингредиентов из ShoppingCart"""

    user = request.user
    shopping_cart = user.shopping_cart.all()
    buying_list = {}
    for record in shopping_cart:
        recipe = record.recipe
        ingredients = IngredientInRecipe.objects.filter(recipe=recipe)
        for ingredient in ingredients:
            quantity = ingredient.quantity
            name = ingredient.ingredient.name
            measurement_unit = ingredient.ingredient.measurement_unit
            if name not in buying_list:
                buying_list[name] = {
                    "measurement_unit": measurement_unit,
                    "quantity": quantity,
                }
            else:
                buying_list[name]["quantity"] = (
                    buying_list[name]["quantity"] + quantity
                )
    wishlist = []
    for name, data in buying_list.items():
        wishlist.append(
            f"{name} - {data['quantity']} {data['measurement_unit']}"
        )
    response = HttpResponse(wishlist, content_type="text/plain")
    return response
