# Backlog de mejoras — poke-engine

Lista priorizada de mejoras detectadas en el análisis del proyecto (2026-08-11).
Cada fila contiene la información mínima para convertirla en una SPEC.

## Prioridad 1 — Seguridad y robustez

| ID       | Título                                                                     | Hallazgo                                                                                                                                   | Archivos afectados                                     | Esfuerzo | Criterios de aceptación esperados                                                                                      |
| -------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| SEC-001  | Hardening de settings: `DEBUG=False` y `ALLOWED_HOSTS` seguros por defecto | ✅ **Resuelto** — defaults seguros implementados y verificados (commit pendiente)                                                          | `config/settings.py`, `.env.example`                   | S        | ✅ `DEBUG` default `False`; `ALLOWED_HOSTS` solo `localhost,127.0.0.1`; activables explícitamente por `.env`           |
| TEST-001 | Suite de tests para `BattleService`                                        | Cero tests en `battle/`. `create_battle()` (3 validaciones + happy path) y `execute_turn()` (validaciones, HP, Turn, estado) sin cobertura | `tests/battle/`, `battle/services/battle_service.py`   | L        | 100% de ramas de `BattleService` cubiertas; tests deterministas (random inyectable)                                    |
| TEST-002 | Tests de integración HTTP (APIClient) para todos los endpoints             | No hay tests que ejerciten los endpoints vía `APIClient`. Regresiones en routing/serializers sin detectar                                  | `tests/pokedex/`, `tests/battle/`, `tests/conftest.py` | L        | Conjunto de fixtures de sesión + test por cada endpoint documentado en README (25+ endpoints)                          |
| DATA-001 | Constraints de integridad en modelo `Battle`                               | `pokemon_1 == pokemon_2` y `winner` arbitrario solo validados en servicio, no en modelo (admin/shell los omiten)                           | `battle/models.py`, migración nueva                    | S        | `CheckConstraint` impide `pokemon_1 == pokemon_2`; `winner` restringido a participantes (FK + validación en `clean()`) |

## Prioridad 2 — Rendimiento

| ID       | Título                                               | Hallazgo                                                                                                                | Archivos afectados                                          | Esfuerzo | Criterios de aceptación esperados                                                     |
| -------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------- |
| PERF-001 | Optimización de queries en serializers de batalla    | `BattleSerializer` y `TurnSerializer` sin `select_related`/`prefetch_related`; N+1 queries por turno en batallas largas | `battle/serializers.py`, `battle/views.py`, `tests/battle/` | M        | Query count por batalla con N turnos fijo (assertNumQueries); sin N+1                 |
| PERF-002 | Eliminar re-consulta en `MyPokemon._level_changed()` | `save()` hace `filter(pk=self.pk).values_list()` extra en cada escritura (lectura innecesaria por write)                | `pokedex/models.py`, `tests/pokedex/`                       | S        | `save()` con un solo UPDATE (assertNumQueries); misma semántica de recálculo de stats |

## Prioridad 3 — Configuración y operación

| ID       | Título                                                        | Hallazgo                                                                                                             | Archivos afectados                                                           | Esfuerzo | Criterios de aceptación esperados                                                                              |
| -------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| CONF-001 | Configurar `devtools.yaml` con comandos reales                | ✅ **Resuelto** (commit `bf82924`) — `testing.command`, `testing.path`, `quality.lint_command` declarados            | `devtools.yaml`                                                              | S        | ✅ `preflight.py -d .` sale con código 0                                                                       |
| CONF-002 | Split de settings (base/dev/prod) + `STATIC_ROOT` + `LOGGING` | Un solo `settings.py` sin separación por entorno; sin `STATIC_ROOT` (roto `collectstatic`); sin logging estructurado | `config/settings/` (nuevo), `config/settings.py` → `config/settings/base.py` | M        | `manage.py check --settings=config.settings.prod` pasa; `collectstatic` funciona; logs a stdout en JSON/simple |
| AUTH-001 | Autenticación JWT y permisos por endpoint                     | Todos los endpoints `AllowAny`. Sin protección ante uso no autenticado ni trazabilidad de quién crea qué             | `config/settings.py`, `views.py` de ambas apps, `requirements.txt`           | L        | Endpoints de escritura requieren token; lectura opcional; login/refresh endpoints; tests de 401/403            |

## Prioridad 4 — CSV de integridad y calidad de datos (baja)

