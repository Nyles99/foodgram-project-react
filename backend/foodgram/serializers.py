from django.db.transaction import atomic
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
from rest_framework import serializers

from users.models import Follow, User
from foodgram.models import (Ingredient, Recipe, RecipeIngredient, Favorite,
                            ShoppingCart, Tag)


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


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeShowSerializer(ModelSerializer):
    '''
    Дополнительный сериализатор для отображения рецептов
    в подписках, избранном и покупках
    '''

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientRecipeCreationSerializer(ModelSerializer):
    '''Сериализатор для вывода ингредиента при создании рецепта'''

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'quantity', 'name', 'measurement_unit')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.ingredient.id
        return data


class RecipeGetSerializer(ModelSerializer):
    '''Сериализатор получения рецепта'''

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeCreationSerializer(
        source='recipeingredient', many=True)
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeCreateSerializer(ModelSerializer):
    '''Сериализатор создания рецепта'''

    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeCreationSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate_tags(self, value):
        if not value:
            raise ValidationError('Добавьте тег.')
        return value

    def validate_ingredients(self, value):
        '''Валидатор ингредиентов'''
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Добавьте хотя бы один ингредиент!!'
            })
        ingredients_list = []
        for item in ingredients:
            if item['id'] in ingredients_list:
                raise ValidationError({
                    'ingredients': 'Ингредиенты не должны дублироваться!!'
                })
            if int(item['quantity']) <= 0:
                raise ValidationError({
                    'quantity': 'Количество должно быть больше нуля!'
                })
            ingredients_list.append(item['id'])
        return value

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGetSerializer(instance,
                                   context=context).data

    def addon_for_create_update_methods(self, ingredients, tags, recipe):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient['id'],
            quantity=ingredient['quantity'],
        ) for ingredient in ingredients])
        return recipe

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.addon_for_create_update_methods(ingredients, tags, recipe)
        return recipe

    @atomic
    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe.tags.clear()
        recipe.ingredients.clear()
        self.addon_for_create_update_methods(ingredients, tags, recipe)
        return super().update(recipe, validated_data)
