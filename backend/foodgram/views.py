from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets, exceptions
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        SAFE_METHODS)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .mixins import ListRetrieveMixin
from users.models import Follow, User
from users.pagination import CustomPaginator
from .permissions import IsAuthorOrReadOnly
from foodgram.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from .serializers import (RecipeGetSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeShowSerializer, TagSerializer,
                          FollowSerializer, CustomUserSerializer)
from users.pagination import CustomPaginator



SHOP_LIST = 'Список покупок:'
FILE = 'shopping_list.txt'


class CustomUserViewSet(UserViewSet):
    '''Вьюсет для пользователей и подписок'''

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPaginator

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        serializer_class=FollowSerializer
    )
    def subscriptions(self, request):
        user = request.user
        favorites = user.followers.all()
        users = User.objects.filter(id__in=[f.author.id for f in favorites])
        paginated_queryset = self.paginate_queryset(users)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        serializer_class=FollowSerializer
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            if user == author:
                raise exceptions.ValidationError(
                    'Подписываться на себя запрещено.')
            if Follow.objects.filter(user=user, author=author).exists():
                raise exceptions.ValidationError(
                    'Вы уже подписаны на этого пользователя.')
            Follow.objects.create(user=user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Follow.objects.filter(user=user, author=author).exists():
                raise exceptions.ValidationError(
                    'Вы не подписаны на этого пользователя!')
            Follow.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ListRetrieveMixin):
    """Теги."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(ListRetrieveMixin):
    """Ингредиенты."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    '''Вьюсет рецептов'''

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = [
        m for m in viewsets.ModelViewSet.http_method_names if m not in ['PUT']
    ]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.post_method(Favorite, request.user, pk)
        return self.delete_method(Favorite, request.user, pk)

    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.post_method(ShoppingCart, request.user, pk)
        return self.delete_method(ShoppingCart, request.user, pk)

    def post_method(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'errors': 'Рецепт уже в списке'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShowSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_method(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепта нет в списке'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=['GET'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .order_by('ingredient__name')
            .annotate(amount=Sum('amount'))
        )
        result = SHOP_LIST
        result += '\n'.join(
            (
                f'{ingredient["ingredient__name"]} - {ingredient["amount"]}/'
                f'{ingredient["ingredient__measurement_unit"]}'
                for ingredient in ingredients
            )
        )
        response = HttpResponse(result, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={FILE}'
        return response
