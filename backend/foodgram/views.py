from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated)
# from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from rest_framework.response import Response

from .constants import DELETE_VALIDATION_ERRORS, POST_VALIDATION_ERRORS
from .models import (Tag, Ingredient, Recipe,
                     ShoppingCart, Favorite, RecipeIngredient)
from .mixins import ListRetrieveMixin
from users.pagination import CustomPaginator
from .filters import IngredientFilter, RecipeFilter
from . serializers import (GetRecipeSerializer, PostRecipeSerializer,
                           TagSerializer, IngredientSerializer,
                           ShortRecipeSerializer)


class TagViewSet(ListRetrieveMixin):
    """Теги."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(ListRetrieveMixin):
    """Ингредиенты"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты."""

    queryset = Recipe.objects.all()
    permission_classes = (AllowAny)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GetRecipeSerializer
        return PostRecipeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer. is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = GetRecipeSerializer(
            instance=serializer.instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        recipe = Recipe.objects.get(pk=kwargs.get('pk'))
        serializer = self.get_serializer(
            recipe, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = GetRecipeSerializer(
            instance=serializer.instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_200_OK, headers=headers)

    def create_or_delete_recipe(self, user, recipe_pk, request, cls):
        recipe = get_object_or_404(Recipe, pk=recipe_pk)

        if request.method == 'POST':
            if cls.objects.filter(user=user, recipe=recipe).exists():
                raise exceptions.ValidationError(
                    POST_VALIDATION_ERRORS[cls.__name__])
            cls.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(instance=recipe, context={
                'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not cls.objects.filter(user=user, recipe=recipe).exists():
                raise exceptions.ValidationError(
                    DELETE_VALIDATION_ERRORS[cls.__name__])
            cls.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST', 'DELETE'), permission_classes=[
        IsAuthenticated])
    def favorite(self, request, pk=None):
        user = self.request.user
        return self.create_or_delete_recipe(user, pk, request, Favorite)

    @action(detail=True, methods=('POST', 'DELETE'), permission_classes=[
        IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        return self.create_or_delete_recipe(user, pk, request, ShoppingCart)

    @action(detail=False, methods=['GET'], permission_classes=[
        IsAuthenticated])
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        recipes_id = [i.recipe.id for i in shopping_cart]
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes_id).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
            amount=Sum('amount'))
        final_list = 'Список покупок от Foodgram\n\n'
        for item in ingredients:
            amount = item.get('amount')
            final_list += (
                f'{item["ingredient__name"]}'
                f'({item["ingredient__measurement_unit"]}) {amount}\n'
            )

        filename = 'foodgram_shopping_list.txt'
        response = HttpResponse(final_list[:-1], content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            filename)
        return response
