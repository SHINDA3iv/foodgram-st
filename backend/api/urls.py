from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from djoser.views import TokenCreateView, TokenDestroyView

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
    
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    path('users/subscriptions/', UserViewSet.as_view({'get': 'subscriptions'}), name='subscriptions'),
    path('users/<int:id>/subscribe/', UserViewSet.as_view({
        'post': 'subscribe',
        'delete': 'subscribe'
    }), name='subscribe'),
    
    path('recipes/<int:id>/favorite/', RecipeViewSet.as_view({
        'post': 'favorite',
        'delete': 'favorite'
    }), name='favorite'),
    path('recipes/<int:id>/shopping_cart/', RecipeViewSet.as_view({
        'post': 'shopping_cart',
        'delete': 'shopping_cart'
    }), name='shopping-cart'),
    path('recipes/download_shopping_cart/', RecipeViewSet.as_view({
        'get': 'download_shopping_cart'
    }), name='download-shopping-cart'),
    
    path('', include(router.urls)),
]