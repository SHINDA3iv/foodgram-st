from django.contrib import admin

from .models import Ingredient

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    
    def recipes_count(self, obj):
        return obj.recipes.count()
    recipes_count.short_description = 'Используется в рецептах'