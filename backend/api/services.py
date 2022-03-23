import csv

from django.db.models import Sum
from django.http import HttpResponse

from recipes.models import ShoppingCart


def get_shoping_cart(user):
    """only for python >= 3.7!!!!"""
    response = HttpResponse(content_type='text/csv; charset=windows-1251')
    response['Content-Disposition'] = 'attachment; filename="buy.csv"'

    writer = csv.writer(response, delimiter=';')

    cols = {
        'name': 'recipe__ingredientcount__ingredient__name',
        'unit': 'recipe__ingredientcount__ingredient__measurement_unit',
        'total': 'total'
    }
    writer.writerow([col for col in cols.keys()])

    qs = ShoppingCart.objects.filter(user=user,
                                     recipe__ingredient__isnull=False).values(
        cols['name'], cols['unit']).annotate(
        total=Sum('recipe__ingredientcount__count'))
    writer.writerows([[rec[cols[col]] for col in cols.keys()] for rec in qs])
    return response
