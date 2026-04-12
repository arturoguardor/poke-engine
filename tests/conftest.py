from decimal import Decimal

import pytest

from pokedex.models import BasePokemon, Move, MyPokemon, PokemonType, TypeEffectiveness


@pytest.fixture
def fire_type(db):
    return PokemonType.objects.create(name="fire")


@pytest.fixture
def water_type(db):
    return PokemonType.objects.create(name="water")


@pytest.fixture
def normal_type(db):
    return PokemonType.objects.create(name="normal")


@pytest.fixture
def ghost_type(db):
    return PokemonType.objects.create(name="ghost")


@pytest.fixture
def fire_vs_water(db, fire_type, water_type):
    """Fuego vs Agua: ×0.5 (poco efectivo)."""
    return TypeEffectiveness.objects.create(
        attacking_type=fire_type,
        defending_type=water_type,
        multiplier=Decimal("0.5"),
    )


@pytest.fixture
def water_vs_fire(db, water_type, fire_type):
    """Agua vs Fuego: ×2.0 (superefectivo)."""
    return TypeEffectiveness.objects.create(
        attacking_type=water_type,
        defending_type=fire_type,
        multiplier=Decimal("2.0"),
    )


@pytest.fixture
def normal_vs_ghost(db, normal_type, ghost_type):
    """Normal vs Fantasma: ×0.0 (inmune)."""
    return TypeEffectiveness.objects.create(
        attacking_type=normal_type,
        defending_type=ghost_type,
        multiplier=Decimal("0.0"),
    )


@pytest.fixture
def charmander_base(db, fire_type):
    return BasePokemon.objects.create(
        pokeapi_id=4,
        name="charmander",
        type_primary=fire_type,
        base_hp=39,
        base_attack=52,
        base_defense=43,
        base_sp_attack=60,
        base_sp_defense=50,
        base_speed=65,
    )


@pytest.fixture
def squirtle_base(db, water_type):
    return BasePokemon.objects.create(
        pokeapi_id=7,
        name="squirtle",
        type_primary=water_type,
        base_hp=44,
        base_attack=48,
        base_defense=65,
        base_sp_attack=50,
        base_sp_defense=64,
        base_speed=43,
    )


@pytest.fixture
def ember(db, fire_type, charmander_base):
    """Movimiento Ascuas: fuego, poder 40."""
    move = Move.objects.create(
        pokeapi_id=52,
        name="ember",
        move_type=fire_type,
        power=40,
    )
    charmander_base.learnable_moves.add(move)
    return move


@pytest.fixture
def water_gun(db, water_type, squirtle_base):
    """Movimiento Pistola Agua: agua, poder 40."""
    move = Move.objects.create(
        pokeapi_id=55,
        name="water-gun",
        move_type=water_type,
        power=40,
    )
    squirtle_base.learnable_moves.add(move)
    return move


@pytest.fixture
def charmander(db, charmander_base, ember):
    """MyPokemon Charmander nivel 50."""
    pokemon = MyPokemon(base_pokemon=charmander_base, level=50)
    pokemon.save()
    pokemon.moves.add(ember)
    return pokemon


@pytest.fixture
def squirtle(db, squirtle_base, water_gun):
    """MyPokemon Squirtle nivel 50."""
    pokemon = MyPokemon(base_pokemon=squirtle_base, level=50)
    pokemon.save()
    pokemon.moves.add(water_gun)
    return pokemon
