from django.contrib import admin
from . import models

admin.site.register(models.Tag)
admin.site.register(models.Ingredient)


class IngredientsInLine(admin.TabularInline):
    model = models.Recipe.ingredients.through


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        IngredientsInLine,
    ]
