from django.urls import include, path
from rest_framework.routers import DefaultRouter

from pokedex.views import (
    BasePokemonViewSet,
    DamageView,
    MoveViewSet,
    MyPokemonViewSet,
    PokemonTypeViewSet,
)

router = DefaultRouter()
router.register(r"pokemon", BasePokemonViewSet, basename="pokemon")
router.register(r"moves", MoveViewSet, basename="move")
router.register(r"my-pokemon", MyPokemonViewSet, basename="my-pokemon")
router.register(r"types", PokemonTypeViewSet, basename="type")

urlpatterns = [
    path("", include(router.urls)),
    path("damage/calculate/", DamageView.as_view(), name="damage-calculate"),
]
