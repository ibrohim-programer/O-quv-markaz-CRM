from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.common.permissions import RolePermission

from .models import User
from .serializers import LogoutSerializer, MeSerializer, UserCreateSerializer, UserSerializer

Role = User.Role


@extend_schema(tags=["Auth"], summary="Tizimga kirish")
class LoginView(TokenObtainPairView):
    """
    Username va parol bilan kirish. Access (30 daqiqa) va refresh (7 kun) token qaytaradi.
    Bitta IP'dan daqiqasiga 5 tadan ortiq urinish — 429 (parolni terib topishga qarshi).
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


@extend_schema(tags=["Auth"], summary="Access tokenni yangilash")
class RefreshView(TokenRefreshView):
    """Refresh token bilan yangi access va yangi refresh token oladi. Eski refresh bekor bo'ladi."""


@extend_schema(tags=["Auth"], summary="Tizimdan chiqish", responses={204: None})
class LogoutView(GenericAPIView):
    """Refresh tokenni qora ro'yxatga qo'shadi — u bilan boshqa access olib bo'lmaydi."""

    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["refresh"].blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Auth"], summary="Mening profilim")
class MeView(RetrieveAPIView):
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


@extend_schema_view(
    list=extend_schema(summary="Xodimlar ro'yxati"),
    retrieve=extend_schema(summary="Bitta xodim"),
    create=extend_schema(summary="Manager yoki Operator yaratish (o'qituvchi — /teachers/)"),
    partial_update=extend_schema(summary="Xodimni tahrirlash yoki bloklash (is_active=false)"),
)
@extend_schema(tags=["Users"])
class UserViewSet(viewsets.ModelViewSet):
    """Xodimlarni faqat Admin boshqaradi. O'chirish yo'q — tarixi bor xodim bloklanadi."""

    queryset = User.objects.select_related("branch")
    permission_classes = [RolePermission]
    role_permissions = {
        "list": [Role.ADMIN],
        "retrieve": [Role.ADMIN],
        "create": [Role.ADMIN],
        "partial_update": [Role.ADMIN],
    }
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["role", "branch", "is_active"]
    search_fields = ["username", "first_name", "last_name", "phone"]
    ordering_fields = ["id", "username", "date_joined"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer
