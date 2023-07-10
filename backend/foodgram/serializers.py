from drf_extra_fields.fields import Base64ImageField
from django.db.transaction import atomic
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.serializers import PrimaryKeyRelatedField

from .models import (Favorite, Ingredient, Recipe, ShoppingCart,
                     Tag, RecipeIngredient)
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class GetIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для GetRecipeSerializer."""
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', 'name', 'measurement_unit')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.ingredient.id
        return data


class GetRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор Recipe для чтения."""

    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

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

    def get_ingredients(self, obj):
        recipe = obj
        ingredients = RecipeIngredient.objects.filter(recipe=recipe)
        serializer = GetIngredientRecipeSerializer(ingredients, many=True)
        return serializer.data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe для добавления в Favorite и ShoppingCart."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShortIngredientSerializerForRecipe(serializers.ModelSerializer):
    """Сериализатор для PostRecipeSerializer."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class PostRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов: post, delete, patch"""

    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = ShortIngredientSerializerForRecipe(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate_tags(self, value):
        if not value:
            raise ValidationError('Должен быть хотя бы один тег.')
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError('Добавьте тег.')
        return value

    def validate_ingredients(self, value):
        '''Валидатор ингредиентов'''
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Добавьте хотя бы один ингредиент!'
            })
        ingredients_list = []
        for item in ingredients:
            if item['id'] in ingredients_list:
                raise ValidationError({
                    'ingredients': 'Ингредиенты не должны дублироваться!'
                })
            if int(item['amount']) <= 0:
                raise ValidationError({
                    'amount': 'Количество должно быть больше нуля!'
                })
            ingredients_list.append(item['id'])
        return value

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return GetRecipeSerializer(instance,
                                   context=context).data

    def addon_for_create_update_methods(self, ingredients, tags, recipe):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient['id'],
            amount=ingredient['amount'],
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
