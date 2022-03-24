from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q

User = get_user_model()


class Tags(models.Model):
    name = models.CharField(max_length=200, verbose_name='Тег')
    color = models.CharField(max_length=10, verbose_name='Hex color',
                             blank=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredients(models.Model):
    name = models.CharField(max_length=200, verbose_name='Ингредиент')
    measurement_unit = models.CharField(max_length=200,
                                        verbose_name='Мера измерения')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class IngredientCount(models.Model):
    ingredient = models.ForeignKey(Ingredients,
                                   on_delete=models.PROTECT)
    recipe = models.ForeignKey('Recipes',
                               on_delete=models.CASCADE)
    count = models.FloatField(validators=[MinValueValidator(0.1)])

    class Meta:
        constraints = [CheckConstraint(check=Q(count__gte=0.1),
                                       name='count_min')]


class Recipes(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL,
                               related_name='author_recipe',
                               verbose_name='автор',
                               null=True)
    name = models.CharField(max_length=200, verbose_name='Рецепт')
    text = models.TextField(verbose_name='Описание')
    image = models.ImageField(verbose_name='Картинка', blank=False,
                              upload_to='recipe/')
    ingredient = models.ManyToManyField(
        Ingredients,
        related_name='use_ingredient',
        verbose_name='Ингредиент',
        through=IngredientCount,
        through_fields=('recipe', 'ingredient')
        )
    tag = models.ManyToManyField(Tags, related_name='tag',
                                 verbose_name='Тэг', blank=True)
    cooking_time = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления')
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following')

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'],
            name='uniq_follow')]


class Favorites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_favorite')
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='recipe_favorite')

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='uniq_favorites')]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_shop'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='recipe_shop'
    )

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='uniq_shopping')]
