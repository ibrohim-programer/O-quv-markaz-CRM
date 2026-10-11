from rest_framework import serializers

from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "address", "phone", "status", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Filial nomi kamida 3 ta belgi bo'lishi kerak.")
        return value


class BranchShortSerializer(serializers.ModelSerializer):
    "Boshqa obyektlar ichida filialni qisqa ko'rsatish uchun: {id, name}."

    class Meta:
        model = Branch
        fields = ["id", "name"]
