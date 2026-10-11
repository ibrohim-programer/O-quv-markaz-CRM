from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from .permissions import RolePermission


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Validatsiya xatosi",
            value={
                "status_code": 400,
                "message": "Ma'lumotlar noto'g'ri.",
                "errors": {"amount": ["To'lov qarzdan oshib ketdi. Qolgan qarz: 1 000 000 so'm."]},
            },
            response_only=True,
        ),
        OpenApiExample(
            "Biznes qoida xatosi",
            value={
                "status_code": 400,
                "message": "Guruhda bo'sh joy yo'q (15/15).",
                "errors": {"non_field_errors": ["Guruhda bo'sh joy yo'q (15/15)."]},
            },
            response_only=True,
        ),
        OpenApiExample(
            "Ruxsat yo'q",
            value={"status_code": 403, "message": "Sizning rolingiz bu amalni bajara olmaydi.", "errors": {}},
            response_only=True,
        ),
    ]
)
class ErrorResponseSerializer(serializers.Serializer):
    """Barcha xatolarning yagona shakli (apps.common.exceptions.custom_exception_handler)."""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text="Maydon bo'yicha xatolar; faqat 400 da to'ladi, qolganlarida bo'sh.",
    )


ERROR_DESCRIPTIONS = {
    "400": "Ma'lumotlar noto'g'ri yoki biznes qoida buzildi",
    "401": "Token yuborilmagan, noto'g'ri yoki muddati o'tgan",
    "403": "Rolingiz bu amalga ruxsat bermaydi",
    "404": "Topilmadi (boshqa filial obyekti ham — uning borligi oshkor qilinmaydi)",
    "409": "Yozuvga bog'langan ma'lumotlar bor — o'chirib bo'lmaydi",
    "429": "So'rovlar juda ko'p — Retry-After soniyadan keyin urinib ko'ring",
}


class CrmAutoSchema(AutoSchema):
    """
    Har bir endpointga u qaytarishi mumkin bo'lgan xato javoblarini qo'shadi (TZ 22-band: "Error
    response"). Qaysi xato bo'lishi view'dan aniqlanadi — har view'ga qo'lda yozish shart emas.
    """

    def _get_response_bodies(self, direction="response"):
        responses = super()._get_response_bodies(direction)
        for code in self._error_codes(responses):
            if code not in responses:
                response = self._get_response_for_code(ErrorResponseSerializer, code, direction=direction)
                response["description"] = ERROR_DESCRIPTIONS[code]
                responses[code] = response
        return responses

    def _error_codes(self, responses):
        codes = []
        if self.method in ("POST", "PUT", "PATCH") or self._has_query_validation():
            codes.append("400")
        if self.method == "DELETE":
            # 204 — yozuv haqiqatan o'chiriladi (bog'liq yozuv bo'lsa — 409). Javobida body bor DELETE
            # (to'lovni bekor qilish) yozuvni o'chirmaydi — u biznes qoida xatosini (400) qaytaradi.
            codes.append("409" if "204" in responses else "400")
        codes.append("401")
        if any(isinstance(permission, RolePermission) for permission in self.view.get_permissions()):
            codes.append("403")
        if "{" in self.path:
            codes.append("404")
        if self.view.get_throttles():
            codes.append("429")
        return codes

    def _has_query_validation(self):
        """GET ro'yxatdagi filtr qiymati noto'g'ri bo'lsa (?date_from=abc) — 400."""
        view = self.view
        has_filters = getattr(view, "filterset_class", None) or getattr(view, "filterset_fields", None)
        return self.method == "GET" and has_filters and self._is_list_view()
