# Verification: DOCKERIZE

## Criterios de Aceptación

- [x] `docker compose up --build` levanta la API en `http://localhost:8000/api/v1/` sin pasos manuales adicionales — ✅ Implementado. Verificado dos veces: contra el repo de trabajo y contra una copia "carpeta limpia" (sin `.venv`/`.git`/`db.sqlite3` previos) simulando un clon nuevo. `HTTP 200` en ambos casos.
- [x] Migraciones y fixture `type_effectiveness.json` se aplican automáticamente en el primer arranque — ✅ Implementado (`entrypoint.sh`: `migrate --noinput` + `loaddata fixtures/type_effectiveness.json` antes de `exec "$@"`). Verificado en carpeta limpia: 20/20 migraciones + `Installed 342 object(s) from 1 fixture(s)`.
- [x] Los datos persisten entre `docker compose down` y `docker compose up` — ✅ Implementado, pero con una desviación respecto a la redacción literal de `SPEC.md` (ver Discrepancias #1). Verificado: `seed_pokemon` (10 creados en carpeta limpia) sobrevive a `down` + `up` sin `--build`; logs muestran `No migrations to apply` en el segundo arranque.
- [x] Swagger UI accesible en `http://localhost:8000/api/docs/` desde el contenedor — ✅ Implementado. `HTTP 200` verificado.
- [x] La imagen no incluye `.venv`, `.git`, `.pytest_cache`, `.coverage` ni el `db.sqlite3` de desarrollo local del host — ✅ Implementado vía `.dockerignore`. Verificado inspeccionando la imagen construida desde carpeta limpia (`ls -a /app` sin coincidencias).
- [x] `docker compose exec web python manage.py seed_pokemon` funciona manualmente — ✅ Implementado. Verificado dos veces: contra `db.sqlite3` real (`0 creados, 10 actualizados`, ya existían) y contra carpeta limpia (`10 creados, 0 actualizados`).
- [x] `README.md` actualizado con instrucciones de uso vía Docker — ✅ Implementado. Sección "Opción B: Docker" (README.md líneas 65-89 aprox.), y se retiró "Docker + docker-compose" de "Posibles mejoras futuras" (ya no aplica) reemplazándolo por la mejora futura real pendiente (imagen production-ready).

## Tests

- Pasados: **378 / 379** (1 `skipped`, preexistente y no relacionado con este ticket)
- Cobertura: 39% global (`pokedex` + `battle`) — sin cambios respecto al estado previo al ticket; este ticket no modifica código de aplicación, solo añade infraestructura Docker (`Dockerfile`, `docker-compose.yml`, `.dockerignore`, `entrypoint.sh`) y documentación. La verificación funcional de la infraestructura se hizo mediante comandos Docker reales documentados en `PLAN.md` (pasos 1-5), no mediante pytest.
- Suite ejecutada con `.venv/Scripts/python.exe -m pytest --cov=pokedex --cov=battle --cov-report=term-missing -q` — sin regresiones.

## Discrepancias

1. **Persistencia de `db.sqlite3`: bind mount completo en vez de volumen dedicado.** `SPEC.md` (Requisitos, línea 21) pedía "persista `db.sqlite3` en un volumen". La implementación usa `volumes: - .:/app` (bind mount de todo el directorio del proyecto) en vez de un volumen Docker nombrado apuntando solo al archivo. Esto fue una decisión deliberada tomada durante el Paso 3, documentada en `PLAN.md` y ya anticipada como mitigación en la sección Riesgos de `SPEC.md` ("bind mounts de un único archivo... a veces presentan problemas de locking/permisos... usar un named volume o montar el directorio completo"). El criterio de aceptación subyacente (persistencia entre `down`/`up`) se cumple y fue verificado. **No bloqueante.**
2. **Variables de entorno: sustitución `${VAR:-default}` en vez de `env_file: .env`.** `SPEC.md` (Requisitos, línea 23) pedía "cargue variables de entorno desde `.env`". La implementación usa `environment:` con sustitución `${SECRET_KEY:-...}` etc., que Docker Compose resuelve automáticamente desde un `.env` en la raíz del proyecto si existe, y aplica los defaults de `config/settings.py` si no. Se prefirió sobre `env_file: .env` porque este último falla si el archivo no existe (rompiendo el edge case "`docker compose up` funciona out-of-the-box sin `.env`", explícitamente listado en `SPEC.md`). Verificado con `docker compose config` sin `.env` presente: resuelve los defaults correctamente. **No bloqueante — de hecho, resuelve mejor el edge case documentado que la redacción original del requisito.**
3. **Alcance de pytest más amplio de lo esperado.** La ejecución de `pytest` desde la raíz de `poke-engine` también recolecta `devtools-agentic/tests/` (herramienta interna de tooling, no parte de la app Django). Esto es preexistente al ticket (config de `pytest.ini`/`rootdir`) y no tiene relación con la dockerización; se documenta solo para que quede claro que los "378 pasados" incluyen esas pruebas y no únicamente `tests/pokedex/`.

## Veredicto

**PASS**

Los 7 criterios de aceptación de `SPEC.md` están implementados y verificados con evidencia real (comandos Docker ejecutados, no solo inspección de código), incluyendo una corrida completa en una copia "carpeta limpia" que simula un clon nuevo. Las dos desviaciones respecto a la redacción literal del `SPEC.md` (bind mount completo, sustitución de variables) están justificadas, documentadas, y no comprometen ningún criterio de aceptación — en el caso de las variables de entorno, incluso mejoran el cumplimiento de un edge case explícito. La suite de tests existente (378/379, 1 skip preexistente) pasa sin regresiones.
