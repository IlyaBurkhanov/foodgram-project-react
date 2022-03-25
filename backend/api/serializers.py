from django.contrib.auth import get_user_model
from drf_base64.fields import Base64ImageField
from rest_framework import serializers, status

from recipes.models import (Favorites, Follow, IngredientCount, Ingredients,
                            Recipes, ShoppingCart, Tags)

User = get_user_model()
User._meta.get_field('email')._unique = True


def is_true(self, model, **kwargs):
    client = self.context['request'].user
    return (client.is_authenticated
            and model.objects.filter(user=client,
                                     **kwargs).exists())


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField('subscribed',
                                                      read_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def subscribed(self, user):
        return is_true(self, Follow, author=user)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'password')
        extra_kwargs = {field: {'required': True}
                        for field in ['email', 'first_name', 'last_name']}
        extra_kwargs['password'] = {'write_only': True}


class PasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(source='user.password',
                                             required=True)

    class Meta:
        model = User
        fields = ('new_password', 'current_password')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = '__all__'
        read_only_fields = ('name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = '__all__'


class IngredientRecipesSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all(),
                                            source='ingredient')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.FloatField(source='count',
                                    min_value=0,
                                    required=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipes.objects.all(),
                                                write_only=True)

    class Meta:
        model = IngredientCount
        fields = ('id', 'name', 'measurement_unit', 'amount', 'recipe')


class RecipesSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(source='tag', many=True, read_only=True)
    ingredients = IngredientRecipesSerializer(many=True,
                                              source='ingredientcount_set',
                                              read_only=True)
    author = UserSerializer(default=serializers.CurrentUserDefault())
    is_favorited = serializers.SerializerMethodField('favorited',
                                                     read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(
        'in_shopping_cart', read_only=True)

    def in_shopping_cart(self, recipe):
        return is_true(self, ShoppingCart, recipe=recipe)

    def favorited(self, recipe):
        return is_true(self, Favorites, recipe=recipe)

    def check_ingredients(self, method='create'):
        """
        :param method: create or update
        :return: ingredients list
        """
        ingredients = self.initial_data.pop('ingredients', [])
        if not ingredients and method == 'create':
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле.'},
                code=status.HTTP_400_BAD_REQUEST
            )
        return ingredients

    def check_tags(self):
        """
        :param method: create or update
        :return: tags list
        """
        tags = self.initial_data.pop('tags', [])
        if tags:
            diff = (set(tags)
                    - set(Tags.objects.filter(
                        id__in=tags).values_list('id', flat=True)))
            if diff:
                raise serializers.ValidationError(
                    {'not_found_tags': sorted(list(diff))},
                    code=status.HTTP_404_NOT_FOUND
                )
        return tags

    @staticmethod
    def add_ingredients(ingredients, recipe_id):
        for ingredient in ingredients:
            ingredient.update({'recipe': recipe_id})
            ingredient_serializer = IngredientRecipesSerializer(
                data=ingredient)
            ingredient_serializer.is_valid(raise_exception=True)
            ingredient_serializer.save()

    def create(self, validated_data):
        ingredients = self.check_ingredients()
        tags = self.check_tags()
        recipe = Recipes.objects.create(**validated_data)
        recipe.tag.add(*tags)
        self.add_ingredients(ingredients, recipe.id)
        return recipe

    def update(self, instance, validated_data):
        ingredients = self.check_ingredients(method='update')
        tags = self.check_tags()

        if tags:
            instance.tag.clear()
            instance.tag.add(*tags)

        if ingredients:
            instance.ingredient.clear()
            self.add_ingredients(ingredients, instance.id)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    class Meta:
        model = Recipes
        fields = ('id', 'tags', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart')


class BestRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='recipe',
                                            queryset=Recipes.objects.all())
    name = serializers.CharField(source='recipe.name',
                                 read_only=True)
    image = serializers.ImageField(source='recipe.image',
                                   read_only=True)
    cooking_time = serializers.FloatField(
        source='recipe.cooking_time', read_only=True)
    user = UserSerializer(default=serializers.CurrentUserDefault(),
                          write_only=True)

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time', 'user')


class ShoppingCartSerializer(BestRecipeSerializer):
    class Meta(BestRecipeSerializer.Meta):
        model = ShoppingCart


class FavoritesCartSerializer(BestRecipeSerializer):
    class Meta(BestRecipeSerializer.Meta):
        model = Favorites


class RecipesSerializerBase(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(UserSerializer, serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email', read_only=True)
    id = serializers.PrimaryKeyRelatedField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(source='author.first_name',
                                       read_only=True)
    last_name = serializers.CharField(source='author.last_name',
                                      read_only=True)
    is_subscribed = serializers.ReadOnlyField(default=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return obj.author.author_recipe.count()

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit')
        recipes = obj.author.author_recipe.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return RecipesSerializerBase(recipes, many=True, read_only=True).data

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')


class FollowSerizlizer(serializers.ModelSerializer):
    author_id = serializers.PrimaryKeyRelatedField(
        source='author', write_only=True, queryset=User.objects.all())

    def validate(self, data):
        author_id = data['author'].id
        if self.context['request'].user.id == author_id:
            raise serializers.ValidationError(
                {'detail': 'Подписка на себя не осуществляется'},
                code=status.HTTP_400_BAD_REQUEST)

        if (self.context['request'].method.upper() == 'POST'
                and Follow.objects.filter(
                    author_id=author_id,
                    user=self.context['request'].user).exists()):
            raise serializers.ValidationError(
                {'detail': f'Вы уже подписаны на автора'},
                code=status.HTTP_400_BAD_REQUEST)
        return author_id

    class Meta:
        model = Follow
        fields = ('author_id',)
