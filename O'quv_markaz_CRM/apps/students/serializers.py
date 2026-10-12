from django.utils import timezone
from rest_framework import serializers

from apps.branches.models import Branch
from apps.branches.serializers import BranchShortSerializer
from apps.common.validators import branch_for_user
from apps.groups.models import Enrollment

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False)

    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "extra_phone",
            "birth_date",
            "gender",
            "address",
            "branch",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_birth_date(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Tug'ilgan sana kelajakda bo'lishi mumkin emas.")
        return value

    def validate(self, attrs):
        student = self.instance
        branch = attrs.get("branch", student.branch if student else None)
        attrs["branch"] = branch_for_user(self.context["request"].user, branch)

        # O'quvchi va uning guruhi har doim bir filialda bo'ladi.
        if student is not None and attrs["branch"] != student.branch:
            if student.enrollments.filter(status=Enrollment.Status.ACTIVE).exists():
                raise serializers.ValidationError(
                    {
                        "branch": "Guruhda o'qiyotgan o'quvchini boshqa filialga o'tkazib bo'lmaydi — "
                        "avval guruhdan chiqaring."
                    }
                )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["branch"] = BranchShortSerializer(instance.branch).data
        return data


class StudentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "full_name", "phone"]
