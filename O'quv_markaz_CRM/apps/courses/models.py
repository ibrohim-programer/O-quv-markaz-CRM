from django.db import models


class Course(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    name = models.CharField("Nomi", max_length=150, unique=True)
    description = models.TextField("Tavsif", blank=True)
    duration_months = models.PositiveSmallIntegerField("Davomiyligi (oy)")
    # Butun kursning narxi. O'quvchi guruhga qo'shilganda kontrakt summasi shu narxdan olinadi.
    price = models.DecimalField("Narxi", max_digits=12, decimal_places=2)
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField("Yaratilgan sana", auto_now_add=True)

    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gt=0), name="course_price_positive"),
            models.CheckConstraint(condition=models.Q(duration_months__gt=0), name="course_duration_positive"),
        ]

    def __str__(self):
        return self.name
