from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class User(AbstractUser):
    """Кастомная модель пользователя"""
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True
    )
    username_validator = RegexValidator(
        regex=r'^[\w.@+-]+$',
        message='Введите корректное имя пользователя. Может содержать только буквы, цифры и символы @/./+/-/_'
    )
    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        max_length=150,
        unique=True,
        validators=[username_validator]
    )
    first_name = models.CharField(verbose_name='Имя', max_length=150)
    last_name = models.CharField(verbose_name='Фамилия', max_length=150)
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/avatars/',
        blank=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
    
    def __str__(self):
        return self.email


class Subscription(models.Model):
    """Модель подписки на авторов"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    
    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]
    
    def __str__(self):
        return f'{self.user} подписан на {self.author}'
        
    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')