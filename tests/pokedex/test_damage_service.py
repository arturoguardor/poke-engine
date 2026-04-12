"""
Tests unitarios para DamageService.
Validan la fórmula del enunciado:
  Daño = {[(2*Nivel/5+2) * Ataque * Poder / Defensa] / 50} * Efectividad * Random/100

Se usa FixedRandomFactor para obtener resultados deterministas sin mockear stdlib_random.
Todos los tests usan la BD de test (pytest-django con @pytest.mark.django_db implícito via fixture).
"""

import math
from decimal import Decimal

from pokedex.models import BasePokemon, Move, MyPokemon, PokemonType, TypeEffectiveness
from pokedex.services.damage_service import DamageService, FixedRandomFactor


def calcular_daño_esperado(nivel, ataque, poder, defensa, efectividad, random_factor):
    """Replica la fórmula del enunciado para verificar los resultados de DamageService."""
    raw = ((2 * nivel / 5 + 2) * ataque * poder / defensa) / 50
    return math.floor(raw * efectividad * random_factor / 100)


class TestDamageServiceFormula:

    def test_formula_efectividad_neutra(
        self, charmander, squirtle, ember, fire_vs_water
    ):
        """
        Efectividad neutra (×1.0): el daño debe coincidir exactamente con la fórmula.
        Nota: fire_vs_water es ×0.5 — aquí se usa una efectividad neutra creada ad-hoc.
        """
        # Creamos efectividad neutra fuego vs fuego para este test
        TypeEffectiveness.objects.create(
            attacking_type=ember.move_type,
            defending_type=charmander.base_pokemon.type_primary,
            multiplier=Decimal("1.0"),
        )
        result = DamageService.calculate(
            attacker=charmander,
            move=ember,
            defender=charmander,  # se ataca a sí mismo para usar efectividad ×1.0
            random_strategy=FixedRandomFactor(100),
        )
        esperado = calcular_daño_esperado(
            nivel=charmander.level,
            ataque=charmander.attack,
            poder=ember.power,
            defensa=charmander.defense,
            efectividad=1.0,
            random_factor=100,
        )
        assert result.damage == esperado
        assert result.effectiveness == Decimal("1.0")
        assert result.random_factor == 100

    def test_formula_superefectivo(
        self, charmander, squirtle, water_gun, water_vs_fire
    ):
        """
        Agua vs Fuego (×2.0): el daño debe ser el doble respecto a efectividad neutra.
        """
        result = DamageService.calculate(
            attacker=squirtle,
            move=water_gun,
            defender=charmander,
            random_strategy=FixedRandomFactor(100),
        )
        esperado = calcular_daño_esperado(
            nivel=squirtle.level,
            ataque=squirtle.attack,
            poder=water_gun.power,
            defensa=charmander.defense,
            efectividad=2.0,
            random_factor=100,
        )
        assert result.damage == esperado
        assert result.effectiveness == Decimal("2.0")

    def test_formula_poco_efectivo(self, charmander, squirtle, ember, fire_vs_water):
        """
        Fuego vs Agua (×0.5): el daño debe ser la mitad respecto a efectividad neutra.
        """
        result = DamageService.calculate(
            attacker=charmander,
            move=ember,
            defender=squirtle,
            random_strategy=FixedRandomFactor(100),
        )
        esperado = calcular_daño_esperado(
            nivel=charmander.level,
            ataque=charmander.attack,
            poder=ember.power,
            defensa=squirtle.defense,
            efectividad=0.5,
            random_factor=100,
        )
        assert result.damage == esperado
        assert result.effectiveness == Decimal("0.5")

    def test_formula_inmunidad(self, db, normal_type, ghost_type, normal_vs_ghost):
        """
        Normal vs Fantasma (×0.0): daño = 0 (inmunidad).
        No se aplica max(1, damage) — fiel al enunciado y al juego original.
        """
        base_normal = BasePokemon.objects.create(
            name="snorlax",
            type_primary=normal_type,
            base_hp=160,
            base_attack=110,
            base_defense=65,
            base_sp_attack=65,
            base_sp_defense=110,
            base_speed=30,
        )
        base_ghost = BasePokemon.objects.create(
            name="gastly",
            type_primary=ghost_type,
            base_hp=30,
            base_attack=35,
            base_defense=30,
            base_sp_attack=100,
            base_sp_defense=35,
            base_speed=80,
        )
        tackle = Move.objects.create(
            name="tackle",
            move_type=normal_type,
            power=40,
        )
        base_normal.learnable_moves.add(tackle)

        snorlax = MyPokemon(base_pokemon=base_normal, level=50)
        snorlax.save()
        snorlax.moves.add(tackle)

        gastly = MyPokemon(base_pokemon=base_ghost, level=50)
        gastly.save()

        result = DamageService.calculate(
            attacker=snorlax,
            move=tackle,
            defender=gastly,
            random_strategy=FixedRandomFactor(100),
        )
        assert result.damage == 0
        assert result.effectiveness == Decimal("0.0")

    def test_defensor_dual_tipo(self, db, fire_type, water_type):
        """
        Defensor de tipo dual: efectividad = producto de ambas efectividades.
        Fuego vs Agua/Fuego → ×0.5 × ×0.5 = ×0.25
        """
        rock_type = PokemonType.objects.create(name="rock")
        TypeEffectiveness.objects.create(
            attacking_type=fire_type,
            defending_type=water_type,
            multiplier=Decimal("0.5"),
        )
        TypeEffectiveness.objects.create(
            attacking_type=fire_type,
            defending_type=rock_type,
            multiplier=Decimal("0.5"),
        )

        base_dual = BasePokemon.objects.create(
            name="geodude-test",
            type_primary=water_type,
            type_secondary=rock_type,
            base_hp=40,
            base_attack=80,
            base_defense=100,
            base_sp_attack=30,
            base_sp_defense=30,
            base_speed=20,
        )
        base_fire = BasePokemon.objects.create(
            name="magmar-test",
            type_primary=fire_type,
            base_hp=65,
            base_attack=95,
            base_defense=57,
            base_sp_attack=100,
            base_sp_defense=85,
            base_speed=93,
        )
        flamethrower = Move.objects.create(
            name="flamethrower-test",
            move_type=fire_type,
            power=90,
        )
        base_fire.learnable_moves.add(flamethrower)

        atacante = MyPokemon(base_pokemon=base_fire, level=50)
        atacante.save()
        atacante.moves.add(flamethrower)

        defensor = MyPokemon(base_pokemon=base_dual, level=50)
        defensor.save()

        result = DamageService.calculate(
            attacker=atacante,
            move=flamethrower,
            defender=defensor,
            random_strategy=FixedRandomFactor(100),
        )
        assert result.effectiveness == Decimal("0.25")
        esperado = calcular_daño_esperado(
            nivel=atacante.level,
            ataque=atacante.attack,
            poder=flamethrower.power,
            defensa=defensor.defense,
            efectividad=0.25,
            random_factor=100,
        )
        assert result.damage == esperado

    def test_factor_aleatorio_inyectable(
        self, charmander, squirtle, ember, fire_vs_water
    ):
        """
        El Strategy Pattern permite inyectar el factor aleatorio.
        random=85 y random=100 deben producir daños distintos.
        """
        result_85 = DamageService.calculate(
            attacker=charmander,
            move=ember,
            defender=squirtle,
            random_strategy=FixedRandomFactor(85),
        )
        result_100 = DamageService.calculate(
            attacker=charmander,
            move=ember,
            defender=squirtle,
            random_strategy=FixedRandomFactor(100),
        )
        assert result_85.random_factor == 85
        assert result_100.random_factor == 100
        assert result_85.damage < result_100.damage

    def test_daño_minimo_es_cero(self, db, fire_type, water_type):
        """
        Nivel 1 con stats muy desfavorables: el daño puede ser 0 pero nunca negativo.
        """
        TypeEffectiveness.objects.create(
            attacking_type=fire_type,
            defending_type=water_type,
            multiplier=Decimal("1.0"),
        )
        base_debil = BasePokemon.objects.create(
            name="magikarp-test",
            type_primary=fire_type,
            base_hp=20,
            base_attack=10,
            base_defense=55,
            base_sp_attack=15,
            base_sp_defense=20,
            base_speed=80,
        )
        base_fuerte = BasePokemon.objects.create(
            name="steelix-test",
            type_primary=water_type,
            base_hp=75,
            base_attack=85,
            base_defense=200,
            base_sp_attack=55,
            base_sp_defense=65,
            base_speed=30,
        )
        splash = Move.objects.create(
            name="splash-test",
            move_type=fire_type,
            power=1,
        )
        base_debil.learnable_moves.add(splash)

        debil = MyPokemon(base_pokemon=base_debil, level=1)
        debil.save()
        debil.moves.add(splash)

        fuerte = MyPokemon(base_pokemon=base_fuerte, level=100)
        fuerte.save()

        result = DamageService.calculate(
            attacker=debil,
            move=splash,
            defender=fuerte,
            random_strategy=FixedRandomFactor(85),
        )
        assert result.damage >= 0
