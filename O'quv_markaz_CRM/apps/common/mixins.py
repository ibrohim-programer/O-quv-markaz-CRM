class BranchScopedMixin:


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
