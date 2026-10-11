from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["id", "first_name", "last_name", "phone", "branch", "status", "created_at"]
    list_filter = ["status", "gender", "branch"]
    list_select_related = ["branch"]
    search_fields = ["first_name", "last_name", "phone", "extra_phone"]
