from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.branches.serializers import BranchShortSerializer
from apps.common.validators import uz_phone_validator

from .models import Teacher
from .services import create_teacher, update_teacher


class TeacherSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", max_length=150)
    last_name = serializers.CharField(source="user.last_name", max_length=150)
    phone = serializers.CharField(source="user.phone", max_length=13, validators=[uz_phone_validator])
    email = serializers.EmailField(source="user.email", required=False, allow_blank=True)
    branch = serializers.PrimaryKeyRelatedField(source="user.branch", queryset=Branch.objects.all())

    class Meta:
        model = Teacher
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "phone",
            "email",
            "branch",
            "specialization",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        branch = attrs.get("user", {}).get("branch")
        if self.instance is not None and branch is not None and branch != self.instance.user.branch:
            groups = self.instance.groups
            if groups.filter(status=groups.model.Status.ACTIVE).exists():
                raise serializers.ValidationError(
                    {"branch": "Faol guruhi bor o'qituvchini boshqa filialga o'tkazib bo'lmaydi."}
                )
        return attrs

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        return update_teacher(instance, user_data, **validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["branch"] = BranchShortSerializer(instance.user.branch).data
        return data


class TeacherCreateSerializer(TeacherSerializer):

    username = serializers.CharField(
        source="user.username",
        max_length=150,
        validators=[
            User.username_validator,
            UniqueValidator(queryset=User.objects.all(), message="Bu username band."),
        ],
    )
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta(TeacherSerializer.Meta):
        fields = TeacherSerializer.Meta.fields + ["password"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        try:
            validate_password(attrs["password"], user=User(**attrs["user"]))
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)})
        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        password = validated_data.pop("password")
        return create_teacher(user_data, password, **validated_data)


class TeacherShortSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "full_name"]
