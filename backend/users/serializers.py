import re
import statistics
from django.contrib.auth import get_user_model
from requests import Response
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.authtoken.models import Token

from .models import Follow
from foodgram.models import Recipe


User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]

    def validate_email(email):
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        return re.match(email_regex, email)

    def clean_email(self):
        cleaned_email = super().clean_email(self)
        if User.objects.filter(email__iexact=cleaned_email.get('email')).exists():
            self.fields.add_error('email', "Эта почта уже зарегистрированна")
        return cleaned_email

    def clean_username(self):
        cleaned_name = super().clean_email(self)
        if User.objects.filter(username__iexact=cleaned_name.get('username')).exists():
            self.fields.add_error('username', "Этот логин уже зарегистрирован")
        return cleaned_name

    def validate_me(self, data):
        username = data.get('username')
        if data.get('username').lower() == 'me':
            raise serializers.ValidationError(
                f'Имя пользователя {username} недопустимо. '
                'Используйте другое имя.')
        return username


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = "__all__"


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
    following = serializers.PrimaryKeyRelatedField(
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
        following = data.get("following")
        if user == following:
            raise serializers.ValidationError("На себя подписаться нельзя")
        return data

    class Meta:
        fields = ("user", "following")
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=["user", "following"],
            )
        ]


class ShowFollowerSerializer(serializers.ModelSerializer):
    recipes = SpecialRecipeSerializer(many=True, required=True)
    is_subscribed = serializers.SerializerMethodField("check_if_is_subscribed")
    recipes_count = serializers.SerializerMethodField("get_recipes_count")

    class Meta:
        model = User
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        ]

    def check_if_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Follow.objects.filter(
            user=user, following=obj).exists()

    def get_recipes_count(self, obj):
        count = obj.recipes.all().count()
        return count
