from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from users.models import Follow, User
from foodgram.models import Recipe
from foodgram.serializers import ShortRecipeSerializer


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для эндпоинтов
    me, users и users/id/
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj.id).exists()


class UserCreateSerializer(UserCreateSerializer):
    """
    Cериализатор для эндпоинта
    users/
    """

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password'
        )



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
                  'last_name', 'is_subscribed',
                  'recipes', "recipes", 'recipes_count')
