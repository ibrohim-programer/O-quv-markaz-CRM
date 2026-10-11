from datetime import datetime, time, timedelta

import django_filters
from django.db.models import Exists, OuterRef
from django.utils import timezone

from apps.groups.models import Enrollment

from .models import Student


class StudentFilter(django_filters.FilterSet):
    created_from = django_filters.DateFilter(
        method="filter_created_from", label="Ro'yxatdan o'tgan sana — shu kundan"
    )
    created_to = django_filters.DateFilter(
        method="filter_created_to", label="Ro'yxatdan o'tgan sana — shu kungacha (o'zi ham)"
    )
    group = django_filters.NumberFilter(method="filter_group", label="Shu guruhda hozir o'qiyotganlar")

    class Meta:
        model = Student
        fields = ["status", "branch", "gender"]

    # created_at__date ishlatilmaydi: u har qatorni sanaga aylantiradi va created_at indeksi ishlamaydi.
    def filter_created_from(self, queryset, name, value):
        return queryset.filter(created_at__gte=_day_start(value))

    def filter_created_to(self, queryset, name, value):
        return queryset.filter(created_at__lt=_day_start(value + timedelta(days=1)))

    # `value: int` — Swagger parametr turini shu annotatsiyadan oladi.
    def filter_group(self, queryset, name, value: int):
        in_group = Enrollment.objects.filter(student=OuterRef("pk"), group=value, status=Enrollment.Status.ACTIVE)
        return queryset.filter(Exists(in_group))


def _day_start(day):
    """Kun boshi (00:00) loyiha vaqt zonasida — Asia/Tashkent."""
    return timezone.make_aware(datetime.combine(day, time.min))
