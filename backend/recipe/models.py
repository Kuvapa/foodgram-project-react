from django.db import models
from colorfield.fields import ColorField
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredients(models.Model):
    """Модель ингридиентов."""

    name = models.CharField(
        max_length=200,
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единицы измерений',
        help_text='Указать единицы измерений: килограмм или кг'
    )


class Tag(models.Model):
    """Модель Тэга."""

    name = models.CharField(
        max_length=200,
        verbose_name='Название тэга',
        help_text='Название тэга',
        unique=True
    )
    color = ColorField(
        unique=True,
    )
    slug = models.SlugField(
        verbose_name='Уникальное название тэга',
        help_text='Уникальное название тэга',
        unique=True
    )


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Введите название рецепта, не более 200 символов',
        help_text='Введите название рецепта, не более 200 символов'
    )
    image = models.ImageField(
        upload_to='recipe/',
        verbose_name='Изображение готового блюда',
        help_text='Загрузите изображение готового блюда'
    )
    text = models.TextField(
        verbose_name='Введите описание рецепта',
        help_text='Введите описание рецепта, пошаговую инструкцию'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        related_name='recipe',
        # through='RecipesIngredients',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipe'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления блюда',
        help_text='Укажите время приготовления блюда в минутах',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время добавления рецепта'
    )

    class Meta:
        """Meta for Title."""

        ordering = ('pub_date', )

    def __str__(self):
        """__str__ for Title."""
        return self.name


class RecipesIngredients(models.Model):
    """Связующая модель."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredients = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField()


class Favorite(models.Model):
    """Модель избранного."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"],
                                    name="user_recipe")
        ]


class ShoppingCart(models.Model):
    """Модель корзины."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"],
                                    name="user_recipe")
        ]
