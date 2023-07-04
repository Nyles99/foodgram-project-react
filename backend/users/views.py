from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, exceptions
from rest_framework.permissions import (
     IsAuthenticated
)
from rest_framework.decorators import action
from rest_framework.response import Response

from users.pagination import CustomPaginator
from .serializers import (
    CustomUserSerializer,
    SubscriptionSerializer
)
from .models import Follow

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Юзеры."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPaginator

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        serializer_class=SubscriptionSerializer
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
        serializer_class=SubscriptionSerializer
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
                    'Вы не подписаны на этого пользователя.')
            Follow.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
