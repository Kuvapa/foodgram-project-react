from rest_framework import serializers

from recipe.models import Ingredients, Tag, Recipe, Favorite, ShoppingCart
from users.models import User, Follow
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField


class UserSerializer(UserSerializer):
    """Сериализатор представления пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.following.filter(author=obj).exists()


class IngridientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов."""

    class Meta:
        model = Ingredients
        fields = (
            'name', 'measurement_unit',
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэга."""

    class Meta:
        model = Tag
        fields = (
            'name', 'color', 'slug',
        )


class CreateUpdateRecipeSerialiazer(serializers.ModelSerializer):
    """Сериализатор рецетов."""

    tags = TagSerializer(many=True)
    ingridients = IngridientsSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'text', 'coocking_time',)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        image = validated_data.pop('image')
        recipe = Recipe.object.create(image=image, **validated_data)

        for tag in tags:
            tag_list = []
            tag, _ = Tag.objects.get_or_create(**tag)
            tag_list.append(tag)
            recipe.tags.set(tag_list)

        for ingredient in ingredients:
            imgredient_list = []
            ingredient, _ = Ingredients.objects.get_or_create(**ingredients)
            imgredient_list.append(tag)
            recipe.ingredients.set(imgredient_list)

        return recipe

    def update(self, instance, validated_data):
        self.name = validated_data.get('name', instance.name)
        self.image = validated_data.get('image', instance.image)
        self.text = validated_data.get('text', instance.text)
        self.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )

        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            ingredients_list = []
            for ingredient in ingredients:
                ingredient, _ = (
                    Ingredients.objects.get_or_create(**ingredients)
                )
                ingredients_list.append(ingredient)
            instance.ingredients.set(ingredients_list)

        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            tag_list = []
            for tag in tags:
                tag, _ = Tag.objects.get_or_create(**tags)
                tag_list.append(tag)
            instance.tags.set(tag_list)
        instance.save()
        return instance


class RecipeReadSerializzer(serializers.ModelSerializer):
    """Сериализатор рецепта GET."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngridientsSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, request, obj):
        if not request.user.is_authenticated:
            return False
        return (Favorite.objects.filter(user=self.context['request'].user,
                                        recipe=obj).exists())

    def get_is_in_shopping_cart(self, request, obj):
        if not request.user.is_authenticated:
            return False
        return (ShoppingCart.objects.filter(user=self.context['request'].user,
                                            recipe=obj).exists())


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения сведений о рецепте
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""

    is_subscribed = serializers.SerializerMethodField(
        source='get_is_subscribed'
    )
    recipes = serializers.SerializerMethodField(source='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        source='get_recipes_count'
    )

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.following.filter(author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request.user.is_anonymous:
            context = {'request': request}
            recipes_limit = request.query_params.get('recipes_limit')
        else:
            return False
        if recipes_limit is not None:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return ShortRecipeSerializer(recipes, many=True, context=context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
