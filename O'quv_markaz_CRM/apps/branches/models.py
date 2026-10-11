from django.db import models

from apps.common.validators import uz_phone_validator


class Branch(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    name = models.CharField("Nomi", max_length=150, unique=True)
    address = models.CharField("Manzil", max_length=255)
    phone = models.CharField("Telefon", max_length=13, validators=[uz_phone_validator])
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField("Yaratilgan sana", auto_now_add=True)

    class Meta:
        verbose_name = "Filial"
        verbose_name_plural = "Filiallar"
        ordering = ["name"]

    def __str__(self):
        return self.name
