from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import CustomFilter
from recipes.models import Follow, Ingredients, Recipes, Tags
from .paginations import MyPagination
from .permissions import RecipesPermission, UserPermissions
from .serializers import (FollowSerizlizer, FavoritesCartSerializer,
                          IngredientSerializer, PasswordSerializer,
                          RecipesSerializer, ShoppingCartSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserSerializer)
from .services import get_shoping_cart

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = (UserPermissions,)
    lookup_field = 'id'
    pagination_class = MyPagination

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        user = get_object_or_404(User, username=self.request.user)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not user.check_password(serializer.data.get('current_password')):
            return Response({'current_password': 'Ошибка пароля'},
                            status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.data.get('new_password'))
        user.save()
        return Response({'status': 'success'},
                        status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        qs = Follow.objects.filter(user=request.user)
        page = self.paginate_queryset(qs)
        serializer = SubscriptionsSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, id):
        serializer = FollowSerizlizer(data={'author_id': id},
                                      context={'request': request})
        serializer.is_valid(raise_exception=True)

        if request.method.upper() == 'DELETE':
            follower = get_object_or_404(
                Follow.objects.filter(author__id=id), user=request.user)
            follower.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        new_author = Follow.objects.create(author_id=id,
                                           user=request.user)
        new_author.save()
        serializer = SubscriptionsSerializer(new_author,
                                             context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagIngredients(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    pagination_class = None
    permission_classes = (AllowAny,)


class TagViewSet(TagIngredients):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(TagIngredients):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipesViewSet(viewsets.ModelViewSet):
    serializer_class = RecipesSerializer
    permission_classes = (RecipesPermission,)
    pagination_class = MyPagination
    queryset = Recipes.objects.all()
    filterset_class = CustomFilter

    def filter_queryset(self, queryset):
        mapping_follow = {'is_favorited': 'recipe_favorite__user',
                          'is_in_shopping_cart': 'recipe_shop__user'}
        if not self.request.user.is_authenticated:
            return queryset
        filter_list = []
        for use_filter, use_attr in mapping_follow.items():
            filter_query = self.request.query_params.get(use_filter)
            if filter_query is not None and filter_query[0].isdigit():
                filter_list.append([use_attr, int(filter_query[0])])
        for filter_use in filter_list:
            queryset = getattr(
                queryset, 'filter' if filter_use[1]
                else 'exclude')(**{filter_use[0]: self.request.user})
        return DjangoFilterBackend().filter_queryset(self.request,
                                                     queryset,
                                                     view=self)

    def favorite_shopping_method(self, request, pk, use_serializer,
                                 field, error):
        if request.method.upper() == 'DELETE':
            recipe_use = getattr(self.get_object(), field).select_related(
                'user').filter(user=request.user)
            if recipe_use:
                recipe_use.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'error': error},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = use_serializer(data={'id': pk},
                                    context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.favorite_shopping_method(
            request, pk,
            use_serializer=ShoppingCartSerializer,
            field='recipe_shop',
            error='Рецепта нет в списке покупок')

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.favorite_shopping_method(
            request, pk,
            use_serializer=FavoritesCartSerializer,
            field='recipe_favorite',
            error='Рецепта нет в избранном')

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        return get_shoping_cart(user=request.user)
