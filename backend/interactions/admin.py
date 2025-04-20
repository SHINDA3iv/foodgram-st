from django.contrib import admin

from .models import Favorite, ShoppingCart

class BaseInteractionAdmin(admin.ModelAdmin):
    """Базовый класс для админ-панели взаимодействий."""
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')

@admin.register(Favorite)
class FavoriteAdmin(BaseInteractionAdmin):
    """Админка избранного."""
    pass

@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseInteractionAdmin):
    """Админка списка покупок."""
    pass