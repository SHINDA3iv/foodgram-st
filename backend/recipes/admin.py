from django.contrib import admin
from django.utils.html import format_html
from .models import Ingredient, Recipe, IngredientAmount, Favorite, ShoppingCart

class IngredientAmountInline(admin.TabularInline):
    """Инлайн для количества ингредиентов"""
    model = IngredientAmount
    extra = 1

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка ингредиентов"""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов"""
    list_display = ('name', 'author', 'get_image', 'favorites_count')
    list_filter = ('author', 'name')
    search_fields = ('name', 'author__email')
    readonly_fields = ('favorites_count',)
    inlines = (IngredientAmountInline,)
    
    def get_image(self, obj):
        return format_html('<img src="{}" width="50"/>', obj.image.url)
    get_image.short_description = 'Миниатюра'
    
    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = 'В избранном'

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