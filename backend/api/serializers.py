from rest_framework import serializers
from recipes.models import Recipe, Ingredient, IngredientAmount, Favorite, ShoppingCart
from users.models import User, Subscription
from django.core.files.base import ContentFile
import base64
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import  UserSerializer, UserCreateSerializer

class MyBase64ImageField(serializers.ImageField):
    """Кастомное поле для обработки изображений в base64"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)

class MyUserSerializer(UserSerializer):
    """Сериализатор пользователя"""
    avatar = MyBase64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 
                  'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.following.filter(user=user).exists()
        return False

class MyUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя"""    
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

class AvatarSerializer(serializers.ModelSerializer):
    avatar = MyBase64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

class AvatarResponseSerializer(serializers.ModelSerializer):
    avatar = MyBase64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url  
        return None

class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с рецептами"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = ('email', 'id', 'username', 'first_name', 
                  'last_name', 'avatar', 'is_subscribed', 
                  'recipes', 'recipes_count')

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

class SubscriptionSerializer(MyUserSerializer):
    """Сериализатор подписок"""
    class Meta:
        model = Subscription
        fields = ('user', 'author')
        extra_kwargs = {
            'user': {'write_only': True},
            'author': {'write_only': True}
        }

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return UserWithRecipesSerializer(
            instance.author, context={'request': request}
        ).data

class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор количества ингредиентов"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')

class RecipeSerializer(serializers.ModelSerializer):
    """Основной сериализатор рецептов"""
    author = MyUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(source='recipe_ingredients', many=True)
    image = MyBase64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'author', 'ingredients', 'image',
                  'text', 'cooking_time', 'is_favorited', 
                  'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated and 
                Favorite.objects.filter(user=user, recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated and 
                ShoppingCart.objects.filter(user=user, recipe=obj).exists())

class RecipeCreateUpdateSerializer(RecipeSerializer):
    """Сериализатор создания/обновления рецепта"""
    class Meta(RecipeSerializer.Meta):
        read_only_fields = ('author', )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один ингредиент')
        ingredient_id = [item['ingredient']['id'] for item in value]
        if len(ingredient_id) != len(set(ingredient_id)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться')
        return value

    def create_ingredients(self, recipe, ingredients_data):
        ingredient_amounts = []
        for ingredient in ingredients_data:
            ingredient_amounts.append(
                IngredientAmount(
                    recipe=recipe,
                    ingredient=ingredient['ingredient']['id'],
                    amount=ingredient['amount']
                )
            )
        IngredientAmount.objects.bulk_create(ingredient_amounts)
    
    def create(self, validated_data):
        ingredients = validated_data.pop("recipe_ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients)
        return recipe
    
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        
        if ingredients_data is None:
            raise serializers.ValidationError({
                'ingredients': 'Это поле обязательно для заполнения.'
            })
    
        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients_data)
        
        return super().update(instance, validated_data)

    def _check_existence(self, model, recipe):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and model.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists()
        )

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
            raise serializers.ValidationError('Этот рецепт уже есть в избранном')
        return data

    def to_representation(self, instance):
        return RecipeSerializer(instance.recipe).data

class ShoppingCartSerializer(FavoriteSerializer):
    """Сериализатор списка покупок"""
    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Этот рецепт уже есть в списке покупок')
        return data

class ShoppingCartDownloadSerializer(serializers.Serializer):
    """Сериализатор скачивания списка покупок"""
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')
    total_amount = serializers.IntegerField()

    class Meta:
        fields = ('name', 'measurement_unit', 'total_amount')