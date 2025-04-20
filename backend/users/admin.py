from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subscription
from django.utils.html import format_html


@admin.register(User)
class MyUserAdmin(UserAdmin):
    """Админка пользователей"""
    list_display = ('email', 'username', 'first_name', 'last_name',
                    'is_staff', 'is_active', 'date_joined', 'avatar_preview')
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    readonly_fields = ('date_joined', 'last_login', 'avatar_preview')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def avatar_preview(self, obj):
        return format_html('<img src="{}" width="50"/>', obj.avatar.url)
    avatar_preview.short_description = 'Аватар'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка подписок"""
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__email', 'author__email',
                     'user__username', 'author__username')
    autocomplete_fields = ('user', 'author')
