from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
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
                          IngredientsSerializer, RecipeReadSerializer,
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
    serializer_class = IngredientsSerializer
    pagination_class = None
    filterset_class = IngredientSearchFilter
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthor, )
    filterset_class = RecipeFilter
    pagination_class = CustomPagination
    ordering_fields = ('pub_date',)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return CreateUpdateRecipeSerialiazer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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
        shopping_cart = RecipesIngredients.objects.filter(
            formula__cart_recipe__user=request.user
        ).values_list(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(
            ingredient_total=Sum('amount')
        )
        text = 'Cписок покупок: \n'
        for ingredients in shopping_cart:
            name, measurement_unit, amount = ingredients
            text += f'{name}: {amount} {measurement_unit}\n'
        response = HttpResponse(text, content_type='text/plain')
        filename = 'shop-list.pdf'
        response['Content-Disposition'] = (
            f'attachment; filename={filename}'
        )
        return response
