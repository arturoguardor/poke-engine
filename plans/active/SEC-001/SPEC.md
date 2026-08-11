# SPEC: SEC-001 — Hardening de settings: DEBUG=False y ALLOWED_HOSTS seguros por defecto

## Contexto Técnico

- `config/settings.py` lee la configuración vía `python-decouple` (`config()` de `decouple`).
- Actualmente `DEBUG = config("DEBUG", default=True)` y `ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*")`.
- Esto significa que **cualquier despliegue que no declare `.env` arranca con DEBUG=True y ALLOWED_HOSTS="\*"**: expone trazas, variables de entorno y detalles internos en producción, y permite Host header injection.
- El proyecto es una API (DRF) con `JSONRenderer` — no se sirven plantillas ni assets propios, por lo que reducir el default de `DEBUG` no afecta el rendering de la API.
- `docker-compose.yml` inyecta `DEBUG` y `ALLOWED_HOSTS` explícitamente en el environment del contenedor (`${DEBUG:-True}`, `${ALLOWED_HOSTS:-*}`). Por tanto, **el flujo Docker de desarrollo local se mantiene intacto** aunque los defaults de settings pasen a seguros: compose los sobreescribe de forma explícita.
- No existe `.env` en el repo (está en `.gitignore`); el arranque actual usa los defaults de settings. `.env.example` declara `DEBUG=True` y `ALLOWED_HOSTS=*`.
- La suite de tests actual (7 tests de `DamageService`) no usa cliente HTTP ni servidor de test; pytest-django carga `config.settings` tal cual.
- Sin embargo, los futuros tests de integración HTTP (TEST-002 del backlog) usarán `testserver` como host (comportamiento del cliente de tests de Django). Con `DEBUG=False` y `ALLOWED_HOSTS` fijo, Django lanza `DisallowedHost` para `testserver` a menos que se incluya explícitamente. Se resuelve en este ticket para no dejar una trampa.

## Alcance de este ticket

- Cambiar los defaults de `DEBUG` y `ALLOWED_HOSTS` en `config/settings.py` a valores seguros.
- Actualizar `.env.example` para reflejar los nuevos defaults de forma coherente.
- Verificar que la suite de tests funciona con `DEBUG=False` (pytest-django ya inyecta `testserver` en `ALLOWED_HOSTS` automáticamente durante los tests, confirmado en el rojo del Paso 1).
- Verificar que la suite de tests completa pasa con los nuevos defaults.
- Verificar que `docker compose config` y el flujo Docker de desarrollo siguen resolviendo defaults correctamente.

## Fuera de alcance

