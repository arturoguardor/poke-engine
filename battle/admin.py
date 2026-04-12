from django.contrib import admin

from battle.models import Battle, Turn


class TurnInline(admin.TabularInline):
    model = Turn
    extra = 0
    readonly_fields = [
        "turn_number",
        "attacker",
        "defender",
        "move_used",
        "damage_dealt",
        "effectiveness",
        "random_factor",
        "defender_hp_before",
        "defender_hp_after",
    ]
    can_delete = False


@admin.register(Battle)
class BattleAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "pokemon_1",
        "pokemon_2",
        "status",
        "winner",
        "current_turn",
        "created_at",
    ]
    list_filter = ["status"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [TurnInline]
