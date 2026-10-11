from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    """
    Rolga qarab ruxsat beradi.

    View ichida qaysi amalga qaysi rollar kira olishi yoziladi:

        role_permissions = {
            "list": [Role.ADMIN, Role.MANAGER],
            "create": [Role.ADMIN],
        }

    ViewSet'da kalit — amal nomi (list, create, destroy...), oddiy APIView'da — HTTP metod
    (get, post...). Lug'atda yo'q amal hech kimga ruxsat etilmaydi (xavfsiz default).
    """

    message = "Sizning rolingiz bu amalni bajara olmaydi."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # View bu HTTP metodni umuman qo'llamasa, qarorni DRF'ga qoldiramiz: u 405 qaytaradi
        # va hech qanday kod ishlamaydi. Busiz foydalanuvchi 405 o'rniga 403 olardi.
        method = request.method.lower()
        if method not in view.http_method_names or not hasattr(view, method):
            return True

        action = getattr(view, "action", None) or method
        allowed_roles = view.role_permissions.get(action, [])
        return user.role in allowed_roles
