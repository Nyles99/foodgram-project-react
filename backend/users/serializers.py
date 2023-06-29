import re
import statistics
from djoser.serializers import UserCreateSerializer, UserSerializer
from requests import Response
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
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
        request = self.context.get('request')
        if request.is_authenticated:
            return False
        return Follow.objects.filter(user=request.user, author=obj.id).exists()

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
                'username', "Этот логин уже зарегистрирован/"
            )
        return cleaned_name

    def validate_me(self, data):
        username = data.get('username')
        if data.get('username').lower() == 'me':
            raise serializers.ValidationError(
                f'Имя пользователя {username} недопустимо. '
                'Используйте другое имя.')
        return username


class UserCreateSerializer(UserCreateSerializer):

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


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, object):
        queryset = object.recipes.all()[:3]

        return ShortRecipeSerializer(queryset, many=True).data

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name')
