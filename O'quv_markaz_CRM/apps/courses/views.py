from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.accounts.models import User
from apps.common.permissions import RolePermission

from .models import Course
from .serializers import CourseSerializer

Role = User.Role


@extend_schema_view(
    list=extend_schema(summary="Kurslar ro'yxati"),
    retrieve=extend_schema(summary="Bitta kurs"),
    create=extend_schema(summary="Kurs yaratish (Admin)"),
    update=extend_schema(summary="Kursni tahrirlash (Admin)"),
    partial_update=extend_schema(summary="Kursni qisman tahrirlash (Admin)"),
    destroy=extend_schema(summary="Kursni o'chirish (Admin; guruhi bo'lsa 409)"),
)
@extend_schema(tags=["Courses"])
class CourseViewSet(viewsets.ModelViewSet):
    """Kurslar barcha filiallar uchun umumiy. Ko'rish — hamma, boshqarish — faqat Admin."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": Role.values,
        "retrieve": Role.values,
        "create": [Role.ADMIN],
        "update": [Role.ADMIN],
        "partial_update": [Role.ADMIN],
        "destroy": [Role.ADMIN],
    }
    filterset_fields = ["status"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "duration_months", "created_at"]
