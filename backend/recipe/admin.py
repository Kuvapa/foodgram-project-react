from django.contrib import admin
from django.utils.html import format_html

from .models import (ShoppingCart, Favorite, Ingredients, RecipesIngredients,
                     Recipe, Tags)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'image', 'text', 'cooking_time',)
    search_fields = ('name', 'author', 'tags',)
    list_filter = ('name', 'author', 'tags',)
    empty_value_display = '-пусто-'


class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'colored', 'slug',)
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'

    @admin.display
    def colored(self, obj):
        return format_html(
            f'<span style="background: {obj.color};'
            f'color: {obj.color}";>___________</span>'
        )
    colored.short_description = 'цвет'


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipesIngredientsAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(RecipesIngredients, RecipesIngredientsAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tags, TagsAdmin)
admin.site.register(Ingredients, IngredientsAdmin)