| ID       | Título                                        | Hallazgo                                                                                                                                      | Archivos afectados                                   | Esfuerzo | Criterios de aceptación esperados                                                                     |
| -------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------- |
| DATA-002 | Validadores de integridad en modelos          | `hp_current` acepta 0 sin advertencia (semántica: 0 = debilitado); `Move.accuracy` permite >100; `BasePokemon.type_2` puede duplicar `type_1` | `pokedex/models.py`, `battle/models.py`, migraciones | S        | Tests de validación para los 3 casos; endpoints rechazan payloads inválidos con 400                   |
| TEST-003 | Ampliar edge cases en `DamageService`         | Faltan tests: stats en 0, nivel >100, tipo dual idéntico, efectividad con 3+ tipos, movimiento sin tipo                                       | `tests/pokedex/test_damage_service.py`               | M        | Nuevos casos parametrizados; suite verde                                                              |
| TEST-004 | Fixtures de `conftest.py` con scope `session` | Cada test recrea 11 objetos (function scope) — escala mal a medida que crece la suite                                                         | `tests/conftest.py`, tests que dependen de mutación  | S        | Suite completa corre con fixtures de sesión; tests que mutan estados usan clones o `transactional_db` |

## Prioridad 5 — DevOps

| ID         | Título                                   | Hallazgo                                                                                             | Archivos afectados                                                      | Esfuerzo | Criterios de aceptación esperados                                                             |
| ---------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------- |
| DOCKER-001 | Imagen Docker production-ready           | La imagen actual usa `runserver`, `DEBUG=True`, sin `collectstatic`; solo apta para desarrollo local | `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `config/settings/` | M        | Imagen multi-stage; gunicorn; `DEBUG=False`; `collectstatic` en build; healthcheck            |
| CI-001     | GitHub Actions: lint + pytest en push/PR | Sin CI. Regresiones de lint/tests se detectan solo localmente                                        | `.github/workflows/ci.yml` (nuevo)                                      | M        | Workflow corre `black --check`, `flake8`, `isort --check-only`, `pytest` y falla si algo roza |

## Prioridad 6 — Features del juego (baja)

| ID       | Título                                                              | Hallazgo                                                                                                                                                   | Archivos afectados                                                                         | Esfuerzo | Criterios de aceptación esperados                                                                                           |
| -------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------- |
| FEAT-001 | STAB bonus (×1.5 mismo tipo)                                        | Mecánica oficial del juego no implementada: si el tipo del movimiento coincide con tipo del atacante, daño ×1.5                                            | `pokedex/services/damage_service.py`, `tests/pokedex/`                                     | S        | Daño con STAB = base ×1.5; sin STAB = base; tests de ambos casos                                                            |
| FEAT-002 | Golpes críticos (1/16, ×1.5) + random inyectable en `BattleService` | `DamageService` usa Strategy Pattern para el factor aleatorio, pero `BattleService.execute_turn()` llama `random.randint` directo → tests no deterministas | `battle/services/battle_service.py`, `pokedex/services/damage_service.py`, `tests/battle/` | M        | Critical hit 1/16 ×1.5; `BattleService` acepta inyección de random; tests deterministas                                     |
| FEAT-003 | Turno automático por velocidad                                      | Ambos Pokémon atacan en un solo request, ordenados por `speed`; más fiel a la mecánica del juego                                                           | `battle/services/battle_service.py`, `battle/views.py`, `battle/serializers.py`            | M        | Nuevo endpoint/parámetro resuelve ambos ataques; orden correcto según stat de velocidad; batalla termina al 0 HP tras ambos |

## Independientes (en cualquier momento)

| ID      | Título                                  | Hallazgo                                                                                       | Archivos afectados                        | Esfuerzo | Criterios de aceptación esperados                                                      |
| ------- | --------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------- | -------- | -------------------------------------------------------------------------------------- |
| DX-001  | Health check endpoint + `.editorconfig` | Sin `GET /health/` para Docker/load balancers; sin `.editorconfig` para convenciones de editor | `config/urls.py`, `.editorconfig` (nuevo) | S        | `/health/` responde 200 con estado de la app; `.editorconfig` alineado con black/isort |
| DOC-001 | Actualizar `plans/INDEX.md`             | Decía "(ningún plan activo)" pero `DOCKERIZE` existe en `active/`                              | `plans/INDEX.md`                          | S        | Índice refleja tickets activos y backlog — ✅ ya resuelto en el commit de limpieza     |

## Orden de ejecución recomendado

```
SEC-001 → CONF-001 → CONF-002
                      ↓
TEST-001 → TEST-002 → TEST-003 → TEST-004
                      ↓
DATA-001 → DATA-002
                      ↓
PERF-001 → PERF-002
                      ↓
AUTH-001
                      ↓
DOCKER-001 → CI-001
                      ↓
FEAT-001 → FEAT-002 → FEAT-003
                      ↓
DX-001 + DOC-001 (independientes, en cualquier momento)
```
