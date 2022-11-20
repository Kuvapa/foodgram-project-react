from drf_extra_fields.fields import Base64ImageField
from recipe.models import (Favorite, Ingredients, Recipe, RecipesIngredients,
                           ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import Follow, User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор представления пользователя."""

    is_subscribed = serializers.SerializerMethodField()

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
        extra_kwargs = {'is_subscribed': {'required': False}}

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.following.filter(author=obj).exists()


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


class RecipesIngredientsSeriliazers(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    name = serializers.ReadOnlyField()
    measurement_unit = serializers.ReadOnlyField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipesIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if int(value) < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше нуля!'
            )
        return value


class CreateUpdateRecipeSerialiazer(serializers.ModelSerializer):
    """Сериализатор рецетов."""

    tags = TagSerializer(many=True)
    ingredients = IngridientsSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'text', 'cooking_time',)

    def adding_components(self, instance, items, model):
        updated_array = []
        for item in items:
            item, _ = model.objects.get_or_create(**items)
            updated_array.append(item)
        instance.array.set(updated_array)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        image = validated_data.pop('image')
        recipe = Recipe.objects.create(image=image, **validated_data)
        self.adding_components(recipe, tags, Tag)
        self.adding_components(recipe, ingredients, Ingredients)
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
            self.adding_components(instance, ingredients, Ingredients)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            self.adding_components(instance, tags, Tag)
        instance.save()
        return instance


class RecipeReadSerializzer(serializers.ModelSerializer):
    """Сериализатор рецепта GET."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = serializers.SerializerMethodField(
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_ingredients(self, obj):
        ingredients = RecipesIngredients.objects.filter(formula=obj)
        return RecipesIngredientsSeriliazers(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.favorite_user.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.cart.filter(recipe=obj).exists()


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения сведений о рецепте
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ShortRecipeSerializer(
            instance.recipe, context=context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ShortRecipeSerializer(
            instance.recipe, context=context).data


class FollowSerializer(UserSerializer):
    """Сериализатор подписок."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + (
            'recipes', 'recipes_count', 'is_subscribed'
        )

    def get_recipes(self, author):
        queryset = self.context.get('request')
        recipes_limit = queryset.query_params.get('recipes_limit')
        if not recipes_limit:
            return ShortRecipeSerializer(
                Recipe.objects.filter(author=author),
                many=True, context={'request': queryset}
            ).data
        return ShortRecipeSerializer(
            Recipe.objects.filter(author=author)[:int(recipes_limit)],
            many=True,
            context={'request': queryset}
        ).data

    def get_recipes_count(self, author):
        return Recipe.objects.filter(author=author).count()


class FollowSubSerializer(serializers.ModelSerializer):
    """Сериализатор подписки и отписки."""

    class Meta:
        model = Follow
        fields = ('author', 'following')

        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('author', 'following')
            )
        ]

    def to_representation(self, instance):
        return FollowSerializer(
            instance.following,
            context={'request': self.context.get('request')}
        ).data
