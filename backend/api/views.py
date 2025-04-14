from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import (
    AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import LimitOffsetPagination

from .serializers import *
from recipes.models import *
from users.models import *
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter, IngredientFilter
from .pagination import MyPagination

class MyUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = MyPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MyUserCreateSerializer
        elif self.action in ['set_avatar', 'delete_avatar']:
            return AvatarSerializer
        elif self.action in ['me', 'subscriptions', 'subscribe']:
            return UserWithRecipesSerializer
        return MyUserSerializer
    
    @action(detail=False, methods=['put', 'delete'], 
            permission_classes=[IsAuthenticated],
            url_path='me/avatar', url_name='avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            return self.set_avatar(request)
        return self.delete_avatar(request)
    
    def set_avatar(self, request):
        user = request.user
        serializer = AvatarResponseSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if 'avatar' not in serializer.validated_data:
            raise serializers.ValidationError("Поле 'avatar' обязательно.")
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], 
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user
        
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        subscription = Subscription.objects.filter(user=user, author=author)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], 
            permission_classes=[IsAuthenticated],
            pagination_class=MyPagination,
            url_path='subscriptions',
            url_name='subscriptions')
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes=(AllowAny,)
    pagination_class = None

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = MyPagination
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': request.user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'user': request.user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        cart_item = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = IngredientAmount.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))
        
        content = "Список покупок:\n\n"
        for item in ingredients:
            content += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) - "
                f"{item['total_amount']}\n"
            )
        
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response