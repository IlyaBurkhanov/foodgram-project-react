from django.contrib import admin

from .models import Favorites, IngredientCount, Ingredients, Recipes, Tags


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color',)
    search_fields = ('name', 'slug',)


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('measurement_unit',)
    search_fields = ('name',)
    filter = ('name',)


class IngredientsInLine(admin.TabularInline):
    model = IngredientCount
    extra = 1


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites',)
    filter = ('name', 'author', 'tag',)
    list_filter = ('author',)
    filter_horizontal = ('ingredient',)
    inlines = (IngredientsInLine,)

    def favorites(self, rec):
        return Favorites.objects.filter(recipe=rec.id).count()
    favorites.short_description = 'В избранном'
