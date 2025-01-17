from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PracticeViewSet

router = DefaultRouter()
router.register(r"", PracticeViewSet, basename="practice")

urlpatterns = [
    path("", include(router.urls)),
]
