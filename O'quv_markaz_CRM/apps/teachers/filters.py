import django_filters
from .models import Teacher

class TeacherFilter(django_filters.FilterSet):
    branch = django_filters.NumberFilter(field_name="user__branch", label="Filial")

    class Meta:
        model = Teacher
        fields = ["status", "branch"]
