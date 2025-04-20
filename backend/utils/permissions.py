from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS
    
class IsUserOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение на уровне запроса и объекта для проверки авторизации, авторства или read-only методов.
    """
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user
    