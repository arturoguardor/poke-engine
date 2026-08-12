# Plan: DOCKERIZE - Dockerizar poke-engine (uso local de desarrollo)

## Pasos

### Paso 1: Dockerfile + .dockerignore ✅ COMPLETADO

**Archivos**: `poke-engine/Dockerfile`, `poke-engine/.dockerignore`
**Esfuerzo**: S
**Tests**: `docker build -t poke-engine .` completa sin errores; `docker run --rm poke-engine python manage.py check` pasa
**Acción**:

- [x] Crear `Dockerfile` basado en `python:3.12-slim`
- [x] Instalar dependencias desde `requirements.txt` (no `requirements-dev.txt`, la imagen es de runtime)
- [x] Copiar el código de la app al contenedor
- [x] `EXPOSE 8000`
- [ ] ~~Definir `ENTRYPOINT`/`CMD` apuntando al script del Paso 2~~ — diferido al Paso 2: apuntar a un script inexistente habría roto el test de build de este paso. Por ahora `CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]` directo; el Paso 2 lo reemplazará por `ENTRYPOINT ["/entrypoint.sh"]`.
- [x] Crear `.dockerignore` excluyendo `.venv`, `__pycache__`, `.git`, `.pytest_cache`, `.coverage`, `db.sqlite3`, `plans/`, `ai-specs/`, `devtools-agentic/` (+ `.env`, `.claude/`, IDE/OS files)

**Verificación real ejecutada**:
- `docker build -t poke-engine:step1 .` → éxito
- `docker run --rm poke-engine:step1 python manage.py check` → `System check identified no issues (0 silenced).`
- Confirmado que `.venv`, `.git`, `.pytest_cache`, `.coverage`, `db.sqlite3` no están presentes dentro de la imagen

### Paso 2: entrypoint.sh (arranque automatizado) ✅ COMPLETADO

**Archivos**: `poke-engine/entrypoint.sh`, `poke-engine/Dockerfile` (actualizado: `ENTRYPOINT`/`CMD`)
**Esfuerzo**: S
**Tests**: ejecutar el script manualmente contra un volumen vacío y verificar que crea `db.sqlite3`, aplica migraciones y carga `type_effectiveness.json` sin error; ejecutarlo una segunda vez y confirmar que no falla (idempotente)
**Acción**:

- [x] Script que ejecute `python manage.py migrate` seguido de `python manage.py loaddata fixtures/type_effectiveness.json`
- [x] Usar `exec "$@"` al final para lanzar `runserver 0.0.0.0:8000` como proceso principal (PID 1) y propagar señales correctamente
- [x] Dar permisos de ejecución al script (`chmod +x` en el `Dockerfile`) y referenciarlo como `ENTRYPOINT` (`./entrypoint.sh`), con `CMD` manteniendo `["python", "manage.py", "runserver", "0.0.0.0:8000"]` como argumento por defecto
- [x] No incluir `seed_pokemon` aquí (queda manual, ver SPEC — riesgo de red externa)

**Verificación real ejecutada** (usando un volumen Docker nombrado, sin tocar el `db.sqlite3` real del proyecto):
- 1ª ejecución sobre volumen vacío: aplica las 20 migraciones + `Installed 342 object(s) from 1 fixture(s)` → OK
- 2ª ejecución sobre el mismo volumen: `No migrations to apply` + recarga del fixture sin error → idempotente confirmado
- `db.sqlite3` persiste en el volumen tras ambas ejecuciones
- Contenedor con `CMD` por defecto (`runserver`) responde `HTTP 200` en `http://localhost:8000/api/v1/`
- Recursos de prueba (`poke_test_db`, imagen `poke-engine:step1`) eliminados tras la verificación

### Paso 3: docker-compose.yml ✅ COMPLETADO

**Archivos**: `poke-engine/docker-compose.yml`
**Esfuerzo**: M
**Tests**: `docker compose config` valida sin errores de sintaxis; `docker compose up --build` levanta el servicio `web` y responde en `http://localhost:8000/api/v1/`
**Acción**:

- [x] Definir servicio `web` usando el `Dockerfile` del Paso 1
- [x] Bind mount del código fuente para reflejar cambios sin rebuild (`.:/app`)
- [x] Persistencia de `db.sqlite3`: en vez de un volumen separado, se optó por el bind mount completo `.:/app` (incluye `db.sqlite3` del host) — evita el riesgo de locking de un bind mount de archivo suelto en Windows, ya anotado en `SPEC.md`
- [x] Mapear puerto `8000:8000`
- [x] Variables de entorno vía `environment:` con sustitución `${VAR:-default}` (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) — no se usó `env_file` para no depender de que `.env` exista; si `.env` está presente Compose lo autocarga para la sustitución, si no, aplican los defaults de `config/settings.py`
- [x] Revisado `.env.example`: ya cubre exactamente `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` — no requirió cambios

