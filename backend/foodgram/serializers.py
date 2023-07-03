from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.serializers import CustomUserSerializer
from rest_framework import exceptions, serializers

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class GetIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для GetRecipeSerializer."""
    id = serializers.CharField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'quantity')

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def get_quantity(self, obj):
        return obj.quantity


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
        user = self.context.get('request').user
        return user.is_authenticated and Favorite.objects.filter(
            user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and ShoppingCart.objects.filter(
            user=user, recipe=obj).exists()

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
    quantity = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'quantity')


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

    def validate_tags(self, value):
        tags = value
        if not value:
            raise exceptions.ValidationError('Добавьте тег.')
        if tags != set(tags):
            raise serializers.ValidationError(
                'Теги не должны дублироваться!'
            )
        return tags

    def validate_ingredients(self, value):
        '''Валидатор ингредиентов'''
        ingredients = value
        if not ingredients:
            raise exceptions.ValidationError({
                'ingredients': 'Добавьте хотя бы один ингредиент!'
            })
        if ingredients != set(ingredients):
            raise serializers.ValidationError(
                'Ингредиенты не должны дублироваться!'
            )
        for item in ingredients:
            if int(item['quantity']) <= 0:
                raise exceptions.ValidationError(
                    {'quantity': 'Ингредиенты должно быть больше 0!'}
                )
        return value

    def validate_cooking_time(self, data):
        if data <= 0:
            raise serializers.ValidationError(
                "Время пригтовления должно быть больше нуля"
            )
        return data

    def get_ingredients(self, ingredients):
        for ingredient in ingredients:
            quantity = ingredient['quantity']
            ingredient_instance = ingredient['id']

            yield quantity, get_object_or_404(Ingredient, pk=ingredient_instance)

    @transaction.atomic
    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        recipe_ingredients = []
        for quantity, ingredient in self.get_ingredients(ingredients):
            recipe_ingredients.append(RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                quantity=quantity
            ))
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()

        for quantity, ingredient in self.get_ingredients(validated_data.
                                                       pop('ingredients')):
            RecipeIngredient.objects.update_or_create(
                recipe=instance,
                ingredient=ingredient,
                quantity=quantity
            )
        return super().update(instance, validated_data)

    class Meta:
        model = Recipe
        fields = '__all__'


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
