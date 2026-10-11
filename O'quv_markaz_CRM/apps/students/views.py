from django.db.models import Exists, OuterRef
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.accounts.models import User
from apps.common.mixins import BranchScopedMixin
from apps.common.permissions import RolePermission
from apps.groups.models import Enrollment

from .filters import StudentFilter
from .models import Student
from .serializers import StudentSerializer

Role = User.Role


@extend_schema_view(
    list=extend_schema(summary="O'quvchilar ro'yxati (Teacher — o'z guruhlaridagilar)"),
    retrieve=extend_schema(summary="Bitta o'quvchi"),
    create=extend_schema(summary="O'quvchi qo'shish (Admin, Manager, Operator)"),
    update=extend_schema(summary="O'quvchini tahrirlash"),
    partial_update=extend_schema(summary="O'quvchini qisman tahrirlash"),
    destroy=extend_schema(summary="O'quvchini o'chirish (Admin, Manager; tarixi bo'lsa 409)"),
)
@extend_schema(tags=["Students"])
class StudentViewSet(BranchScopedMixin, viewsets.ModelViewSet):
    queryset = Student.objects.select_related("branch")
    serializer_class = StudentSerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": Role.values,
        "retrieve": Role.values,
        "create": [Role.ADMIN, Role.MANAGER, Role.OPERATOR],
        "update": [Role.ADMIN, Role.MANAGER, Role.OPERATOR],
        "partial_update": [Role.ADMIN, Role.MANAGER, Role.OPERATOR],
        "destroy": [Role.ADMIN, Role.MANAGER],
    }
    filterset_class = StudentFilter
    search_fields = ["first_name", "last_name", "phone", "extra_phone"]
    ordering_fields = ["id", "first_name", "last_name", "created_at"]

    def filter_for_teacher(self, queryset, user):
        # Faqat o'z guruhlarida hozir o'qiyotganlar. JOIN emas, Exists: ikkita guruhida
        # o'qiyotgan o'quvchi ro'yxatda ikki marta chiqmaydi.
        in_own_group = Enrollment.objects.filter(
            student=OuterRef("pk"), group__teacher__user=user, status=Enrollment.Status.ACTIVE
        )
        return queryset.filter(Exists(in_own_group))
