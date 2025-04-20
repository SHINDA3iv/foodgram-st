from django.contrib import admin

from .models import Favorite, ShoppingCart

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка избранного"""
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')

@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка списка покупок"""
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')