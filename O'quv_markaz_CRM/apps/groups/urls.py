from rest_framework.routers import SimpleRouter

from .views import EnrollmentViewSet, GroupViewSet

router = SimpleRouter()
router.register("groups", GroupViewSet, basename="group")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")

urlpatterns = router.urls
