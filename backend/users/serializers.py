from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.authtoken.models import Token

from . import models
from foodgram.models import Recipe


User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


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
        queryset=models.User.objects.all()
    )
    following = serializers.PrimaryKeyRelatedField(
        queryset=models.User.objects.all()
    )

    def validate(self, data):
        user = data.get("user")
        following = data.get("following")
        if user == following:
            raise serializers.ValidationError("На себя подписаться нельзя")
        return data

    class Meta:
        fields = ("user", "following")
        model = models.Follow
        validators = [
            UniqueTogetherValidator(
                queryset=models.Follow.objects.all(),
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
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return models.Follow.objects.filter(
            user=request.user, following=obj
        ).exists()

    def get_recipes_count(self, obj):
        count = obj.recipes.all().count()
        return count