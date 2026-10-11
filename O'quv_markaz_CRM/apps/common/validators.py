from django.core.validators import RegexValidator
from rest_framework import serializers

uz_phone_validator = RegexValidator(
    regex=r"^\+998\d{9}$",
    message="Telefon raqam +998901234567 formatida bo'lishi kerak.",
)


def branch_for_user(user, branch):
    if user.is_admin:
        if branch is None:
            raise serializers.ValidationError({"branch": "Filialni tanlash majburiy."})
        return branch
    if branch is not None and branch.id != user.branch_id:
        raise serializers.ValidationError({"branch": "Faqat o'z filialingiz uchun yozuv qo'sha olasiz."})
    return user.branch
