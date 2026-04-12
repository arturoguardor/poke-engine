from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from pokedex.models import BasePokemon, Move, MyPokemon, PokemonType
from pokedex.serializers import (
    BasePokemonSerializer,
    DamageCalculationSerializer,
    DamageResultSerializer,
    MoveSerializer,
    MyPokemonSerializer,
    PokemonTypeSerializer,
)
from pokedex.services.damage_service import DamageService
from pokedex.services.pokeapi_service import (
    fetch_and_save_base_pokemon,
    fetch_learnable_moves,
    save_moves_for_pokemon,
)


class PokemonTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solo lectura — los tipos son datos de referencia cargados desde fixtures.
    No se modifican por API.
    """

    queryset = PokemonType.objects.all()
    serializer_class = PokemonTypeSerializer


class BasePokemonViewSet(viewsets.ModelViewSet):
    queryset = BasePokemon.objects.select_related(
        "type_primary", "type_secondary"
    ).prefetch_related("learnable_moves__move_type")
    serializer_class = BasePokemonSerializer

    @action(detail=False, methods=["post"], url_path="fetch")
    def fetch_from_pokeapi(self, request):
        """
        POST /api/v1/pokemon/fetch/
        Añade un BasePokemon desde PokéAPI a la BD.
        Body: {"name_or_id": "pikachu"} o {"name_or_id": 25}
        """
        name_or_id = request.data.get("name_or_id")
        if not name_or_id:
            return Response({"error": "Se requiere el campo 'name_or_id'."}, status=400)
        try:
            pokemon, created = fetch_and_save_base_pokemon(name_or_id)
            moves_data = fetch_learnable_moves(pokemon.pokeapi_id, limit=4)
            save_moves_for_pokemon(pokemon, moves_data)
        except Exception as e:
            return Response({"error": str(e)}, status=502)

        status_code = 201 if created else 200
        return Response(BasePokemonSerializer(pokemon).data, status=status_code)

    @action(detail=True, methods=["get"], url_path="moves")
    def same_type_moves(self, request, pk=None):
        """
        GET /api/v1/pokemon/{id}/moves/
        Movimientos del mismo tipo que el Pokémon (tipo primario o secundario).
        """
        pokemon = self.get_object()
        type_ids = [pokemon.type_primary_id]
        if pokemon.type_secondary_id:
            type_ids.append(pokemon.type_secondary_id)
        moves = Move.objects.filter(move_type_id__in=type_ids).select_related(
            "move_type"
        )
        return Response(MoveSerializer(moves, many=True).data)

    @action(detail=True, methods=["get"], url_path="possible-moves")
    def possible_moves(self, request, pk=None):
        """
        GET /api/v1/pokemon/{id}/possible-moves/
        Movimientos que el Pokémon puede aprender (M2M learnable_moves).
        """
        pokemon = self.get_object()
        moves = pokemon.learnable_moves.select_related("move_type")
        return Response(MoveSerializer(moves, many=True).data)


class MoveViewSet(viewsets.ModelViewSet):
    queryset = Move.objects.select_related("move_type").prefetch_related("learnable_by")
    serializer_class = MoveSerializer

    @action(detail=True, methods=["get"], url_path="pokemon")
    def learnable_by_pokemon(self, request, pk=None):
        """
        GET /api/v1/moves/{id}/pokemon/
        BasePokemon que pueden aprender este movimiento.
        """
        move = self.get_object()
        pokemon = move.learnable_by.select_related("type_primary", "type_secondary")
        return Response(BasePokemonSerializer(pokemon, many=True).data)


class MyPokemonViewSet(viewsets.ModelViewSet):
    queryset = MyPokemon.objects.select_related(
        "base_pokemon__type_primary", "base_pokemon__type_secondary"
    ).prefetch_related("moves__move_type")
    serializer_class = MyPokemonSerializer

    @action(detail=False, methods=["post"], url_path="catch")
    def catch(self, request):
        """
        POST /api/v1/my-pokemon/catch/
        Crea una instancia nueva de MyPokemon (atrapar un Pokémon).
        Equivalente a POST / pero con una URL semánticamente más expresiva.
        """
        serializer = MyPokemonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["post"], url_path="heal")
    def heal(self, request, pk=None):
        """
        POST /api/v1/my-pokemon/{id}/heal/
        Restaura el HP actual del Pokémon a su máximo.
        Sin este endpoint, un Pokémon que llega a 0 PS queda inutilizable para siempre.
        """
        pokemon = self.get_object()
        pokemon.hp_current = pokemon.hp_max
        pokemon.save(update_fields=["hp_current"])
        return Response(MyPokemonSerializer(pokemon).data)


class DamageView(APIView):
    """
    POST /api/v1/damage/calculate/
    Calcula el daño de un movimiento entre dos MyPokemon.
    No persiste nada — útil para simular combates o validar builds.
    Implementa la Parte 1 del enunciado de forma aislada.
    """

    def post(self, request):
        serializer = DamageCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = DamageService.calculate(**serializer.validated_data)
        return Response(DamageResultSerializer(result).data, status=200)
