from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from djoser.serializers import SetPasswordSerializer

from .serializers import *
from utils.filters import RecipeFilter
from utils.permissions import IsUserOrReadOnly

class MyUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = [IsUserOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return MyUserCreateSerializer
        elif self.action in ['set_avatar', 'delete_avatar']:
            return AvatarSerializer
        elif self.action in ['subscriptions', 'subscribe']:
            return UserWithRecipesSerializer
        if self.action in ['set_password']:
            return SetPasswordSerializer
        return MyUserSerializer
    
    @action(detail=False, methods=['get'], 
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
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
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
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
        if not subscription.exists():
            raise serializers.ValidationError("Вы не подписаны на этого пользователя.")
    
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], 
            permission_classes=[IsAuthenticated],
            url_path='subscriptions',
            url_name='subscriptions')
    def subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,filters.SearchFilter,)
    filterset_fields = ('name',)
    search_fields = ('^name',)
    permission_classes=[AllowAny]
    pagination_class = None

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsUserOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer
    
    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication credentials were not provided.")
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=("get",),
        url_path="get-link",
        url_name="get-link",
    )
    def get_short_link(self, request, pk):
        url = f"{request.get_host()}/s/{pk}"
        return Response(
            data={
                "short-link": url
            }
        )
    
    @action(detail=True, methods=('post', 'delete',),
        permission_classes=[IsAuthenticated],
        url_path="favorite",
        url_name="favorite",)
    def favorite(self, request, pk):            
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
        if not favorite.exists():
            raise serializers.ValidationError("Этот рецепт не находится в вашем избранном.")
        
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=('post', 'delete',),
            permission_classes=[IsAuthenticated],
            url_path="shopping_cart",
            url_name="shopping_cart",)
    def shopping_cart(self, request, pk):
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
        if not cart_item.exists():
            raise serializers.ValidationError("Этот рецепт не находится в вашей корзине.")

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart',
            url_name='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredients.objects.filter(
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