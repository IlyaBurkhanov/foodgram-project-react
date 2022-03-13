from django.urls import include, path, re_path
from rest_framework import routers

from .views import UserViewSet, TagViewSet, IngredientViewSet, RecipesViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
