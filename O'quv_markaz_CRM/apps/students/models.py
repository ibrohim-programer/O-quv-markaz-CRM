from django.db import models

from apps.common.validators import uz_phone_validator


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Erkak"
        FEMALE = "female", "Ayol"

    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        FROZEN = "frozen", "Muzlatilgan"
        GRADUATED = "graduated", "Bitirgan"
        LEFT = "left", "Ketgan"

    first_name = models.CharField("Ism", max_length=100)
    last_name = models.CharField("Familiya", max_length=100)
    phone = models.CharField("Telefon", max_length=13, validators=[uz_phone_validator])
    extra_phone = models.CharField(
        "Qo'shimcha telefon", max_length=13, blank=True, validators=[uz_phone_validator]
    )
    birth_date = models.DateField("Tug'ilgan sana", null=True, blank=True)
    gender = models.CharField("Jinsi", max_length=6, choices=Gender.choices)
    address = models.CharField("Manzil", max_length=255, blank=True)
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="Filial",
    )
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField("Ro'yxatdan o'tgan sana", auto_now_add=True)

    class Meta:
        verbose_name = "O'quvchi"
        verbose_name_plural = "O'quvchilar"
        ordering = ["-id"]
        indexes = [
            # Eng ko'p ishlatiladigan filtr: filial + status (/students/?status=active).
            models.Index(fields=["branch", "status"], name="student_branch_status_idx"),
            models.Index(fields=["created_at"], name="student_created_at_idx"),
            # Ism-familiya bo'yicha saralash (?ordering=last_name).
            models.Index(fields=["last_name", "first_name"], name="student_name_idx"),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
