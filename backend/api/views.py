from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    AllowAny,
    IsAuthenticated
)
from django_filters.rest_framework import DjangoFilterBackend


from .permissions import IsAuthor
from rest_framework.pagination import LimitOffsetPagination
from .filters import RecipeFilter, IngredientSearchFilter
from recipe.models import (
    Ingredients,
    Tag,
    Recipe,
    Favorite,
    ShoppingCart,
    RecipesIngredients
)
from .serializers import (
    CreateUpdateRecipeSerialiazer,
    RecipeReadSerializzer,
    IngridientsSerializer,
    TagSerializer,
    FavoriteSerializer,
    UserSerializer,
    ShoppingCartSerializer,
    FollowSerializer,
)


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination

    @action(
        methods=('GET'),
        detail=True,
        url_path='subscriptions',
        permission_classes=[IsAuthenticated, ]
    )
    def subscriptions(self, request):
        return User.objects.filter(following__user=self.request.user)

    @action(
        methods=('POST', 'DELETE'),
        detail=True,
        url_path='subscribe',
        permission_classes=[IsAuthenticated, ]
    )
    def subscribe(self, id, serializer, request):
        author = get_object_or_404(User, pk=id)
        if self.request.method == 'POST':
            request.user.following.add(author)
            return Response(
                data=FollowSerializer.data,
                status=status.HTTP_201_OK
            )
        request.user.following.remove(author)
        return Response(
            data=FollowSerializer.data,
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )


class IngredientsViewSet(viewsets.ModelViewSet):
    """Вьюсет ингредиентов."""

    queryset = Ingredients.objects.all()
    serializer_class = IngridientsSerializer
    permission_classes = (AllowAny, )
    filter_backends = IngredientSearchFilter
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthor)
    filterset_class = RecipeFilter
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, ]
    ordering_fields = ('pub_date',)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializzer
        return CreateUpdateRecipeSerialiazer

    def perform_create(self, serializer, request):
        serializer.save(author=request.user)

    @action(
        methods=('POST', 'DELETE'),
        url_path='favorite',
        detail=True,
        permission_classes=[IsAuthenticated, ]
    )
    def favorite(self, request, serializer, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if self.request.method == 'POST':
            Favorite.object.create(recipe=recipe, user=request.user)
            return Response(
                data=FavoriteSerializer.data,
                status=status.HTTP_201_OK
            )
        Favorite.object.delete(recipe=recipe, user=request.user)
        return Response(
            data=FavoriteSerializer.data,
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        methods=('POST', 'DELETE'),
        url_path='shopping_cart',
        detail=True,
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, serializer, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if self.request.method == 'POST':
            ShoppingCart.object.create(recipe=recipe, user=request.user)
            return Response(
                data=ShoppingCartSerializer.data,
                status=status.HTTP_201_OK
            )
        ShoppingCart.object.delete(recipe=recipe, user=request.user)
        return Response(
            data=ShoppingCartSerializer.data,
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=['GET'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        ingredients = RecipesIngredients.objects.filter(
            recipe__cart__user=request.user
        ).values_list(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            ingredients_amount=Sum('amount')
        )
        filename = f'{user.username}_shopping_list.txt'
        temp_shopping_cart = {}
        for ingredient in ingredients:
            name = ingredient[0]
            temp_shopping_cart[name] = {
                'amount': ingredient[2],
                'measurement_unit': ingredient[1]
            }
            shopping_cart = ["Список покупок\n\n"]
            for key, value in temp_shopping_cart.items():
                shopping_cart.append(f'{key} - {value["amount"]} '
                                     f'{value["measurement_unit"]}\n')
        response = HttpResponse(
            shopping_cart, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = (
            f'attachment; filename={filename}.txt'
        )
        return response
