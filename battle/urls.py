from django.urls import include, path
from rest_framework.routers import DefaultRouter

from battle.views import BattleViewSet

router = DefaultRouter()
router.register(r"battles", BattleViewSet, basename="battle")

urlpatterns = [
    path("", include(router.urls)),
]
