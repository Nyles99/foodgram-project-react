import re
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, exceptions, serializers
from rest_framework.permissions import (
    AllowAny,
)
from rest_framework.decorators import action
from rest_framework.response import Response

from users.pagination import CustomPaginator
from .serializers import (
    CustomUserSerializer,
    FollowerSerializer
)
from .models import Follow


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPaginator

    @action( 
        detail=False,
        methods=['GET'],
        permission_classes=[AllowAny],
        serializer_class=FollowerSerializer
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
        serializer_class=FollowerSerializer
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

    def validate_email(email):
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        return re.match(email_regex, email)

    def clean_email(self):
        cleaned_email = super().clean_email(self)
        if User.objects.filter(
            email__iexact=cleaned_email.get('email')
        ).exists():
            self.fields.add_error(
                'email', "Эта почта уже зарегистрированна"
            )
        return cleaned_email

    def clean_username(self):
        cleaned_name = super().clean_email(self)
        if User.objects.filter(
            username__iexact=cleaned_name.get('username')
        ).exists():
            self.fields.add_error(
                'username', "Этот логин уже зарегистрирован!"
            )
        return cleaned_name

    def validate_me(self, data):
        username = data.get('username')
        if data.get('username').lower() == 'me':
            raise serializers.ValidationError(
                f'Имя пользователя {username} недопустимо. '
                'Используйте другое имя.')
        return username
