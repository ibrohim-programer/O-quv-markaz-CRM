from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.accounts.models import User
from apps.common.mixins import BranchScopedMixin
from apps.common.permissions import RolePermission
from apps.students.models import Student
from apps.students.serializers import StudentShortSerializer

from .filters import GroupFilter
from .models import Enrollment, Group
from .serializers import EnrollmentSerializer, EnrollmentUpdateSerializer, GroupSerializer

Role = User.Role


@extend_schema_view(
    list=extend_schema(summary="Guruhlar ro'yxati (Teacher — faqat o'z guruhlari)"),
    retrieve=extend_schema(summary="Bitta guruh"),
    create=extend_schema(summary="Guruh ochish (Admin, Manager)"),
    update=extend_schema(summary="Guruhni tahrirlash (Admin, Manager)"),
    partial_update=extend_schema(summary="Guruhni qisman tahrirlash (Admin, Manager)"),
    destroy=extend_schema(summary="Guruhni o'chirish (Admin, Manager; o'quvchisi bo'lsa 409)"),
)
@extend_schema(tags=["Groups"])
class GroupViewSet(BranchScopedMixin, viewsets.ModelViewSet):
    # order_by() aniq yoziladi: annotate(Count) GROUP BY qiladi, bunday so'rovda Meta.ordering ishlamaydi.
    queryset = (
        Group.objects.select_related("course", "teacher__user", "branch")
        .annotate(
            active_students_count=Count("enrollments", filter=Q(enrollments__status=Enrollment.Status.ACTIVE))
        )
        .order_by("-id")
    )
    serializer_class = GroupSerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": Role.values,
        "retrieve": Role.values,
        "students": Role.values,
        "create": [Role.ADMIN, Role.MANAGER],
        "update": [Role.ADMIN, Role.MANAGER],
        "partial_update": [Role.ADMIN, Role.MANAGER],
        "destroy": [Role.ADMIN, Role.MANAGER],
    }
    teacher_field = "teacher__user"
    filterset_class = GroupFilter
    search_fields = ["name", "course__name", "teacher__user__first_name", "teacher__user__last_name"]
    ordering_fields = ["id", "name", "start_date", "created_at", "active_students_count"]

    @extend_schema(summary="Guruhdagi faol o'quvchilar", responses=StudentShortSerializer(many=True))
    @action(detail=True, filter_backends=[])
    def students(self, request, pk=None):
        group = self.get_object()
        students = Student.objects.filter(
            enrollments__group=group, enrollments__status=Enrollment.Status.ACTIVE
        ).order_by("last_name", "first_name")

        page = self.paginate_queryset(students)
        serializer = StudentShortSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="Guruhga biriktirishlar (Teacher — o'z guruhlari)"),
    retrieve=extend_schema(summary="Bitta biriktirish: kontrakt, to'langan summa va qarz"),
    create=extend_schema(summary="O'quvchini guruhga biriktirish (Admin, Manager, Operator)"),
    partial_update=extend_schema(
        summary="Guruhdan chiqarish (status=left) yoki kontraktni o'zgartirish (Admin, Manager)",
        responses=EnrollmentSerializer,
    ),
)
@extend_schema(tags=["Enrollments"])
class EnrollmentViewSet(BranchScopedMixin, viewsets.ModelViewSet):
    """O'chirish yo'q: guruhdan chiqqan o'quvchi status=left bo'ladi, kontrakt va to'lovlar tarixda qoladi."""

    queryset = Enrollment.objects.select_related("student", "group__course")
    permission_classes = [RolePermission]
    role_permissions = {
        "list": Role.values,
        "retrieve": Role.values,
        "create": [Role.ADMIN, Role.MANAGER, Role.OPERATOR],
        "partial_update": [Role.ADMIN, Role.MANAGER],
    }
    http_method_names = ["get", "post", "patch", "head", "options"]
    branch_field = "group__branch"
    teacher_field = "group__teacher__user"
    filterset_fields = ["student", "group", "status"]
    search_fields = ["student__first_name", "student__last_name", "student__phone", "group__name"]
    ordering_fields = ["id", "created_at", "contract_amount", "paid_amount"]

    def get_serializer_class(self):
        if self.action == "partial_update":
            return EnrollmentUpdateSerializer
        return EnrollmentSerializer
