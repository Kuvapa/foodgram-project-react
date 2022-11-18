from django_filters import rest_framework as filters

from recipe.models import Ingredients, Recipe


class RecipeFilter(filters .FilterSet):
    """Фильтр рецептов."""

    author = filters.CharFilter(
        field_name='author', lookup_expr='exact'
    )
    tags = filters.CharFilter(
        field_name='tags__slug', lookup_expr='exact'
    )
    is_favorited = filters.CharFilter(lookup_expr='exact')
    is_in_shopping_cart = filters.CharFilter(lookup_expr='exact')

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart'
        )


class IngredientSearchFilter(filters.FilterSet):
    """Фильтр поиска по названию ингредиента."""
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredients
        fields = ('name', )
