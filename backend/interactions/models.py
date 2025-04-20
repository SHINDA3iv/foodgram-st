from django.db import models

from users.models import User
from recipes.models import Recipe


class BaseInteractionModel(models.Model):
    """Абстрактная модель для взаимодействий пользователя с рецептом."""
    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(app_label)s_%(class)s_unique_user_recipe'
            )
        ]

    @classmethod
    def is_exists(cls, user, recipe):
        """Проверяет существование взаимодействия."""
        return cls.objects.filter(user=user, recipe=recipe).exists()


class Favorite(BaseInteractionModel):
    """Модель избранного"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta(BaseInteractionModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(BaseInteractionModel):
    """Модель списка покупок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta(BaseInteractionModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