- **Split de settings (base/dev/prod)** — es CONF-002 del backlog; este ticket solo toca defaults de un `settings.py` único.
- **Cambiar `docker-compose.yml`** — el compose es de desarrollo local y debe seguir forzando `DEBUG=True`/`ALLOWED_HOSTS=*` explícitamente. Ajustar compose es DOCKER-001 (imagen production-ready).
- **Añadir `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS** — hardening de producción adicional que corresponde a CONF-002 (settings por entorno), no a este ticket. Este ticket solo elimina los defaults inseguros.
- **Autenticación/permisos** — AUTH-001 del backlog.
- **Logging estructurado, STATIC_ROOT, CACHES** — CONF-002.

## Requisitos

- `DEBUG` debe tomar valor seguro por defecto (`False`) cuando no está declarado en `.env`.
- `ALLOWED_HOSTS` debe tomar un valor restringido por defecto (`localhost,127.0.0.1` en desarrollo) cuando no está declarado en `.env`.
- Debe seguir siendo posible activar `DEBUG=True` y `ALLOWED_HOSTS=*` explícitamente vía `.env` (comportamiento de desarrollo local no se pierde).
- `.env.example` debe declarar los nuevos defaults seguros (para que copiar `cp .env.example .env` no reintroduzca el comportamiento inseguro por accidente).
- La suite de tests debe seguir pasando con `DEBUG=False` por defecto; los tests que usen cliente HTTP deben permitir `testserver`.
- El flujo Docker de desarrollo local (dependiente de `${DEBUG:-True}` en compose) no debe romperse.

## Criterios de Aceptación

- [ ] `config/settings.py` con `DEBUG = config("DEBUG", default=False, cast=bool)` y `ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=lambda v: [...])`.
- [ ] Test unitario que verifica que, sin variables de entorno declaradas, `settings.DEBUG is False`, `localhost` y `127.0.0.1` están en `ALLOWED_HOSTS` y el comodín `*` NO está.
- [ ] Test unitario que verifica que, con `DEBUG=True` y `ALLOWED_HOSTS=*` declarados explícitamente (via `override_settings` o env), los valores se aplican.
- [ ] `.env.example` actualizado: `DEBUG=False`, `ALLOWED_HOSTS=localhost,127.0.0.1`.
- [ ] Suite completa (`pytest -q`) pasa: **9 passed** (7 originales + 2 nuevos de settings, sin regresiones). Confirmado durante el rojo del Paso 1 que pytest-django inyecta `testserver` automáticamente.
- [ ] `python manage.py check` sin errores con los nuevos defaults.
- [ ] `docker compose config` sigue resolviendo `DEBUG=True` y `ALLOWED_HOSTS=*` por defecto (dev local intacto).

## Archivos Afectados

- `config/settings.py` — cambiar defaults de `DEBUG` y `ALLOWED_HOSTS`.
- `.env.example` — actualizar valores de ejemplo.
- `tests/test_settings.py` — nuevo test de los defaults de configuración (TDD). No se toca `conftest.py`: pytest-django ya garantiza `testserver` en `ALLOWED_HOSTS`.

## Dependencias

- Ninguna dependencia Python nueva. `python-decouple` ya está en `requirements.txt`.
- Esta ticket no depende de otros; es prerrequisito lógico de CONF-002, DOCKER-001 y CI-001.

## Riesgos

- **Tests de integración futuros (TEST-002) y `DEBUG=False`** — riesgo descartado durante el rojo del Paso 1: pytest-django añade `testserver` a `ALLOWED_HOSTS` automáticamente en su entorno de test, así que no se requiere soporte manual.
- **Desarrolladores acostumbrados a `cp .env.example .env`** — si el ejemplo quedara con `DEBUG=True`, el hardening sería inútil; por eso `.env.example` se actualiza a los valores seguros.
- **Alguien podría declarar `ALLOWED_HOSTS` con espacios** — el `cast` actual ya hace `strip()` de cada elemento; se conserva.
- **Acceso por IP distinta a localhost en dev sin `.env`** — con los nuevos defaults, `runserver` solo acepta `localhost`/`127.0.0.1`. Es el comportamiento deseado; quienes quieran exponer a la LAN deben declarar `ALLOWED_HOSTS` explícitamente en `.env`.

## Edge Cases

- **Sin `.env` y sin variables de entorno**: defaults seguros (`DEBUG=False`, `ALLOWED_HOSTS=["localhost","127.0.0.1"]`).
- **`.env` con `DEBUG=True`**: se activa debug explícitamente; `ALLOWED_HOSTS` seguirá siendo el default restringido salvo que también se declare.
- **`.env` con `ALLOWED_HOSTS=*`**: explícito, permite cualquier host (uso dev local por LAN), igual que hoy con `.env`.
- **Docker compose sin `.env`**: el compose inyecta `${DEBUG:-True}` y `${ALLOWED_HOSTS:-*}` → sigue forzando dev local; el nuevo default de settings no aplica dentro del contenedor porque compose lo sobreescribe.
- **Variables de entorno del shell del desarrollador**: `decouple` prioriza las variables de entorno reales; si el shell exporta `DEBUG`, ese valor manda. Comportamiento estándar de decouple, se documenta en la SPEC y el test explícito lo cubre con `override_settings`.
