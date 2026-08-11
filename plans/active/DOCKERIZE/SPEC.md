# SPEC: DOCKERIZE - Dockerizar poke-engine (uso local de desarrollo)

## Contexto Técnico

- Stack: Django 5.1.7 + DRF 3.15.2, Python 3.12.10, SQLite (`db.sqlite3`, archivo local, sin servidor de BD externo).
- Config vía `python-decouple` + `.env` (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) — `.env.example` ya existe con los defaults.
- Sin dependencias de servicios externos en tiempo de ejecución (sin Redis/Celery/etc.). La única llamada de red saliente es a PokéAPI, y sólo desde el management command opcional `seed_pokemon`.
- `TECHNICAL_DECISIONS.md` (líneas 98-104) documenta la elección actual de SQLite "sin servidor externo: no requiere Docker" para el MVP, y en la lista de mejoras futuras (línea 700) ya anota: *"Docker: para eliminar el requisito de tener Python 3.12 instalado. `python:3.12-slim` + volume para SQLite."* — este ticket implementa exactamente esa mejora.
- No existen actualmente `Dockerfile`, `docker-compose.yml` ni `.dockerignore` en el repo.
- Servidor de desarrollo: `python manage.py runserver` (WSGI dev server). **Decisión confirmada con el usuario: esta dockerización es solo para desarrollo local — se usa `runserver` dentro del contenedor, no se añade gunicorn ni se cambia el comportamiento de `DEBUG`.**
- Swagger UI en `/api/docs/`, schema en `/api/schema/`.
- Tests con pytest / pytest-cov; existen `.coverage` y `.pytest_cache/` que no deben copiarse a la imagen.
- `STATIC_URL` está definido pero no `STATIC_ROOT`; con `runserver` y `DEBUG=True` esto no es un problema (django.contrib.staticfiles sirve los assets de Swagger/admin directamente).

## Requisitos

- Crear un `Dockerfile` basado en `python:3.12-slim` que instale las dependencias de `requirements.txt` y arranque la app con `manage.py runserver 0.0.0.0:8000`.
- Crear un `docker-compose.yml` para desarrollo local que:
  - levante el servicio `web`
  - monte el código fuente como volumen (para reflejar cambios sin rebuild)
  - persista `db.sqlite3` en un volumen para no perder datos entre `down`/`up` o rebuilds
  - exponga el puerto 8000
  - cargue variables de entorno desde `.env` (reutilizando `.env.example` como plantilla)
- Crear un `.dockerignore` que excluya `.venv`, `__pycache__`, `.git`, `.pytest_cache`, `.coverage`, `plans/`, `ai-specs/`, `devtools-agentic/`, y `db.sqlite3` si se gestiona vía volumen.
- Automatizar `migrate` + `loaddata fixtures/type_effectiveness.json` al arrancar el contenedor (entrypoint script), de forma idempotente (no debe fallar si ya están aplicadas).
- `seed_pokemon` queda **fuera** del entrypoint automático (depende de red externa) — se documenta como paso manual: `docker compose exec web python manage.py seed_pokemon`.
- Documentar en `README.md` el flujo `docker compose up` como alternativa al setup con venv.

## Criterios de Aceptación

- [x] `docker compose up --build` levanta la API en `http://localhost:8000/api/v1/` sin pasos manuales adicionales. Verificado en carpeta limpia (sin `.venv`/`.git`/`db.sqlite3` previos): `HTTP 200`.
- [x] Migraciones y fixture `type_effectiveness.json` se aplican automáticamente en el primer arranque. Verificado: 20/20 migraciones aplicadas + `Installed 342 object(s) from 1 fixture(s)` en el primer `up --build` sobre carpeta limpia.
- [x] Los datos persisten entre `docker compose down` y `docker compose up` (bind mount completo `.:/app`, no un volumen de archivo suelto — ver Riesgos). Verificado: tras `seed_pokemon` (10 creados) + `down` + `up`, `showmigrations`/logs confirman `No migrations to apply` y los datos siguen presentes.
- [x] Swagger UI accesible en `http://localhost:8000/api/docs/` desde el contenedor. Verificado: `HTTP 200`.
- [x] La imagen no incluye `.venv`, `.git`, `.pytest_cache`, `.coverage` ni el propio `db.sqlite3` de desarrollo local del host. Verificado inspeccionando la imagen construida desde carpeta limpia.
- [x] `docker compose exec web python manage.py seed_pokemon` funciona manualmente. Verificado dos veces: contra `db.sqlite3` real (10 actualizados, ya existían) y contra carpeta limpia (10 creados desde cero).
- [x] `README.md` actualizado con instrucciones de uso vía Docker. Sección "Opción B: Docker" añadida junto al setup con venv.

## Archivos Afectados

- `poke-engine/Dockerfile` — nuevo, imagen de la app (python:3.12-slim + requirements.txt).
- `poke-engine/docker-compose.yml` — nuevo, servicio `web` + volumen para SQLite.
- `poke-engine/.dockerignore` — nuevo.
- `poke-engine/entrypoint.sh` (o script equivalente) — nuevo, ejecuta `migrate` + `loaddata` antes de `runserver`.
- `poke-engine/README.md` — sección de setup ampliada con instrucciones Docker.
- `poke-engine/.env.example` — revisar si necesita nuevas variables (p. ej. host/puerto explícitos para compose).

## Dependencias

- Docker Desktop en la máquina del usuario (Windows) — asumido, no verificado en esta sesión.
- Ninguna dependencia Python nueva (no se añade gunicorn al quedar fuera de alcance el uso "preparado para despliegue").

## Riesgos

- **Volumen de BD en Windows** — los bind mounts de un único archivo (`db.sqlite3`) en Docker Desktop sobre Windows a veces presentan problemas de locking/permisos. Mitigación: usar un named volume o montar el directorio completo del proyecto en vez de un bind mount de solo el archivo.
- **`seed_pokemon` depende de red externa (PokéAPI)** — no debe ejecutarse en el entrypoint automático para no bloquear el arranque del contenedor si no hay conexión o hay rate-limiting.
- **Alcance limitado a desarrollo** — al no incluir gunicorn ni `DEBUG=False` por defecto, esta imagen no es apta para producción tal cual; si en el futuro se necesita desplegar, requerirá un ticket adicional (alineado con la opción "preparado para despliegue" descartada en este ticket).

## Edge Cases

- Primer arranque con volumen vacío: no existe `db.sqlite3` → `migrate` debe crearla desde cero antes de `loaddata`.
- Rebuild de imagen (`--build`) sin tocar el volumen: los datos deben sobrevivir.
- Contenedor sin acceso a internet: `seed_pokemon` debe fallar de forma clara sin afectar el servicio principal (que ya está corriendo).
- `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` no definidos en `.env`: deben tomar los defaults ya presentes en `config/settings.py` para que `docker compose up` funcione out-of-the-box sin `.env`.
