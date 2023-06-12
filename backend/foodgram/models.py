from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название тега",
    )

    slug = models.SlugField(max_length=200, unique=True, verbose_name="Слаг")


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name="Название ингредиента", max_length=200
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения", max_length=200
    )

    class Meta:
        verbose_name = "Ингредиенты"

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    tags = models.ManyToManyField(
        Tag, through="TagsInRecipe", related_name="recipes"
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    text = models.TextField(verbose_name="Описание")
    cooking_time = models.PositiveSmallIntegerField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientInRecipe",
        related_name="recipes",
        blank=True,
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Время публикации"
    )
    image = models.ImageField()

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class TagsInRecipe(models.Model):

    tag = models.ForeignKey(
        Tag, verbose_name="Тег в рецепте", on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Теги в рецепте"
        verbose_name_plural = verbose_name


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент в рецепте",
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name="Рецепт"
    )
    quantity = models.PositiveIntegerField(
        null=True, verbose_name="Количество ингредиента"
    )

    class Meta:
        verbose_name = "Количество ингредиента в рецепте"
        verbose_name_plural = verbose_name


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name="favorite",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="favorite",
    )
    time_oclock = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-time_oclock"]
        verbose_name = "Список покупок"
        verbose_name_plural = verbose_name
        unique_together = ("user", "recipe")

    def __str__(self):
        return f"{self.user} added {self.recipe}"


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name="shopping_cart",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="shopping_cart",
    )
    time_oclock = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-time_oclock"]
        verbose_name = "Список покупок"
        verbose_name_plural = verbose_name
        unique_together = ("user", "recipe")

    def __str__(self):
        return f"{self.user} added {self.recipe}"
