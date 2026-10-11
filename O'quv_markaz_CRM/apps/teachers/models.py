from django.conf import settings
from django.db import models


class Teacher(models.Model):
    """
    O'qituvchi profili. Ism, familiya, telefon, email va filial — User'da (o'qituvchi tizimga
    kirib davomat qiladi), bu yerda faqat o'qituvchiga xos maydonlar.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": "teacher"},
        verbose_name="Foydalanuvchi",
    )
    specialization = models.CharField("Mutaxassisligi", max_length=150)
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField("Yaratilgan sana", auto_now_add=True)

    class Meta:
        verbose_name = "O'qituvchi"
        verbose_name_plural = "O'qituvchilar"
        ordering = ["id"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username
