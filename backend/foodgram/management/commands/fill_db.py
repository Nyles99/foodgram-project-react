import csv

from django.core.management.base import BaseCommand

from foodgram import models


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('foodgram/management/commands/ingredients.csv',
            encoding='utf-8') as fixture:
            for line in fixture:
                ing = line.split(',')
                models.Ingredient.objects.get_or_create(
                    name=ing[0], measurement_unit=ing[1]
                )