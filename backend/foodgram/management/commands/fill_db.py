import csv

from django.core.management.base import BaseCommand

from foodgram.models import Ingredient


class Command(BaseCommand):
    help = "Load ingredients to DB"

    def handle(self, *args, **options):
        with open('foodgram/management/commands/ingredients.csv',
                  encoding='utf-8') as fixture:
            reader = csv.reader(fixture)
            for line in reader:
                name, measurement_unit = line
                Ingredient.objects.get_or_create(
                    name=name, measurement_unit=measurement_unit
                )
