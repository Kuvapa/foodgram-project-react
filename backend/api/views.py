from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipe.models import (Favorite, Ingredients, Recipe, RecipesIngredients,
                           ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Follow

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAdminOrReadOnly, IsAuthor
from .serializers import (CreateUpdateRecipeSerialiazer, FavoriteSerializer,
                          FollowSerializer, FollowSubSerializer,
                          IngridientsSerializer, RecipeReadSerializzer,
                          ShoppingCartSerializer, TagSerializer)

User = get_user_model()


class UserViewSet(viewsets.GenericViewSet):
    """Вьюсет пользователя."""

    queryset = User.objects.all()
    serializer_class = FollowSerializer
    pagination_class = CustomPagination

    @action(
        methods=('GET', ),
        detail=False,
        url_path='subscriptions',
        permission_classes=[IsAuthenticated, ]
    )
    def subscriptions(self, request):
        subscriptions_list = self.paginate_queryset(
            User.objects.filter(following__following=request.user)
        )
        serializer = FollowSerializer(
            subscriptions_list, many=True, context={
                'request': request
            }
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=('POST', 'DELETE', ),
        detail=True,
        url_path='subscribe',
        permission_classes=[IsAuthenticated, ]
    )
    def subscribe(self, request, pk):
        following = request.user
        author = get_object_or_404(User, id=pk)
        if self.request.method == 'POST':
            data = {'author': pk, 'following': following.id}
            serializer = FollowSubSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        following = get_object_or_404(
            Follow,
            author=author,
            following=following
        )
        following.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientsViewSet(viewsets.ModelViewSet):
    """Вьюсет ингредиентов."""

    queryset = Ingredients.objects.all()
    serializer_class = IngridientsSerializer
    permission_classes = (IsAdminOrReadOnly, )
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthor, )
    filterset_class = RecipeFilter
    pagination_class = CustomPagination
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
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if self.request.method == 'POST':
            data = {
                'user': user.id,
                'recipe': pk
            }
            serializer = FavoriteSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = get_object_or_404(
            Favorite,
            user=user,
            recipe=recipe
        )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('POST', 'DELETE'),
        url_path='shopping_cart',
        detail=True,
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if self.request.method == 'POST':
            data = {
                'user': user.id,
                'recipe': pk
            }
            serializer = ShoppingCartSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        cart = get_object_or_404(
            ShoppingCart,
            user=user,
            recipe=recipe
        )
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
