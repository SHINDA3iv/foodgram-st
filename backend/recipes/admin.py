from django.contrib import admin
from django.utils.html import format_html
from .models import Recipe, RecipeIngredients

class RecipeIngredientsInline(admin.TabularInline):
    """Inline для ингредиентов внутри рецепта"""
    model = RecipeIngredients
    extra = 1
    min_num = 1
    verbose_name = ('Ингредиент')
    verbose_name_plural = ('Ингредиенты')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов"""
    list_display = ('name', 'author', 'get_image', 'favorites_count', 
                    'in_shopping_carts_count', 'pub_date')
    list_filter = ('author', 'name')
    search_fields = ('name', 'author__email')
    readonly_fields = ('favorites_count', 'in_shopping_carts_count', 'get_image')
    filter_horizontal = ('ingredients',)
    inlines = (RecipeIngredientsInline,)
    
    def get_image(self, obj):
        return format_html('<img src="{}" width="50"/>', obj.image.url)
    get_image.short_description = 'Миниатюра'
    
    def favorites_count(self, obj):
        return obj.favorites_count()
    favorites_count.short_description = 'В избранном'
    
    def in_shopping_carts_count(self, obj):
        return obj.in_shopping_carts_count()
    in_shopping_carts_count.short_description = 'В списках покупок'


@admin.register(RecipeIngredients)
class RecipeIngredientsAdmin(admin.ModelAdmin):
    """Класс админки для модели RecipeIngredients"""
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')