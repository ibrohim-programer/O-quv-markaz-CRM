import django_filters

from .models import Group, Weekday


class GroupFilter(django_filters.FilterSet):
    lesson_day = django_filters.TypedChoiceFilter(
        choices=Weekday.choices, coerce=int, method="filter_lesson_day", label="Shu kuni darsi bor guruhlar"
    )

    class Meta:
        model = Group
        fields = ["status", "course", "teacher", "branch"]

    # `value: int` — Swagger parametr turini shu annotatsiyadan oladi.
    def filter_lesson_day(self, queryset, name, value: int):
        return queryset.filter(lesson_days__contains=[value])
