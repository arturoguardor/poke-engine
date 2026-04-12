import requests

from pokedex.models import BasePokemon, Move, PokemonType

POKEAPI_BASE = "https://pokeapi.co/api/v2"


def fetch_and_save_base_pokemon(name_or_id: str | int) -> tuple[BasePokemon, bool]:
    """
    Consulta PokéAPI /pokemon/{name_or_id}/ y persiste un BasePokemon.
    Retorna (instancia, created) — mismo patrón que get_or_create.

    Mapeo de campos PokéAPI → BasePokemon:
      response["id"]                          → pokeapi_id
      response["name"]                        → name
      response["types"][n]["type"]["name"]    → type_primary / type_secondary
      stats iterados por stat["stat"]["name"] → base_hp, base_attack, base_defense,
                                                base_sp_attack, base_sp_defense, base_speed

    Los PokemonType se crean via get_or_create si no existen aún en BD.
    """
    response = requests.get(f"{POKEAPI_BASE}/pokemon/{name_or_id}/", timeout=10)
    response.raise_for_status()
    data = response.json()

    types = data["types"]
    primary_name = types[0]["type"]["name"]
    secondary_name = types[1]["type"]["name"] if len(types) > 1 else None

    type_primary, _ = PokemonType.objects.get_or_create(name=primary_name)
    type_secondary = None
    if secondary_name:
        type_secondary, _ = PokemonType.objects.get_or_create(name=secondary_name)

    stat_map = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

    pokemon, created = BasePokemon.objects.get_or_create(
        pokeapi_id=data["id"],
        defaults={
            "name": data["name"],
            "type_primary": type_primary,
            "type_secondary": type_secondary,
            "base_hp": stat_map["hp"],
            "base_attack": stat_map["attack"],
            "base_defense": stat_map["defense"],
            "base_sp_attack": stat_map["special-attack"],
            "base_sp_defense": stat_map["special-defense"],
            "base_speed": stat_map["speed"],
        },
    )
    return pokemon, created


def fetch_learnable_moves(pokeapi_id: int, limit: int = 4) -> list[dict]:
    """
    Extrae los primeros `limit` movimientos de level-up con power > 0 para un Pokémon.
    Para cada movimiento consulta /move/{url}/ para obtener tipo y poder.
    Retorna lista de dicts: {"pokeapi_id": int, "name": str, "type": str, "power": int}
    """
    response = requests.get(f"{POKEAPI_BASE}/pokemon/{pokeapi_id}/", timeout=10)
    response.raise_for_status()
    data = response.json()

    level_up_moves = [
        m
        for m in data["moves"]
        if any(
            vg["move_learn_method"]["name"] == "level-up"
            for vg in m["version_group_details"]
        )
    ]

    result = []
    for move_entry in level_up_moves:
        if len(result) >= limit:
            break
        move_url = move_entry["move"]["url"]
        move_resp = requests.get(move_url, timeout=10)
        move_resp.raise_for_status()
        move_data = move_resp.json()
        if move_data.get("power") is None:
            continue  # ignorar movimientos de estado (sin poder)
        result.append(
            {
                "pokeapi_id": move_data["id"],
                "name": move_data["name"],
                "type": move_data["type"]["name"],
                "power": move_data["power"],
            }
        )
    return result


def save_moves_for_pokemon(pokemon: BasePokemon, moves_data: list[dict]) -> None:
    """
    Persiste los movimientos y los asocia al BasePokemon via learnable_by.
    Usa get_or_create para que el mismo movimiento no se duplique si lo aprenden varios Pokémon.
    """
    for move_dict in moves_data:
        move_type, _ = PokemonType.objects.get_or_create(name=move_dict["type"])
        move, _ = Move.objects.get_or_create(
            pokeapi_id=move_dict["pokeapi_id"],
            defaults={
                "name": move_dict["name"],
                "move_type": move_type,
                "power": move_dict["power"],
            },
        )
        pokemon.learnable_moves.add(move)
