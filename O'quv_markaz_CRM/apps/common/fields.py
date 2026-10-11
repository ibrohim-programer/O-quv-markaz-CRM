from rest_framework import serializers


class BranchScopedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Id bo'yicha tanlanadigan bog'langan obyekt — faqat xodimning o'z filialidan (Admin — hammasi).

    Boshqa filial obyekti "mavjud emas" deb ko'rinadi: 403 yoki "boshqa filialniki" degan
    xabar uning borligini oshkor qilgan bo'lardi. `branch_field` — obyektdan filialgacha yo'l.
    `teacher_field` berilsa, o'qituvchi faqat o'ziga tegishli obyektlarni tanlay oladi
    (BranchScopedMixin'dagi kabi: obyektdan o'qituvchining User'igacha yo'l).
    """

    def __init__(self, branch_field="branch", teacher_field=None, **kwargs):
        self.branch_field = branch_field
        self.teacher_field = teacher_field
        super().__init__(**kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = getattr(self.context.get("request"), "user", None)
        if user is None or not user.is_authenticated:
            return queryset.none()
        if user.is_admin:
            return queryset
        queryset = queryset.filter(**{self.branch_field: user.branch_id})
        if user.is_teacher and self.teacher_field:
            queryset = queryset.filter(**{self.teacher_field: user})
        return queryset
