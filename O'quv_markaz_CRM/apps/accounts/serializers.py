from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.branches.models import Branch
from apps.branches.serializers import BranchShortSerializer

from .models import User


class MeSerializer(serializers.ModelSerializer):
    branch = BranchShortSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "phone", "role", "branch"]
        read_only_fields = fields


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
        except TokenError:
            raise serializers.ValidationError("Token noto'g'ri, muddati o'tgan yoki allaqachon bekor qilingan.")

        user = self.context["request"].user
        if str(token.get("user_id")) != str(user.pk):
            raise serializers.ValidationError("Bu token sizga tegishli emas.")
        return token


class UserSerializer(serializers.ModelSerializer):
    """Xodimni ko'rish va tahrirlash (PATCH). Yaratish — UserCreateSerializer."""

    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "branch",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "username", "date_joined", "last_login"]

    def validate(self, attrs):
        instance = self.instance
        role = attrs.get("role", instance.role if instance else None)
        branch = attrs.get("branch", instance.branch if instance else None)

        if instance is not None:
            if (instance.role == User.Role.TEACHER) != (role == User.Role.TEACHER):
                raise serializers.ValidationError(
                    {"role": "O'qituvchi rolini bu yerda berib ham, olib ham bo'lmaydi — /api/teachers/ dan foydalaning."}
                )
            if instance == self.context["request"].user:
                if role != User.Role.ADMIN or attrs.get("is_active") is False:
                    raise serializers.ValidationError(
                        {"detail": "O'zingizning admin rolingizni olib tashlay yoki o'zingizni bloklay olmaysiz."}
                    )

        attrs["branch"] = _branch_for_role(role, branch)
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["branch"] = BranchShortSerializer(instance.branch).data if instance.branch else None
        return data


class UserCreateSerializer(UserSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["password"]
        read_only_fields = ["id", "date_joined", "last_login"]

    def validate_role(self, value):
        if value == User.Role.TEACHER:
            raise serializers.ValidationError("O'qituvchi /api/teachers/ orqali yaratiladi.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        password = attrs.get("password")
        user_data = {key: value for key, value in attrs.items() if key != "password"}
        try:
            validate_password(password, user=User(**user_data))
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


def _branch_for_role(role, branch):
    """Admin filialsiz bo'ladi; qolgan rollarga filial majburiy."""
    if role == User.Role.ADMIN:
        return None
    if branch is None:
        raise serializers.ValidationError({"branch": "Bu rol uchun filialni tanlash majburiy."})
    return branch


class UserShortSerializer(serializers.ModelSerializer):
    """Boshqa obyektlar ichida xodimni qisqa ko'rsatish uchun: {id, username}."""

    class Meta:
        model = User
        fields = ["id", "username"]
