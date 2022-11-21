from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredients(models.Model):
    """Модель ингридиентов."""

    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единицы измерений',
        help_text='Указать единицы измерений: килограмм или кг'
    )

    def __str__(self):
        """__str__ for Title."""
        return self.name


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
        max_length=7,
        default='#FF0000',
        format='hex',
        verbose_name='HEX-код цвета',
    )
    slug = models.SlugField(
        verbose_name='Уникальное название тэга',
        help_text='Уникальное название тэга',
        unique=True
    )

    def __str__(self):
        """__str__ for Title."""
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Введите название рецепта, не более 200 символов',
        help_text='Введите название рецепта, не более 200 символов'
    )
    image = models.ImageField(
        upload_to='recipe/media/',
        verbose_name='Изображение готового блюда',
        help_text='Загрузите изображение готового блюда'
    )
    text = models.TextField(
        verbose_name='Введите описание рецепта',
        help_text='Введите описание рецепта, пошаговую инструкцию'
    )
    ingredients = models.ManyToManyField(
        'RecipesIngredients',
        symmetrical=False
    )
    tags = models.ManyToManyField(
        Tag,
        symmetrical=False
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления блюда',
        help_text='Укажите время приготовления блюда в минутах',
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления не может быть меньше 1 мин.'
            )
        ]
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

    formula = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1, message='Количество не может быть меньше 1!')
        ]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'formula'],
                name='recipe_ingredient_unique',
            ),
            models.CheckConstraint(
                check=models.Q(amount__gte=1),
                name='amount_gte_1'),
        ]


class Favorite(models.Model):
    """Модель избранного."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_user'
    )

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
        related_name='cart_recipe'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"],
                                    name="user_recipes")
        ]
