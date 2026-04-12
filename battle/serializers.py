from rest_framework import serializers

from battle.models import Battle, Turn
from pokedex.models import Move, MyPokemon
from pokedex.serializers import MyPokemonSerializer


class TurnSerializer(serializers.ModelSerializer):
    attacker_name = serializers.CharField(source="attacker.__str__", read_only=True)
    defender_name = serializers.CharField(source="defender.__str__", read_only=True)
    move_name = serializers.CharField(source="move_used.name", read_only=True)

    class Meta:
        model = Turn
        fields = [
            "id",
            "turn_number",
            "attacker",
            "attacker_name",
            "defender",
            "defender_name",
            "move_used",
            "move_name",
            "damage_dealt",
            "effectiveness",
            "random_factor",
            "defender_hp_before",
            "defender_hp_after",
        ]


class BattleCreateSerializer(serializers.Serializer):
    """Input para crear una batalla: solo los IDs de los dos Pokémon."""

    pokemon_1_id = serializers.PrimaryKeyRelatedField(
        queryset=MyPokemon.objects.all(), source="pokemon_1"
    )
    pokemon_2_id = serializers.PrimaryKeyRelatedField(
        queryset=MyPokemon.objects.all(), source="pokemon_2"
    )


class BattleDetailSerializer(serializers.ModelSerializer):
    pokemon_1 = MyPokemonSerializer(read_only=True)
    pokemon_2 = MyPokemonSerializer(read_only=True)
    winner = MyPokemonSerializer(read_only=True)
    turns = TurnSerializer(many=True, read_only=True)

    class Meta:
        model = Battle
        fields = [
            "id",
            "pokemon_1",
            "pokemon_2",
            "status",
            "winner",
            "current_turn",
            "turns",
            "created_at",
            "updated_at",
        ]


class ExecuteTurnSerializer(serializers.Serializer):
    """Input para ejecutar un turno: atacante y movimiento a usar."""

    attacker_id = serializers.PrimaryKeyRelatedField(
        queryset=MyPokemon.objects.all(), source="attacker"
    )
    move_id = serializers.PrimaryKeyRelatedField(
        queryset=Move.objects.all(), source="move"
    )
