from rest_framework.routers import DefaultRouter

from django.urls import include, path
from .views import RecipeViewSet, UserViewSet, TagViewSet, IngredientsViewSet

app_name = 'api'

router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tag')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('ingredients', IngredientsViewSet, basename='ingridients')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
    path('', include(router.urls)),
]
