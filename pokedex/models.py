from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PokemonType(models.Model):
    """Tipo de Pokémon (fuego, agua, etc.). Nombres en inglés minúsculas — igual que PokéAPI."""

    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TypeEffectiveness(models.Model):
    """
    Tabla de efectividades de tipo: attacking_type vs defending_type → multiplier.
    Valores posibles: 0.0 (inmune), 0.5 (poco efectivo), 1.0 (neutro), 2.0 (superefectivo).
    Se usan DecimalField en lugar de FloatField para evitar imprecisión en comparaciones.
    Las 324 combinaciones (18×18) se cargan desde fixtures/type_effectiveness.json.
    """

    attacking_type = models.ForeignKey(
        PokemonType,
        on_delete=models.CASCADE,
        related_name="attacking_matchups",
    )
    defending_type = models.ForeignKey(
        PokemonType,
        on_delete=models.CASCADE,
        related_name="defending_matchups",
    )
    multiplier = models.DecimalField(max_digits=3, decimal_places=1)

    class Meta:
        unique_together = [("attacking_type", "defending_type")]

    def __str__(self):
        return f"{self.attacking_type} → {self.defending_type}: ×{self.multiplier}"


class BasePokemon(models.Model):
    """
    Especie base de Pokémon. Contiene stats base y tipos.
    No es una instancia concreta — para eso existe MyPokemon.
    """

    pokeapi_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    type_primary = models.ForeignKey(
        PokemonType,
        on_delete=models.PROTECT,
        related_name="primary_pokemon",
    )
    type_secondary = models.ForeignKey(
        PokemonType,
        on_delete=models.PROTECT,
        related_name="secondary_pokemon",
        null=True,
        blank=True,
    )
    # Stats base directamente de PokéAPI (sin nivel aplicado)
    base_hp = models.PositiveSmallIntegerField()
    base_attack = models.PositiveSmallIntegerField()
    base_defense = models.PositiveSmallIntegerField()
    base_sp_attack = models.PositiveSmallIntegerField()
    base_sp_defense = models.PositiveSmallIntegerField()
    base_speed = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["pokeapi_id", "name"]

    def __str__(self):
        return self.name


class Move(models.Model):
    """
    Movimiento de Pokémon.
    learnable_by: M2M hacia BasePokemon — controla qué especies pueden aprender el movimiento.
    Los movimientos no están restringidos por tipo (Charizard puede aprender Terremoto).
    """

    pokeapi_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    move_type = models.ForeignKey(
        PokemonType,
        on_delete=models.PROTECT,
        related_name="moves",
    )
    power = models.PositiveSmallIntegerField()
    learnable_by = models.ManyToManyField(
        BasePokemon,
        related_name="learnable_moves",
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.move_type})"


class MyPokemon(models.Model):
    """
    Instancia única e irrepetible de un Pokémon.
    La misma especie puede tener múltiples instancias con nivel, stats y movimientos distintos.
    Las stats se calculan y persisten en BD para mantener el estado de batalla entre requests.
    """

    base_pokemon = models.ForeignKey(
        BasePokemon,
        on_delete=models.PROTECT,
        related_name="instances",
    )
    nickname = models.CharField(max_length=100, blank=True)
    level = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    moves = models.ManyToManyField(Move, related_name="pokemon_instances", blank=True)

    # Stats calculadas y persistidas — editable=False evita modificación manual desde el Admin
    hp_max = models.PositiveSmallIntegerField(editable=False)
    hp_current = models.PositiveSmallIntegerField(editable=False)
    attack = models.PositiveSmallIntegerField(editable=False)
    defense = models.PositiveSmallIntegerField(editable=False)
    sp_attack = models.PositiveSmallIntegerField(editable=False)
    sp_defense = models.PositiveSmallIntegerField(editable=False)
    speed = models.PositiveSmallIntegerField(editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        nombre = self.nickname or self.base_pokemon.name
        return f"{nombre} (Lv.{self.level})"

    def calculate_stats(self):
        """
        Fórmula Gen I simplificada (sin IVs ni EVs — no especificados en el enunciado):
          hp   = floor(2 * base_hp * level / 100) + level + 10
          stat = floor(2 * base_stat * level / 100) + 5

        Asigna los valores a self pero NO llama save().
        El método save() se encarga de llamar a calculate_stats() cuando corresponde.
        """
        bp = self.base_pokemon
        self.hp_max = (2 * bp.base_hp * self.level) // 100 + self.level + 10
        self.hp_current = self.hp_max
        self.attack = (2 * bp.base_attack * self.level) // 100 + 5
        self.defense = (2 * bp.base_defense * self.level) // 100 + 5
        self.sp_attack = (2 * bp.base_sp_attack * self.level) // 100 + 5
        self.sp_defense = (2 * bp.base_sp_defense * self.level) // 100 + 5
        self.speed = (2 * bp.base_speed * self.level) // 100 + 5

    def save(self, *args, **kwargs):
        # Template Method: Django define el esqueleto de save(); aquí se añade el paso previo.
        # Solo recalcula stats en la creación o si cambió el nivel.
        if not self.pk or self._level_changed():
            self.calculate_stats()
        super().save(*args, **kwargs)

    def _level_changed(self) -> bool:
        """Comprueba si el nivel cambió respecto al valor persistido en BD."""
        nivel_actual = (
            MyPokemon.objects.filter(pk=self.pk).values_list("level", flat=True).first()
        )
        return nivel_actual != self.level

    @property
    def is_fainted(self) -> bool:
        """True si el Pokémon está debilitado (HP = 0)."""
        return self.hp_current <= 0
