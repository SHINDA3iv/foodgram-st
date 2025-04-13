from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Subscription

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Subscription.objects.filter(
                user=user, author=obj
            ).exists()
        return False

class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя"""
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def validate_password(self, value):
        validate_password(value)
        return value

class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок"""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_is_subscribed(self, obj):
        return True
    
class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/удаления подписок"""
    
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
        if Subscription.objects.filter(
            user=user, author=author
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionSerializer(instance, context={'request': request}).data