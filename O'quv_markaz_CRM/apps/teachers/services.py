from django.db import transaction

from apps.accounts.models import User

from .models import Teacher


@transaction.atomic
def create_teacher(user_data, password, **profile_data):
  
    user = User.objects.create_user(role=User.Role.TEACHER, password=password, **user_data)
    return Teacher.objects.create(user=user, **profile_data)


@transaction.atomic
def update_teacher(teacher, user_data, **profile_data):
    if user_data:
        for field, value in user_data.items():
            setattr(teacher.user, field, value)
        teacher.user.save(update_fields=list(user_data))

    for field, value in profile_data.items():
        setattr(teacher, field, value)
    teacher.save()
    return teacher
