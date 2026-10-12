from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.accounts.models import User
from apps.common.mixins import BranchScopedMixin
from apps.common.permissions import RolePermission

from .filters import TeacherFilter
from .models import Teacher
from .serializers import TeacherCreateSerializer, TeacherSerializer

Role = User.Role


@extend_schema_view(
    list=extend_schema(summary="O'qituvchilar ro'yxati (Manager, Operator — o'z filiali; Teacher — o'zi)"),
    retrieve=extend_schema(summary="Bitta o'qituvchi"),
    create=extend_schema(summary="O'qituvchi yaratish — login va parol bilan (Admin)"),
    partial_update=extend_schema(summary="O'qituvchini tahrirlash yoki nofaol qilish (Admin)"),
    destroy=extend_schema(summary="O'qituvchini login akkaunti bilan o'chirish (Admin; guruhi bo'lsa 409)"),
)
@extend_schema(tags=["Teachers"])
class TeacherViewSet(BranchScopedMixin, viewsets.ModelViewSet):

    queryset = Teacher.objects.select_related("user__branch")
    permission_classes = [RolePermission]
    role_permissions = {
        "list": Role.values,
        "retrieve": Role.values,
        "create": [Role.ADMIN],
        "partial_update": [Role.ADMIN],
        "destroy": [Role.ADMIN],
    }
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    branch_field = "user__branch"
    teacher_field = "user"
    filterset_class = TeacherFilter
    search_fields = ["user__first_name", "user__last_name", "user__phone", "specialization"]
    ordering_fields = ["id", "specialization", "created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return TeacherCreateSerializer
        return TeacherSerializer

    def perform_destroy(self, instance):
        instance.user.delete()
