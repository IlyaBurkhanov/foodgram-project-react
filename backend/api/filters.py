from django_filters import rest_framework as filters

from .models import Recipes


class CustomFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.CharFilter(method='filter_tags')

    def filter_tags(self, qs, name, value):
        return qs.filter(tag__slug__in=self.request.GET.getlist('tags'))

    class Meta:
        model = Recipes
        fields = ['author', 'tags']
