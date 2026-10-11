from rest_framework import serializers

from .models import Course


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name", "description", "duration_months", "price", "status", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Kurs nomi kamida 2 ta belgi bo'lishi kerak.")
        return value

    def validate_duration_months(self, value):
        if value < 1:
            raise serializers.ValidationError("Kurs davomiyligi kamida 1 oy bo'lishi kerak.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Kurs narxi 0 dan katta bo'lishi kerak.")
        return value


class CourseShortSerializer(serializers.ModelSerializer):
    """Boshqa obyektlar ichida kursni qisqa ko'rsatish uchun: {id, name}."""

    class Meta:
        model = Course
        fields = ["id", "name"]
