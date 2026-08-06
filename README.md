# poke-engine

API REST para gestión de Pokémons y sistema de combate por turnos.

El proyecto implementa las tres partes del enunciado en un único servicio Django REST Framework,
con mejoras documentadas sobre el spec original.

**Parte 1 — Cálculo de daño:** Endpoint `POST /api/v1/damage/calculate/` que aplica la fórmula
del enunciado: `{[(2*Nivel/5+2) * Ataque * Poder / Defensa] / 50} * Efectividad * Random/100`.
La efectividad se obtiene de una tabla de tipos en base de datos (18 tipos, 324 combinaciones),
incluyendo multiplicadores para Pokémon de tipo dual.

**Parte 2 — API Pokédex:** CRUD completo de `BasePokemon`, `Move` y `MyPokemon` con validación
de movimientos aprendibles (máx. 4 por Pokémon). Consultas relacionales: movimientos del mismo
tipo que un Pokémon, movimientos que una especie puede aprender, Pokémon que aprenden un movimiento
concreto. Integración con PokéAPI para importar datos reales.

**Parte 3 — Sistema de batalla:** Gestión de estado `ONGOING → FINISHED`. Cada turno recibe
`attacker_id` y `move_id`, calcula el daño, decrementa el HP del defensor y registra el historial
completo en la tabla `Turn`. La batalla termina cuando un Pokémon llega a 0 PS.

## Stack

| Componente | Tecnología | Versión |
|---|---|---|
| Runtime | Python | 3.12.10 |
| Framework | Django | 5.1.7 |
| REST API | Django REST Framework | 3.15.2 |
| Documentación API | drf-spectacular (Swagger UI) | 0.28.0 |
| Configuración | python-decouple | 3.8 |
| HTTP client | requests | 2.32.3 |
| Base de datos | SQLite 3 | built-in |
| Tests | pytest + pytest-django + pytest-cov | 8.3.5 / 4.9.0 / 6.0.0 |
| Linting | black + flake8 + isort | 24.10.0 / 7.1.1 / 5.13.2 |

