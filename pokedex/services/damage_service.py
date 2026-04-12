import math
import random as stdlib_random
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol

from pokedex.models import TypeEffectiveness

if TYPE_CHECKING:
    from pokedex.models import Move, MyPokemon


# --- Strategy Pattern ---


class RandomFactorStrategy(Protocol):
    """
    Interfaz para la estrategia de generación del factor aleatorio.
    Usa Protocol (duck typing estructural) — no requiere herencia explícita.
    Separa 'cómo se genera el azar' de 'cómo se calcula el daño'.
    """

    def get_factor(self) -> int: ...


class DefaultRandomFactor:
    """Estrategia de producción: entero aleatorio entre 85 y 100."""

    def get_factor(self) -> int:
        return stdlib_random.randint(85, 100)


class FixedRandomFactor:
    """Estrategia de testing: factor fijo y determinista. Evita mockear stdlib_random."""

    def __init__(self, value: int):
        self.value = value

    def get_factor(self) -> int:
        return self.value


# --- Value Object ---


@dataclass(frozen=True)
class DamageResult:
    """
    Value Object inmutable que encapsula el resultado del cálculo de daño.
    frozen=True: dos resultados con los mismos valores son equivalentes (sin identidad propia).
    """

    damage: int
    effectiveness: Decimal
    random_factor: int


# --- Service Layer ---


class DamageService:
    """
    Servicio de cálculo de daño. Sin efectos secundarios — no modifica la BD.
    Recibe objetos de dominio y retorna un Value Object (DamageResult).
    """

    @staticmethod
    def get_effectiveness(
        attacking_type_id: int, defending_type_ids: list[int]
    ) -> Decimal:
        """
        Multiplicador compuesto para todos los tipos del defensor.
        Pokémon dual-tipo: efectividad = producto de ambas efectividades.
        Ejemplo: fuego vs agua+roca → 0.5 × 2.0 = 1.0.
        Una sola consulta con IN — minimiza viajes a BD.
        """
        matchups = TypeEffectiveness.objects.filter(
            attacking_type_id=attacking_type_id,
            defending_type_id__in=defending_type_ids,
        ).values_list("multiplier", flat=True)

        result = Decimal("1.0")
        for m in matchups:
            result *= m
        return result

    @staticmethod
    def calculate(
        attacker: "MyPokemon",
        move: "Move",
        defender: "MyPokemon",
        random_strategy: RandomFactorStrategy | None = None,
    ) -> DamageResult:
        """
        Fórmula del enunciado:
          Daño = {[(2*Nivel/5+2) * AtaqueAtacante * PoderMovimiento / DefensaRival] / 50}
                 * Efectividad * Random/100

        Efectividad: multiplicador de tipo desde TypeEffectiveness (tabla del enunciado).
        Random: entero 85-100 generado por la estrategia inyectada.

        random_strategy=None → DefaultRandomFactor (producción).
        random_strategy=FixedRandomFactor(100) → tests deterministas sin mockear stdlib_random.

        Daño = 0 si effectiveness = 0.0 (inmunidad). Fiel al enunciado — sin mínimo forzado.
        """
        strategy = random_strategy or DefaultRandomFactor()
        random_factor = strategy.get_factor()

        defending_type_ids = [defender.base_pokemon.type_primary_id]
        if defender.base_pokemon.type_secondary_id:
            defending_type_ids.append(defender.base_pokemon.type_secondary_id)

        effectiveness = DamageService.get_effectiveness(
            move.move_type_id, defending_type_ids
        )

        raw = (
            (2 * attacker.level / 5 + 2)
            * attacker.attack
            * move.power
            / defender.defense
        ) / 50

        damage = math.floor(raw * float(effectiveness) * random_factor / 100)

        return DamageResult(
            damage=damage,
            effectiveness=effectiveness,
            random_factor=random_factor,
        )
