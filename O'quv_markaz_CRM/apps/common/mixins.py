class BranchScopedMixin:
    """
    Admin bo'lmagan xodimga faqat o'z filialidagi yozuvlarni ko'rsatadi.

    `branch_field` — querysetdan filialgacha bo'lgan yo'l. Masalan:
    Student uchun "branch", Payment uchun "enrollment__group__branch".

    `teacher_field` — o'qituvchi uchun qo'shimcha cheklov: querysetdan o'qituvchining
    User'igacha bo'lgan yo'l (Group uchun "teacher__user"). Berilsa, o'qituvchi filialning
    hammasini emas, faqat o'ziga tegishli yozuvlarni ko'radi. Bitta yo'l bilan ifodalab
    bo'lmaydigan holatda view `filter_for_teacher()` ni qayta yozadi.

    Begona obyekt querysetda bo'lmagani uchun API 404 qaytaradi.
    """

    branch_field = "branch"
    teacher_field = None

    def get_queryset(self):
        queryset = super().get_queryset()

        # Swagger sxemasini yasashda foydalanuvchi yo'q — bo'sh queryset yetarli.
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()

        user = self.request.user
        if user.is_admin:
            return queryset

        queryset = queryset.filter(**{self.branch_field: user.branch_id})
        if user.is_teacher:
            queryset = self.filter_for_teacher(queryset, user)
        return queryset

    def filter_for_teacher(self, queryset, user):
        if self.teacher_field:
            return queryset.filter(**{self.teacher_field: user})
        return queryset
