from rest_framework import serializers
from .models import Ingredient, Recipe, IngredientAmount, Favorite, ShoppingCart

class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор количества ингредиентов"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')

class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Минифицированный сериализатор рецептов"""
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        return obj.image.url

class RecipeSerializer(serializers.ModelSerializer):
    """Основной сериализатор рецептов"""
    author = serializers.SerializerMethodField()
    ingredients = IngredientAmountSerializer(many=True)
    image = serializers.ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'name', 'image',
            'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if ingredients_data is not None:
            instance.ingredients.clear()
            self.create_ingredients(instance, ingredients_data)
        return instance

    def create_ingredients(self, recipe, ingredients_data):
        IngredientAmount.objects.bulk_create([
            IngredientAmount(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

class RecipeCreateSerializer(RecipeSerializer):
    """Сериализатор создания рецептов"""
    image = serializers.SerializerMethodField()

    class Meta(RecipeSerializer.Meta):
        read_only_fields = ('author',)

class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного"""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        extra_kwargs = {
            'user': {'write_only': True},
            'recipe': {'write_only': True}
        }

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в избранном'
            )
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок"""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        extra_kwargs = {
            'user': {'write_only': True},
            'recipe': {'write_only': True}
        }

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в списке покупок'
            )
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(instance.recipe).data