from drf_extra_fields.fields import Base64ImageField
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, exceptions

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
    id = serializers.CharField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def get_amount(self, obj):
        return obj.amount


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
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj.id).exists()

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

    def validate_tags(self, tags):
        if not tags:
            raise exceptions.ValidationError('Должен быть хотя бы один тег.')
        return tags

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise exceptions.ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент!'
            })
        ingredients_list = []
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredients_list:
                raise exceptions.ValidationError({
                    'ingredients': 'Ингридиенты не могут повторяться!'
                })
            if int(item['amount']) <= 0:
                raise exceptions.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0!'
                })
            ingredients_list.append(ingredient)
        return value

    def validate_cooking_time(self, cooking_time):
        if cooking_time <= 0:
            raise exceptions.ValidationError(
                'Минимальное время приготовления 1 минута.')
        return cooking_time

    def get_ingredients(self, ingredients):
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient_instance = ingredient['id']

            yield amount, get_object_or_404(Ingredient, pk=ingredient_instance)

    @transaction.atomic
    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        recipe_ingredients = []
        for amount, ingredient in self.get_ingredients(ingredients):
            recipe_ingredients.append(RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            ))
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()

        for amount, ingredient in self.get_ingredients(validated_data.
                                                       pop('ingredients')):
            RecipeIngredient.objects.update_or_create(
                recipe=instance,
                ingredient=ingredient,
                amount=amount
            )
        return super().update(instance, validated_data)

    class Meta:
        model = Recipe
        fields = '__all__'
