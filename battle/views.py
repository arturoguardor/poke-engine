from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from battle.models import Battle
from battle.serializers import (
    BattleCreateSerializer,
    BattleDetailSerializer,
    ExecuteTurnSerializer,
    TurnSerializer,
)
from battle.services.battle_service import BattleService


class BattleViewSet(viewsets.ModelViewSet):
    """
    ViewSet de batalla.
    Solo admite GET y POST — una batalla no se puede editar ni eliminar.
    La batalla avanza únicamente a través del endpoint /turn/.
    """

    queryset = Battle.objects.select_related(
        "pokemon_1__base_pokemon__type_primary",
        "pokemon_1__base_pokemon__type_secondary",
        "pokemon_2__base_pokemon__type_primary",
        "pokemon_2__base_pokemon__type_secondary",
        "winner__base_pokemon",
    ).prefetch_related("turns")
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return BattleCreateSerializer
        return BattleDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        POST /api/v1/battles/
        Crea una nueva batalla. Delega a BattleService para validaciones de dominio.
        """
        serializer = BattleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        battle = BattleService.create_battle(
            serializer.validated_data["pokemon_1"],
            serializer.validated_data["pokemon_2"],
        )
        return Response(BattleDetailSerializer(battle).data, status=201)

    @action(detail=True, methods=["post"], url_path="turn")
    def execute_turn(self, request, pk=None):
        """
        POST /api/v1/battles/{id}/turn/
        Ejecuta un turno de batalla.
        Body: {"attacker_id": 1, "move_id": 3}
        """
        battle = self.get_object()
        serializer = ExecuteTurnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        turn, warning = BattleService.execute_turn(
            battle=battle,
            attacker=serializer.validated_data["attacker"],
            move=serializer.validated_data["move"],
        )

        response_data = TurnSerializer(turn).data
        if warning:
            response_data["warning"] = warning

        return Response(response_data, status=200)
