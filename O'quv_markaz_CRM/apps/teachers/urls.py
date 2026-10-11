from rest_framework.routers import SimpleRouter

from .views import TeacherViewSet

router = SimpleRouter()
router.register("teachers", TeacherViewSet, basename="teacher")

urlpatterns = router.urls
