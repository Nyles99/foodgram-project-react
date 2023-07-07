import re
import statistics
from djoser.serializers import UserCreateSerializer, UserSerializer
from requests import Response
from rest_framework import serializers
from rest_framework.validators import (UniqueTogetherValidator,
                                       UniqueValidator)
from rest_framework.authtoken.models import Token

from users.models import Follow, User
from foodgram.models import Recipe


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name",
                  "last_name", 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()


class UserCreateSerializer(UserCreateSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all(), lookup='iexact'),
        ]
    )

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')
        required_fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password')
        validators = [UniqueTogetherValidator(
            queryset=User.objects.all(),
            fields=('username', 'email')
        )]

    def validate(self, data):
        if not re.match(r'^[\w.@+-]+', str(data.get('username'))):
            raise serializers.ValidationError(
                'Неверный формат имени.'
            )
        return data

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                f'Имя пользователя me недопустимо.'
                 'Используйте другое имя.')
        return value


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = "__all__"

    def validate(self, data):
        if data['current_password'] == data['new_password']:
            raise serializers.ValidationError(
                'Пароль не изменился.'
            )
        return data


class SpecialRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class TokenSerializer(serializers.ModelSerializer):
    token = serializers.CharField(source="key")

    class Meta:
        model = Token
        fields = ("token",)


class FollowerSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    def resubscribe(self, request):
        if request.method == "GET" or request.method == "POST":
            if Follow.exists():
                return Response(
                    "Вы уже подписаны", status=statistics.HTTP_400_BAD_REQUEST
                )

    def validate(self, data):
        user = data.get("user")
        author = data.get("author")
        if user == author:
            raise serializers.ValidationError("На себя подписаться нельзя")
        return data

    class Meta:
        fields = ("user", "author")
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=["user", "author"],
            )
        ]


class ShowFollowerSerializer(serializers.ModelSerializer):
    recipes = SpecialRecipeSerializer(many=True, required=True)
    is_subscribed = serializers.SerializerMethodField("check_if_is_subscribed")
    recipes_count = serializers.SerializerMethodField("get_recipes_count")

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def check_if_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Follow.objects.filter(
            user=user, author=obj).exists()

    def get_recipes_count(self, obj):
        count = obj.recipes.all().count()
        return count


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
