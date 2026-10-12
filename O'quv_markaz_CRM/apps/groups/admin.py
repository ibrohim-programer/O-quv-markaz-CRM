from django.contrib import admin

from .models import Enrollment, Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "course", "teacher", "branch", "start_date", "max_students", "status"]
    list_filter = ["status", "branch", "course"]
    list_select_related = ["course", "teacher__user", "branch"]
    search_fields = ["name"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["id", "student", "group", "contract_amount", "paid_amount", "status", "created_at"]
    list_filter = ["status"]
    list_select_related = ["student", "group"]
    search_fields = ["student__first_name", "student__last_name", "student__phone", "group__name"]
    # To'langan summa faqat to'lovlar orqali o'zgaradi; o'quvchi va guruh almashtirilmaydi.
    readonly_fields = ["student", "group", "paid_amount"]

    def has_add_permission(self, request):
        return False
