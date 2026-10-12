from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.common.money import format_sum
from apps.students.models import Student

from .models import Enrollment, Group


@transaction.atomic
def enroll_student(student, group):

    group = Group.objects.select_for_update(of=("self",)).select_related("course").get(pk=group.pk)

    if student.branch_id != group.branch_id:
        raise ValidationError("O'quvchi va guruh boshqa-boshqa filialda.")
    if group.status != Group.Status.ACTIVE:
        raise ValidationError("Guruh faol emas.")
    if student.status != Student.Status.ACTIVE:
        raise ValidationError("Faqat faol o'quvchini guruhga qo'shish mumkin.")

    enrollment = Enrollment.objects.filter(student=student, group=group).first()
    if enrollment is not None and enrollment.status == Enrollment.Status.ACTIVE:
        raise ValidationError("O'quvchi allaqachon shu guruhda.")

    active_count = group.enrollments.filter(status=Enrollment.Status.ACTIVE).count()
    if active_count >= group.max_students:
        raise ValidationError(f"Guruhda bo'sh joy yo'q ({active_count}/{group.max_students}).")

    if enrollment is not None:
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])
        return enrollment
    return Enrollment.objects.create(student=student, group=group, contract_amount=group.course.price)


@transaction.atomic
def update_enrollment(enrollment, **changes):
  
    enrollment = Enrollment.objects.select_for_update().get(pk=enrollment.pk)

    contract_amount = changes.get("contract_amount", enrollment.contract_amount)
    if contract_amount < enrollment.paid_amount:
        raise ValidationError(
            {
                "contract_amount": "Kontrakt to'langan summadan "
                f"({format_sum(enrollment.paid_amount)}) kam bo'lishi mumkin emas."
            }
        )

    for field, value in changes.items():
        setattr(enrollment, field, value)
    enrollment.save(update_fields=list(changes))
    return enrollment
