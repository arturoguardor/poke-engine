from django.db import transaction
from rest_framework.exceptions import ValidationError

from battle.models import Battle, Turn
from pokedex.models import Move, MyPokemon
from pokedex.services.damage_service import DamageService


class BattleService:
    """
    Servicio de batalla. Orquesta la creación de partidas y la ejecución de turnos.
    Facade: execute_turn oculta 4 subsistemas (damage, HP, Turn creation, Battle state)
    tras una sola operación pública.
    """

    @staticmethod
    def create_battle(pokemon_1: MyPokemon, pokemon_2: MyPokemon) -> Battle:
        """
        Crea una batalla nueva entre dos MyPokemon.
        Precondiciones validadas:
          - No son el mismo objeto
          - Ninguno está debilitado (hp_current > 0)
          - Ambos tienen al menos 1 movimiento asignado
        """
        if pokemon_1.pk == pokemon_2.pk:
            raise ValidationError("Un Pokémon no puede batallar contra sí mismo.")
        if pokemon_1.is_fainted or pokemon_2.is_fainted:
            raise ValidationError(
                "No se puede iniciar una batalla con un Pokémon debilitado."
            )
        if not pokemon_1.moves.exists() or not pokemon_2.moves.exists():
            raise ValidationError("Ambos Pokémon deben tener al menos un movimiento.")
        return Battle.objects.create(pokemon_1=pokemon_1, pokemon_2=pokemon_2)

    @staticmethod
    @transaction.atomic
    def execute_turn(
        battle: Battle,
        attacker: MyPokemon,
        move: Move,
        random_strategy=None,
    ) -> tuple[Turn, str | None]:
        """
        Ejecuta un turno de batalla.
        Flujo:
          1. Validar precondiciones (estado, pertenencia, movimiento, debilitado)
          2. Determinar defensor (el que NO es el atacante)
          3. Calcular daño via DamageService.calculate()
          4. Guardar hp_before, aplicar daño (update_fields=['hp_current'])
          5. Crear registro Turn con todos los parámetros del cálculo
          6. Incrementar battle.current_turn
          7. Si defensor debilitado → FINISHED, winner=attacker
          8. Guardar battle

        @transaction.atomic garantiza que si algo falla, el HP no queda modificado.
        Retorna: (Turn, warning | None)
        """
        BattleService._validate_turn(battle, attacker, move)

        defender = (
            battle.pokemon_2 if attacker.pk == battle.pokemon_1_id else battle.pokemon_1
        )

        result = DamageService.calculate(attacker, move, defender, random_strategy)

        hp_before = defender.hp_current
        defender.hp_current = max(0, defender.hp_current - result.damage)
        defender.save(update_fields=["hp_current"])

        turn = Turn.objects.create(
            battle=battle,
            turn_number=battle.current_turn,
            attacker=attacker,
            defender=defender,
            move_used=move,
            damage_dealt=result.damage,
            effectiveness=result.effectiveness,
            random_factor=result.random_factor,
            defender_hp_before=hp_before,
            defender_hp_after=defender.hp_current,
        )

        battle.current_turn += 1
        if defender.is_fainted:
            battle.status = Battle.Status.FINISHED
            battle.winner = attacker
        battle.save(update_fields=["current_turn", "status", "winner_id"])

        # Advertencia de velocidad: informa sin rechazar el turno
        warning = None
        if attacker.speed < defender.speed:
            warning = (
                f"{defender} ({defender.speed} SPD) es más rápido que "
                f"{attacker} ({attacker.speed} SPD). "
                "En combate real, el defensor atacaría primero."
            )

        return turn, warning

    @staticmethod
    def _validate_turn(battle: Battle, attacker: MyPokemon, move: Move) -> None:
        """Valida las precondiciones del turno antes de ejecutarlo."""
        if battle.status == Battle.Status.FINISHED:
            raise ValidationError("La batalla ya ha terminado.")
        if attacker.pk not in (battle.pokemon_1_id, battle.pokemon_2_id):
            raise ValidationError("El atacante no pertenece a esta batalla.")
        if not attacker.moves.filter(pk=move.pk).exists():
            raise ValidationError("El movimiento no pertenece al atacante.")
        if attacker.is_fainted:
            raise ValidationError("El atacante está debilitado.")
