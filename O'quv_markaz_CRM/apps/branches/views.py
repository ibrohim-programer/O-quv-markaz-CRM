from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.accaunts.models import User
from apps.common.mixins import BranchScopedMixin
from apps.common.permissions import RolePermission

from .models import Branch
from .serializers import BranchSerializer

Role = User.Role


@extend_schema_view(
    list=extend_schema(summary="Filiallar ro'yxati (non-admin — faqat o'z filiali)"),
    retrieve=extend_schema(summary="Bitta filial"),
    create=extend_schema(summary="Filial yaratish (Admin)"),
    update=extend_schema(summary="Filialni tahrirlash (Admin)"),
    partial_update=extend_schema(summary="Filialni qisman tahrirlash (Admin)"),
    destroy=extend_schema(summary="Filialni o'chirish (Admin; bog'liq ma'lumot bo'lsa 409)"),
)
@extend_schema(tags=["Branches"])
class BranchViewSet(BranchScopedMixin, viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": Role.values,
        "retrieve": Role.values,
        "create": [Role.ADMIN],
        "update": [Role.ADMIN],
        "partial_update": [Role.ADMIN],
        "destroy": [Role.ADMIN],
    }
    # Filialning o'zi — filtrlanadigan maydon uning id'si.
    branch_field = "id"
    filterset_fields = ["status"]
    search_fields = ["name", "address", "phone"]
    ordering_fields = ["name", "created_at"]
