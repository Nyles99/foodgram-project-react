import csv

from django.core.management.base import BaseCommand

from foodgram import models


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('foodgram/management/commands/ingredients.csv',
                  encoding='utf-8') as fixture:
            reader = csv.reader(fixture)
            for line in reader:
                name, measurement_unit = line
                models.Ingredient.objects.get_or_create(
                    name=name, measurement_unit=measurement_unit
                )