**Verificación real ejecutada** (contra el `db.sqlite3` real del proyecto — seguro por ser idempotente, ya validado en el Paso 2):
- `docker compose config` → resuelve defaults correctamente sin `.env` presente
- `docker compose up --build -d` → build + arranque OK; `GET /api/v1/` → `HTTP 200`; `GET /api/docs/` → `HTTP 200`
- `docker compose down` + `docker compose up -d` (sin `--build`) → `No migrations to apply`, datos persistidos
- `docker compose exec web python manage.py seed_pokemon` → ejecuta correctamente contra PokéAPI (`0 creados, 10 actualizados`, ya existían)
- `docker compose down` final → `git status --short db.sqlite3` sigue mostrando `??` (sin cambios de tracking, sin efectos secundarios inesperados)

### Paso 4: Documentación (README.md) ✅ COMPLETADO

**Archivos**: `poke-engine/README.md`
**Esfuerzo**: S
**Tests**: seguir las instrucciones documentadas al pie de la letra en una carpeta limpia y confirmar que funcionan (se valida junto con el Paso 5)
**Acción**:

- [x] Añadida sección "Opción B: Docker" junto al setup existente con venv (renombrado a "Opción A: entorno virtual (venv)")
- [x] Documentado `docker compose up --build` como comando principal
- [x] Documentado el paso manual `docker compose exec web python manage.py seed_pokemon`
- [x] Aclarado que esta imagen es solo para desarrollo local (sin gunicorn, `DEBUG=True` por defecto), incluyendo el bind mount del código y la carga de `.env`
- [x] Quitado "Docker + docker-compose" de "Posibles mejoras futuras" (ya implementado) y añadida en su lugar la mejora futura pendiente real: imagen "production-ready" (gunicorn, `DEBUG=False`, `collectstatic`)

**Nota**: los comandos documentados son textualmente los mismos que ya se ejecutaron y verificaron en el Paso 3 (`docker compose up --build`, `docker compose exec web python manage.py seed_pokemon`), por lo que ya están validados en la práctica; la validación formal "en carpeta limpia" queda para el Paso 5.

### Paso 5: Verificación end-to-end ✅ COMPLETADO

**Archivos**: ninguno (validación manual sobre lo construido en los pasos 1-4)
**Esfuerzo**: M
**Tests**: checklist manual cubriendo los Criterios de Aceptación de `SPEC.md`
**Acción**:

- [x] `docker compose up --build` desde cero (sin volumen previo) levanta la API en `http://localhost:8000/api/v1/`
- [x] Migraciones y fixture `type_effectiveness.json` se aplicaron automáticamente (verificado por logs: 20/20 migraciones + `Installed 342 object(s)`)
- [x] Swagger UI accesible en `http://localhost:8000/api/docs/`
- [x] `docker compose down` + `docker compose up` (sin `--build`) conserva los datos previos
- [x] `docker compose exec web python manage.py seed_pokemon` funciona manualmente
- [x] Inspeccionada la imagen y confirmado que no incluye `.venv`, `.git`, `.pytest_cache`, `.coverage`
- [x] Criterios de Aceptación de `SPEC.md` marcados como cumplidos

**Metodología de verificación**: en vez de validar solo sobre el repo de trabajo (que ya tenía un `db.sqlite3` de desarrollo con datos), se armó una copia "carpeta limpia" en el directorio temporal de scratchpad — usando `git ls-files` (archivos versionados) + los 4 archivos nuevos de Docker aún no commiteados (`Dockerfile`, `docker-compose.yml`, `.dockerignore`, `entrypoint.sh`) — para simular fielmente la experiencia de un clon nuevo sin `.venv` ni `db.sqlite3` previos:

- Build + arranque desde cero: 20/20 migraciones aplicadas, fixture cargado, `/api/v1/` y `/api/docs/` → `HTTP 200`
- `seed_pokemon` sobre BD vacía: `10 creados, 0 actualizados`
- `down` + `up` (sin rebuild): `No migrations to apply` → persistencia confirmada
- Imagen inspeccionada: sin `.venv`, `.git`, `.pytest_cache`, `.coverage`
- Recursos de la carpeta limpia (contenedor, red, imagen, directorio temporal) eliminados al finalizar
- Confirmado con `git status --short db.sqlite3` que el `db.sqlite3` real del proyecto no sufrió cambios de tracking por estas pruebas
