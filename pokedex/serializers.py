from rest_framework import serializers

from pokedex.models import BasePokemon, Move, MyPokemon, PokemonType


class PokemonTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PokemonType
        fields = ["id", "name"]


class MoveSerializer(serializers.ModelSerializer):
    move_type = PokemonTypeSerializer(read_only=True)
    move_type_id = serializers.PrimaryKeyRelatedField(
        queryset=PokemonType.objects.all(), source="move_type", write_only=True
    )
    learnable_by = serializers.PrimaryKeyRelatedField(
        many=True, queryset=BasePokemon.objects.all(), required=False
    )

    class Meta:
        model = Move
        fields = [
            "id",
            "pokeapi_id",
            "name",
            "move_type",
            "move_type_id",
            "power",
            "learnable_by",
        ]


class BasePokemonSerializer(serializers.ModelSerializer):
    type_primary = PokemonTypeSerializer(read_only=True)
    type_primary_id = serializers.PrimaryKeyRelatedField(
        queryset=PokemonType.objects.all(), source="type_primary", write_only=True
    )
    type_secondary = PokemonTypeSerializer(read_only=True)
    type_secondary_id = serializers.PrimaryKeyRelatedField(
        queryset=PokemonType.objects.all(),
        source="type_secondary",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = BasePokemon
        fields = [
            "id",
            "pokeapi_id",
            "name",
            "type_primary",
            "type_primary_id",
            "type_secondary",
            "type_secondary_id",
            "base_hp",
            "base_attack",
            "base_defense",
            "base_sp_attack",
            "base_sp_defense",
            "base_speed",
        ]


class MyPokemonSerializer(serializers.ModelSerializer):
    base_pokemon_id = serializers.PrimaryKeyRelatedField(
        queryset=BasePokemon.objects.all(), source="base_pokemon"
    )
    base_pokemon_name = serializers.CharField(
        source="base_pokemon.name", read_only=True
    )
    move_ids = serializers.PrimaryKeyRelatedField(
        queryset=Move.objects.all(),
        source="moves",
        many=True,
        required=False,
    )
    moves = MoveSerializer(many=True, read_only=True)

    class Meta:
        model = MyPokemon
        fields = [
            "id",
            "base_pokemon_id",
            "base_pokemon_name",
            "nickname",
            "level",
            "move_ids",
            "moves",
            "hp_max",
            "hp_current",
            "attack",
            "defense",
            "sp_attack",
            "sp_defense",
            "speed",
            "created_at",
        ]
        read_only_fields = [
            "hp_max",
            "hp_current",
            "attack",
            "defense",
            "sp_attack",
            "sp_defense",
            "speed",
            "created_at",
        ]

    def validate_move_ids(self, moves):
        """Máximo 4 movimientos por Pokémon."""
        if len(moves) > 4:
            raise serializers.ValidationError(
                "Un Pokémon no puede tener más de 4 movimientos."
            )
        return moves

    def validate(self, attrs):
        """Valida que los movimientos asignados sean aprendibles por la especie."""
        base_pokemon = attrs.get("base_pokemon") or (
            self.instance.base_pokemon if self.instance else None
        )
        moves = attrs.get("moves", [])
        if base_pokemon and moves:
            learnable_ids = set(
                base_pokemon.learnable_moves.values_list("id", flat=True)
            )
            invalid = [m.name for m in moves if m.id not in learnable_ids]
            if invalid:
                raise serializers.ValidationError(
                    f"Movimientos no aprendibles por {base_pokemon.name}: {invalid}"
                )
        return attrs

    def create(self, validated_data):
        moves = validated_data.pop("moves", [])
        instance = MyPokemon(**validated_data)
        instance.save()  # calculate_stats() se llama dentro de save()
        if moves:
            instance.moves.set(moves)
        return instance

    def update(self, instance, validated_data):
        moves = validated_data.pop("moves", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if moves is not None:
            instance.moves.set(moves)
        return instance


# --- Serializers para el endpoint de cálculo de daño ---


class DamageCalculationSerializer(serializers.Serializer):
    """Input para POST /api/v1/damage/calculate/"""

    attacker_id = serializers.PrimaryKeyRelatedField(
        queryset=MyPokemon.objects.all(), source="attacker"
    )
    move_id = serializers.PrimaryKeyRelatedField(
        queryset=Move.objects.all(), source="move"
    )
    defender_id = serializers.PrimaryKeyRelatedField(
        queryset=MyPokemon.objects.all(), source="defender"
    )


class DamageResultSerializer(serializers.Serializer):
    """Output para POST /api/v1/damage/calculate/"""

    damage = serializers.IntegerField()
    effectiveness = serializers.DecimalField(max_digits=3, decimal_places=1)
    random_factor = serializers.IntegerField()
