import csv

from django.core.management import BaseCommand
from recipes.models import Ingredients


class Command(BaseCommand):
    help = 'Load Ingredients from csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str)

    def handle(self, *args, **options):
        path = options['path']
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                Ingredients.objects.create(
                    name=row[0],
                    measurement_unit=row[1])
