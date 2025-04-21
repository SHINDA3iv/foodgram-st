from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyUserViewSet, IngredientViewSet, RecipeViewSet

router = DefaultRouter()
router.register(r'users', MyUserViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