Fuente de datos: [PokéAPI](https://pokeapi.co) — seeding de 10 Pokémons reales con sus movimientos.

## Instalación

### Opción A: entorno virtual (venv)

```bash
git clone https://github.com/arturoguardor/poke-engine.git
cd poke-engine

# Entorno virtual con Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# source .venv/Scripts/activate  # Windows Git Bash

pip install -r requirements-dev.txt
cp .env.example .env

python manage.py migrate
python manage.py loaddata fixtures/type_effectiveness.json

# Carga 10 Pokémons desde PokéAPI (requiere conexión a internet)
python manage.py seed_pokemon
```

```bash
python manage.py runserver
```

### Opción B: Docker

Alternativa que no requiere tener Python 3.12 instalado localmente.

```bash
git clone https://github.com/arturoguardor/poke-engine.git
cd poke-engine

docker compose up --build
```

- Al arrancar, el contenedor aplica `migrate` y carga `fixtures/type_effectiveness.json`
  automáticamente (`entrypoint.sh`) — no requiere pasos manuales adicionales.
- El código fuente se monta como bind mount (`.:/app`): los cambios se reflejan sin reconstruir
  la imagen.
- `SECRET_KEY`, `DEBUG` y `ALLOWED_HOSTS` toman los mismos defaults que `config/settings.py`
  (ver `.env.example`); si querés sobreescribirlos, creá un `.env` en la raíz del proyecto,
  Docker Compose lo carga automáticamente.
- Para cargar los 10 Pokémons reales desde PokéAPI (requiere conexión a internet), ejecutar
  manualmente en un segundo terminal:

  ```bash
  docker compose exec web python manage.py seed_pokemon
  ```

- Esta imagen está pensada **solo para desarrollo local**: usa `manage.py runserver`, no un
  servidor WSGI de producción como gunicorn, y `DEBUG=True` por defecto.

## Uso

- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **Admin**: http://127.0.0.1:8000/admin/
- **OpenAPI schema**: http://127.0.0.1:8000/api/schema/

## Endpoints

### Pokédex

| Método | URL | Descripción |
|--------|-----|-------------|
| GET POST | `/api/v1/pokemon/` | Listar / crear BasePokemon |
| POST | `/api/v1/pokemon/fetch/` | Importar BasePokemon desde PokéAPI |
| GET PUT PATCH DELETE | `/api/v1/pokemon/{id}/` | Detalle / editar / eliminar |
| GET | `/api/v1/pokemon/{id}/moves/` | Movimientos del mismo tipo que el Pokémon |
| GET | `/api/v1/pokemon/{id}/possible-moves/` | Movimientos que el Pokémon puede aprender |
| GET POST | `/api/v1/moves/` | Listar / crear movimientos |
| GET PUT PATCH DELETE | `/api/v1/moves/{id}/` | Detalle / editar / eliminar |
| GET | `/api/v1/moves/{id}/pokemon/` | Pokémon que pueden aprender el movimiento |
| GET POST | `/api/v1/my-pokemon/` | Listar / crear instancias de Pokémon |
| POST | `/api/v1/my-pokemon/catch/` | Atrapar un Pokémon (crear instancia) |
| GET PUT PATCH DELETE | `/api/v1/my-pokemon/{id}/` | Detalle / editar / eliminar |
| POST | `/api/v1/my-pokemon/{id}/heal/` | Restaurar HP al máximo |
| GET | `/api/v1/types/` | Listar tipos (solo lectura) |
| POST | `/api/v1/damage/calculate/` | Calcular daño sin persistir nada |

### Batalla

| Método | URL | Descripción |
|--------|-----|-------------|
| GET POST | `/api/v1/battles/` | Listar / crear batallas |
| GET | `/api/v1/battles/{id}/` | Estado completo + historial de turnos |
| POST | `/api/v1/battles/{id}/turn/` | Ejecutar un turno |

### Flujo completo de ejemplo

```bash
# 1. Calcular daño (Parte 1 — sin persistir nada)
curl -X POST http://127.0.0.1:8000/api/v1/damage/calculate/ \
  -H "Content-Type: application/json" \
  -d '{"attacker_id": 1, "move_id": 1, "defender_id": 2}'

# 2. Atrapar un Pokémon
curl -X POST http://127.0.0.1:8000/api/v1/my-pokemon/catch/ \
  -H "Content-Type: application/json" \
  -d '{"base_pokemon_id": 1, "level": 50, "move_ids": [1, 2]}'

# 3. Crear batalla (Parte 3)
curl -X POST http://127.0.0.1:8000/api/v1/battles/ \
  -H "Content-Type: application/json" \
  -d '{"pokemon_1_id": 1, "pokemon_2_id": 2}'

# 4. Ejecutar turno
curl -X POST http://127.0.0.1:8000/api/v1/battles/1/turn/ \
  -H "Content-Type: application/json" \
  -d '{"attacker_id": 1, "move_id": 1}'

# 5. Ver estado de la batalla + historial
curl http://127.0.0.1:8000/api/v1/battles/1/
```

## Tests

```bash
pytest --cov=pokedex --cov=battle --cov-report=term-missing -v
```

Los tests unitarios validan la fórmula de daño con 7 casos: efectividad neutra, superefectivo
(×2), poco efectivo (×0.5), inmunidad (×0 = 0 daño, sin `max(1, damage)`), Pokémon dual-tipo
(efectividad como producto), factor aleatorio inyectable (Strategy Pattern) y daño mínimo ≥ 0.

```bash
# Linting
black --check .
flake8 .
isort --check-only .
```

## Decisiones técnicas destacadas

### Tabla de tipos en base de datos

Las 324 combinaciones de efectividad de tipo (18×18) se almacenan en la tabla `TypeEffectiveness`
y se cargan desde `fixtures/type_effectiveness.json`. Esto permite modificar efectividades sin
desplegar código y mantiene el `DamageService` sin lógica condicional.

El término `Efectividad` de la fórmula es el multiplicador de tipo (`TypeEffectiveness.multiplier`):
0.0 (inmune), 0.5 (poco efectivo), 1.0 (neutro), 2.0 (superefectivo). Para Pokémon dual-tipo, la
efectividad final es el producto de ambos multiplicadores.

### Arquitectura en capas

```
View (HTTP) → Service (lógica de negocio) → Model (persistencia) → SQLite
```

`DamageService` y `BattleService` son independientes de HTTP. Los tests unitarios los invocan
directamente, sin cliente HTTP ni fixtures de red.

### Patrones de diseño

- **Strategy** con `Protocol` en `DamageService`: separa la generación del factor aleatorio del
  cálculo del daño, permitiendo tests deterministas con `FixedRandomFactor(100)`.
- **Value Object** `DamageResult (@dataclass frozen=True)`: encapsula el resultado del cálculo de
  daño de forma inmutable y con igualdad por valor.
- **Facade** `BattleService.execute_turn`: oculta cuatro operaciones de base de datos (daño, HP,
  registro `Turn`, estado de `Battle`) tras una sola llamada pública.
- **Adapter** `pokeapi_service`: aísla el acoplamiento a la API externa en un único módulo.
- **Unit of Work** (`@transaction.atomic`): la modificación de HP, la creación del `Turn` y la
  actualización del estado de `Battle` son atómicas.
- **Template Method** `MyPokemon.save()`: añade `calculate_stats()` al ciclo de guardado de Django.
- **State** `Battle.Status`: el estado `FINISHED` bloquea activamente nuevos turnos en el guard de
  `_validate_turn`.

### Stats persistidas en base de datos

`hp_current` debe persistirse obligatoriamente para mantener el estado de batalla entre requests.
Dado eso, se persisten todas las stats para consistencia. Se calculan automáticamente en `save()`
usando la fórmula Gen I simplificada (sin IVs/EVs, no especificados en el enunciado):
`stat = (2 * base_stat * level) // 100 + 5`.

### MyPokemon como instancia única e irrepetible

Cada `MyPokemon` es independiente. La misma especie puede tener múltiples instancias con nivel,
stats y movimientos distintos, lo que permite demostraciones más ricas y es fiel al juego original.

## Mejoras implementadas sobre el enunciado

Las siguientes decisiones van más allá del spec original con justificación técnica:

| Mejora | Justificación |
|--------|---------------|
| `TypeEffectiveness` en BD | Extensible sin despliegue de código |
| Seeding desde PokéAPI | 10 Pokémons reales, diversidad de tipos, listo para demostrar |
| `MyPokemon` como instancia irrepetible | Fiel al juego; permite múltiples instancias por especie |
| `POST /api/v1/pokemon/fetch/` | Importar cualquier Pokémon por nombre/ID en tiempo real |
| `POST /api/v1/my-pokemon/catch/` | Endpoint semánticamente expresivo para crear instancias |
| `POST /api/v1/my-pokemon/{id}/heal/` | Sin curación, un Pokémon debilitado es inutilizable |
| Advertencia de velocidad en `/turn/` | Informa sobre la mecánica de velocidad sin imponer restricciones |

## Posibles mejoras futuras

- Suite de tests de integración HTTP (APIClient de DRF) para todos los endpoints
- STAB bonus: ×1.5 si el tipo del movimiento coincide con el tipo del atacante
- Golpes críticos: probabilidad 1/16, multiplicador ×1.5
- Turno automático por velocidad: los dos Pokémon atacan en un solo request, ordenados por `speed`
- JWT Authentication (djangorestframework-simplejwt)
- GitHub Actions CI (lint + pytest en cada push)
- Imagen Docker "production-ready" (gunicorn, `DEBUG=False`, `collectstatic`) — la actual es solo para desarrollo local
