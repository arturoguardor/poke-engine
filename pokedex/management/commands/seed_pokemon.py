from django.core.management.base import BaseCommand

from pokedex.services.pokeapi_service import (
    fetch_and_save_base_pokemon,
    fetch_learnable_moves,
    save_moves_for_pokemon,
)

# 10 Pokémons clásicos con diversidad de tipos (cubre 10 de los 18 tipos)
POKEMON_IDS = [
    1,  # bulbasaur  — grass/poison
    4,  # charmander — fire
    7,  # squirtle   — water
    25,  # pikachu    — electric
    39,  # jigglypuff — normal/fairy
    54,  # psyduck    — water
    63,  # abra       — psychic
    94,  # gengar     — ghost/poison
    131,  # lapras     — water/ice
    133,  # eevee      — normal
]


class Command(BaseCommand):
    """
    Management command que carga 10 Pokémons reales desde PokéAPI.
    Command Pattern: operación de administración encapsulada como objeto invocable desde CLI.
    Uso: python manage.py seed_pokemon
    """

    help = "Carga 10 Pokémons reales desde PokéAPI con sus movimientos de level-up."

    def handle(self, *args, **options):
        creados = 0
        actualizados = 0

        for pokemon_id in POKEMON_IDS:
            self.stdout.write(f"Cargando Pokémon ID {pokemon_id}...", ending=" ")
            try:
                pokemon, created = fetch_and_save_base_pokemon(pokemon_id)
                moves_data = fetch_learnable_moves(pokemon.pokeapi_id, limit=4)
                save_moves_for_pokemon(pokemon, moves_data)

                if created:
                    creados += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ {pokemon.name} creado"))
                else:
                    actualizados += 1
                    self.stdout.write(
                        self.style.WARNING(f"↺ {pokemon.name} ya existía")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error al cargar ID {pokemon_id}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeding completado: {creados} creados, {actualizados} actualizados."
            )
        )
