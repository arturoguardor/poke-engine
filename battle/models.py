from django.db import models


class Battle(models.Model):
    """
    Partida de batalla entre dos MyPokemon.
    Es inmutable una vez creada: no admite PUT/PATCH/DELETE.
    Solo avanza mediante el endpoint /turn/.
    El estado pasa de ONGOING a FINISHED cuando uno de los Pokémon llega a 0 PS.
    """

    class Status(models.TextChoices):
        ONGOING = "ongoing", "En curso"
        FINISHED = "finished", "Terminada"

    pokemon_1 = models.ForeignKey(
        "pokedex.MyPokemon",
        on_delete=models.PROTECT,
        related_name="battles_as_p1",
    )
    pokemon_2 = models.ForeignKey(
        "pokedex.MyPokemon",
        on_delete=models.PROTECT,
        related_name="battles_as_p2",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ONGOING,
    )
    winner = models.ForeignKey(
        "pokedex.MyPokemon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="battles_won",
    )
    current_turn = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Batalla {self.pk}: {self.pokemon_1} vs {self.pokemon_2} [{self.status}]"
        )


class Turn(models.Model):
    """
    Registro de un turno dentro de una batalla.
    Guarda todos los parámetros del cálculo para trazabilidad completa.
    La batalla puede reconstruirse íntegramente desde el historial de turnos.
    """

    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name="turns")
    turn_number = models.PositiveSmallIntegerField()
    attacker = models.ForeignKey(
        "pokedex.MyPokemon",
        on_delete=models.PROTECT,
        related_name="turns_as_attacker",
    )
    defender = models.ForeignKey(
        "pokedex.MyPokemon",
        on_delete=models.PROTECT,
        related_name="turns_as_defender",
    )
    move_used = models.ForeignKey("pokedex.Move", on_delete=models.PROTECT)
    damage_dealt = models.PositiveSmallIntegerField()
    effectiveness = models.DecimalField(max_digits=3, decimal_places=1)
    random_factor = models.PositiveSmallIntegerField()  # 85–100
    defender_hp_before = models.PositiveSmallIntegerField()
    defender_hp_after = models.SmallIntegerField()  # puede ser 0 al finalizar

    class Meta:
        unique_together = [("battle", "turn_number")]
        ordering = ["battle", "turn_number"]

    def __str__(self):
        return f"Turno {self.turn_number} — {self.attacker} usa {self.move_used}"
