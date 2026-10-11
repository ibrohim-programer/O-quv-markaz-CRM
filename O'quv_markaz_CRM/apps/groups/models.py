from django.db import models

# Create your models here.
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, Q


class Weekday(models.IntegerChoices):
    """Python'dagi date.weekday() bilan bir xil: 0 — Dushanba ... 6 — Yakshanba."""

    MONDAY = 0, "Dushanba"
    TUESDAY = 1, "Seshanba"
    WEDNESDAY = 2, "Chorshanba"
    THURSDAY = 3, "Payshanba"
    FRIDAY = 4, "Juma"
    SATURDAY = 5, "Shanba"
    SUNDAY = 6, "Yakshanba"


class Group(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        FINISHED = "finished", "Tugagan"
        CANCELLED = "cancelled", "Bekor qilingan"

    name = models.CharField("Nomi", max_length=100)
    course = models.ForeignKey(
        "courses.Course", on_delete=models.PROTECT, related_name="groups", verbose_name="Kurs"
    )
    teacher = models.ForeignKey(
        "teachers.Teacher", on_delete=models.PROTECT, related_name="groups", verbose_name="O'qituvchi"
    )
    branch = models.ForeignKey(
        "branches.Branch", on_delete=models.PROTECT, related_name="groups", verbose_name="Filial"
    )
    start_date = models.DateField("Boshlanish sanasi")
    end_date = models.DateField("Tugash sanasi")
    # JSONField'dan farqli, ArrayField faqat butun sonlar ro'yxatini qabul qiladi va
    # lesson_days__contains=[2] kabi filtrlanadi. Masalan, [0, 2, 4] — Du, Chor, Ju.
    lesson_days = ArrayField(
        models.PositiveSmallIntegerField(choices=Weekday.choices), verbose_name="Dars kunlari"
    )
    start_time = models.TimeField("Boshlanish vaqti")
    end_time = models.TimeField("Tugash vaqti")
    max_students = models.PositiveSmallIntegerField("Maksimal o'quvchilar soni")
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    students = models.ManyToManyField(
        "students.Student", through="Enrollment", related_name="groups", verbose_name="O'quvchilar"
    )
    created_at = models.DateTimeField("Yaratilgan sana", auto_now_add=True)

    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(fields=["branch", "name"], name="group_unique_name_per_branch"),
            models.CheckConstraint(
                condition=Q(end_date__gt=F("start_date")), name="group_end_date_after_start"
            ),
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")), name="group_end_time_after_start"
            ),
            models.CheckConstraint(condition=Q(max_students__gt=0), name="group_max_students_positive"),
            models.CheckConstraint(
                condition=Q(lesson_days__len__gt=0) & Q(lesson_days__contained_by=Weekday.values),
                name="group_lesson_days_valid",
            ),
        ]
        indexes = [models.Index(fields=["branch", "status"], name="group_branch_status_idx")]

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    """
    O'quvchining guruhdagi a'zoligi va kontrakti. Kontrakt — guruhga qo'shilgan paytdagi
    kurs narxi: keyin kurs narxi o'zgarsa ham, eski o'quvchilarning kontrakti o'zgarmaydi.
    Qarz saqlanmaydi, so'rov paytida hisoblanadi: contract_amount - paid_amount.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        LEFT = "left", "Guruhdan chiqqan"

    student = models.ForeignKey(
        "students.Student", on_delete=models.PROTECT, related_name="enrollments", verbose_name="O'quvchi"
    )
    group = models.ForeignKey(
        Group, on_delete=models.PROTECT, related_name="enrollments", verbose_name="Guruh"
    )
    contract_amount = models.DecimalField("Kontrakt summasi", max_digits=12, decimal_places=2)
    # Faqat to'lov servislari o'zgartiradi — to'lov yozilganda oshadi, bekor qilinganda kamayadi.
    paid_amount = models.DecimalField("To'langan summa", max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField("Guruhga qo'shilgan sana", auto_now_add=True)

    class Meta:
        verbose_name = "Guruhga a'zolik"
        verbose_name_plural = "Guruhga a'zoliklar"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(fields=["student", "group"], name="enrollment_unique_student_group"),
            models.CheckConstraint(
                condition=Q(contract_amount__gte=0), name="enrollment_contract_not_negative"
            ),
            models.CheckConstraint(condition=Q(paid_amount__gte=0), name="enrollment_paid_not_negative"),
            # Ortiqcha to'lovga qarshi oxirgi to'siq: kod xato qilsa ham baza buni qabul qilmaydi.
            models.CheckConstraint(
                condition=Q(paid_amount__lte=F("contract_amount")), name="enrollment_paid_within_contract"
            ),
        ]
        indexes = [
            # Guruhdagi faol o'quvchilarni sanash (joy bormi?) va ro'yxatini olish uchun.
            models.Index(fields=["group", "status"], name="enrollment_group_status_idx"),
            # Qarzdorlar ro'yxati: faqat qarzi borlar, eng katta qarz birinchi. Indekssiz Postgres
            # har so'rovda barcha qarzdorlarni join qilib saralaydi; indeks bilan — sahifadagi 20 tasini.
            models.Index(
                (F("contract_amount") - F("paid_amount")).desc(),
                "id",
                condition=Q(paid_amount__lt=F("contract_amount")),
                name="enrollment_debt_idx",
            ),
        ]

    def __str__(self):
        return f"{self.student} — {self.group}"

    @property
    def debt(self):
        return self.contract_amount - self.paid_amount
