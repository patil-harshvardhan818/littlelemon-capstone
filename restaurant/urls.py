from rest_framework.routers import SimpleRouter

from .views import BookingViewSet, MenuViewSet

router = SimpleRouter()
router.register("menu", MenuViewSet, basename="menu")
router.register("booking/tables", BookingViewSet, basename="booking")

urlpatterns = router.urls
