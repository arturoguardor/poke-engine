from django.contrib import admin

from pokedex.models import BasePokemon, Move, MyPokemon, PokemonType, TypeEffectiveness


@admin.register(PokemonType)
class PokemonTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(TypeEffectiveness)
class TypeEffectivenessAdmin(admin.ModelAdmin):
    list_display = ["attacking_type", "defending_type", "multiplier"]
    list_filter = ["multiplier"]


@admin.register(BasePokemon)
class BasePokemonAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "pokeapi_id",
        "name",
        "type_primary",
        "type_secondary",
        "base_hp",
        "base_attack",
        "base_defense",
    ]
    search_fields = ["name"]
    list_filter = ["type_primary", "type_secondary"]


@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ["id", "pokeapi_id", "name", "move_type", "power"]
    search_fields = ["name"]
    list_filter = ["move_type"]
    filter_horizontal = ["learnable_by"]


@admin.register(MyPokemon)
class MyPokemonAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "base_pokemon",
        "nickname",
        "level",
        "hp_current",
        "hp_max",
        "attack",
        "defense",
        "speed",
    ]
    search_fields = ["base_pokemon__name", "nickname"]
    list_filter = ["base_pokemon__type_primary"]
    filter_horizontal = ["moves"]
    readonly_fields = [
        "hp_max",
        "hp_current",
        "attack",
        "defense",
        "sp_attack",
        "sp_defense",
        "speed",
        "created_at",
    ]
