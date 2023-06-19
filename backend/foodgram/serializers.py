from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import (Favorite, Ingredient, Recipe, ShoppingCart, 
                     Tag, IngredientInRecipe, TagsInRecipe, User)
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientInRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "quantity")


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class ShowRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField("get_ingredients")
    is_favorited = serializers.SerializerMethodField("get_is_favorited")
    is_in_shopping_cart = serializers.SerializerMethodField(
        "get_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        ]

    def get_ingredients(self, obj):
        ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and ShoppingCart.objects.filter(
            user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and ShoppingCart.objects.filter(
            user=user, recipe=obj).exists()


class AddIngredientToRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "quantity")


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientToRecipeSerializer(many=True)
    cooking_time = serializers.IntegerField()
    tags = serializers.SlugRelatedField(
        many=True, queryset=Tag.objects.all(), slug_field="id"
    )

    class Meta:
        model = Recipe
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        ]

    def validate_cooking_time(self, data):
        if data <= 0:
            raise serializers.ValidationError("Введите число больше 0")
        return data

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
            if int(item['quantity']) <= 0:
                raise ValidationError({
                    'quantity': 'Количество должно быть больше нуля!'
                })
            ingredients_list.append(item['id'])
        return value

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        recipe_ingredients = []
        for quantity, ingredient in self.get_ingredients(ingredients):
            recipe_ingredients.append(IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient,
                quantity=quantity
            ))
        IngredientInRecipe.objects.bulk_create(recipe_ingredients)
        return recipe
        

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        TagsInRecipe.objects.filter(recipe=instance).delete()
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        for ingredient in ingredients:
            ingredient_model = ingredient["id"]
            quantity = ingredient["quantity"]
            IngredientInRecipe.objects.bulk_create(
                ingredient=ingredient_model, recipe=instance, quantity=quantity
            )
        instance.name = validated_data.pop("name")
        instance.text = validated_data.pop("text")
        if validated_data.get("image") is not None:
            instance.image = validated_data.pop("image")
        instance.cooking_time = validated_data.pop("cooking_time")
        instance.tags.set(tags)
        instance.save()
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ["recipe", "user"]
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['recipe', 'user']
            )
        ]


class ShoppingCartSerializer(FavoriteSerializer):
    class Meta:
        model = ShoppingCart
        fields = ["recipe", "user"]
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['recipe', 'user']
            )
        ]
