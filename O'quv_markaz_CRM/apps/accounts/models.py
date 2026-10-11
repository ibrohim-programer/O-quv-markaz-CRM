from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.validators import uz_phone_validator


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        OPERATOR = "operator", "Operator"
        TEACHER = "teacher", "O'qituvchi"

    role = models.CharField("Rol", max_length=10, choices=Role.choices)
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Filial",
    )
    phone = models.CharField(
        "Telefon", max_length=13, blank=True, validators=[uz_phone_validator]
    )

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role="admin") | models.Q(branch__isnull=False),
                name="user_non_admin_has_branch",
            ),
        ]

    def clean(self):
        super().clean()
        if self.role != self.Role.ADMIN and self.branch_id is None:
            raise ValidationError({"branch": "Admin'dan boshqa xodim filialga biriktirilishi shart."})

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_operator(self):
        return self.role == self.Role.OPERATOR

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER
