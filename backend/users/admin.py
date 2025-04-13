from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subscription

@admin.register(User)
class UserAdmin(UserAdmin):
    """Админка пользователей"""
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    ordering = ('email',)
    
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка подписок"""
    list_display = ('user', 'author')
    search_fields = ('user__email', 'author__email')
    list_filter = ('user', 'author')