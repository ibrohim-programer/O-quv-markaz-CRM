from rest_framework import serializers

from apps.branches.models import Branch
from apps.branches.serializers import BranchShortSerializer
from apps.common.fields import BranchScopedPrimaryKeyRelatedField
from apps.common.validators import branch_for_user
from apps.courses.models import Course
from apps.courses.serializers import CourseShortSerializer
from apps.students.models import Student
from apps.students.serializers import StudentShortSerializer
from apps.teachers.models import Teacher
from apps.teachers.serializers import TeacherShortSerializer

from .models import Enrollment, Group, Weekday
from .services import enroll_student, update_enrollment


class GroupSerializer(serializers.ModelSerializer):
    # Admin filialni tanlaydi; boshqa xodimlarda filial avtomatik — o'z filiali.
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.select_related("user"))
    lesson_days = serializers.ListField(
        child=serializers.ChoiceField(choices=Weekday.choices),
        allow_empty=False,
        help_text="Dars kunlari: 0 — Dushanba ... 6 — Yakshanba. Masalan: [0, 2, 4].",
    )
    active_students_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "course",
            "teacher",
            "branch",
            "start_date",
            "end_date",
            "lesson_days",
            "start_time",
            "end_time",
            "max_students",
            "active_students_count",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        # Nomning filial ichida unikalligi validate() da tekshiriladi: non-admin filialni yubormaydi,
        # DRF'ning avtomatik UniqueTogetherValidator'i esa uni majburiy qilib qo'yardi.
        validators = []

    def get_active_students_count(self, group) -> int:
        # Ro'yxatda annotate() dan keladi — har guruh uchun alohida so'rov yo'q.
        count = getattr(group, "active_students_count", None)
        if count is None:
            count = group.enrollments.filter(status=Enrollment.Status.ACTIVE).count()
        return count

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Guruh nomi kamida 2 ta belgi bo'lishi kerak.")
        return value

    def validate_lesson_days(self, value):
        # [4, 0, 2, 2] -> [0, 2, 4]: takrorsiz va hafta tartibida saqlanadi.
        return sorted(set(value))

    def validate_max_students(self, value):
        if value < 1:
            raise serializers.ValidationError("Guruhda kamida 1 ta o'rin bo'lishi kerak.")
        if self.instance is not None:
            active_count = self.instance.enrollments.filter(status=Enrollment.Status.ACTIVE).count()
            if value < active_count:
                raise serializers.ValidationError(
                    f"Guruhda {active_count} ta faol o'quvchi bor — o'rinlar soni bundan kam bo'lolmaydi."
                )
        return value

    def validate(self, attrs):
        group = self.instance

        def value(field):
            return attrs.get(field, getattr(group, field, None))

        def changed(field):
            return group is None or (field in attrs and attrs[field] != getattr(group, field))

        branch = branch_for_user(self.context["request"].user, value("branch"))
        attrs["branch"] = branch
        has_students = group is not None and group.enrollments.exists()
        errors = {}

        if changed("branch") and has_students:
            errors["branch"] = "O'quvchisi bor guruhni boshqa filialga ko'chirib bo'lmaydi."

        if changed("course"):
            if attrs["course"].status != Course.Status.ACTIVE:
                errors["course"] = "Nofaol kursga guruh ochib bo'lmaydi."
            elif has_students:
                errors["course"] = "O'quvchisi bor guruhning kursini o'zgartirib bo'lmaydi."

        teacher = value("teacher")
        if changed("teacher") and teacher.status != Teacher.Status.ACTIVE:
            errors["teacher"] = "Nofaol o'qituvchiga guruh berib bo'lmaydi."
        elif (changed("teacher") or changed("branch")) and teacher.user.branch_id != branch.id:
            errors["teacher"] = "O'qituvchi boshqa filialda ishlaydi."

        if value("end_date") <= value("start_date"):
            errors["end_date"] = "Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak."
        if value("end_time") <= value("start_time"):
            errors["end_time"] = "Dars tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."

        if changed("name") or changed("branch"):
            same_name = Group.objects.filter(branch=branch, name=value("name"))
            if group is not None:
                same_name = same_name.exclude(pk=group.pk)
            if same_name.exists():
                errors["name"] = "Bu filialda shu nomli guruh bor."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["course"] = CourseShortSerializer(instance.course).data
        data["teacher"] = TeacherShortSerializer(instance.teacher).data
        data["branch"] = BranchShortSerializer(instance.branch).data
        return data


class GroupShortSerializer(serializers.ModelSerializer):
    """Boshqa obyektlar ichida guruhni qisqa ko'rsatish uchun: {id, name}."""

    class Meta:
        model = Group
        fields = ["id", "name"]


class EnrollmentSerializer(serializers.ModelSerializer):
    """Ko'rish va guruhga biriktirish (POST: student, group). Kontrakt — kursning hozirgi narxi."""

    student = BranchScopedPrimaryKeyRelatedField(
        queryset=Student.objects.all(), error_messages={"does_not_exist": "Bunday o'quvchi mavjud emas."}
    )
    group = BranchScopedPrimaryKeyRelatedField(
        queryset=Group.objects.all(), error_messages={"does_not_exist": "Bunday guruh mavjud emas."}
    )
    course = CourseShortSerializer(source="group.course", read_only=True)
    debt = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "group",
            "course",
            "contract_amount",
            "paid_amount",
            "debt",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "contract_amount", "paid_amount", "status", "created_at"]
        # (student, group) juftligini servis tekshiradi: guruhdan chiqqan o'quvchi qaytsa, eski a'zolik
        # faollashadi. DRF'ning avtomatik UniqueTogetherValidator'i buni xato deb rad etardi.
        validators = []

    def create(self, validated_data):
        return enroll_student(validated_data["student"], validated_data["group"])

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["student"] = StudentShortSerializer(instance.student).data
        data["group"] = GroupShortSerializer(instance.group).data
        return data


class EnrollmentUpdateSerializer(serializers.ModelSerializer):
    """Guruhdan chiqarish (status=left) va kontraktni o'zgartirish. Javob — to'liq a'zolik."""

    class Meta:
        model = Enrollment
        fields = ["status", "contract_amount"]

    def validate_status(self, value):
        if value == Enrollment.Status.ACTIVE and self.instance.status != Enrollment.Status.ACTIVE:
            # Qaytishda joy, guruh va o'quvchi holati qayta tekshirilishi kerak — bu biriktirish servisida.
            raise serializers.ValidationError(
                "Guruhga qaytarish uchun o'quvchini qayta biriktiring: POST /api/enrollments/."
            )
        return value

    def validate_contract_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Kontrakt summasi manfiy bo'lishi mumkin emas.")
        return value

    def update(self, instance, validated_data):
        return update_enrollment(instance, **validated_data)

    def to_representation(self, instance):
        return EnrollmentSerializer(instance, context=self.context).data
