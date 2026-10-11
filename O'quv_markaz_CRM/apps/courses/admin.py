from django.contrib import admin

from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "duration_months", "price", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["name"]
