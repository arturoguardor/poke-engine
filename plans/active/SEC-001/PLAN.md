# Plan: SEC-001 — Hardening de settings: DEBUG=False y ALLOWED_HOSTS seguros por defecto

## Pasos

### Paso 1: Tests de defaults seguros (TDD — rojo) ✅ COMPLETADO

**Archivos**: `tests/test_settings.py` (nuevo)
**Esfuerzo**: S
**Tests**: los que se escriben en este paso (usados para demostrar el rojo)

**Acción**:

- [x] Crear `tests/test_settings.py` con:
  - `test_settings_defaults_are_safe` — verifica que `settings.DEBUG is False`, `localhost` y `127.0.0.1` están en `ALLOWED_HOSTS` y el comodín `*` NO está (robusto ante el `testserver` que pytest-django añade automáticamente durante los tests).
  - `test_settings_can_be_overridden_explicitly` — con `override_settings(DEBUG=True, ALLOWED_HOSTS=["*"])` verifica que el modo dev explícito sigue funcionando (los valores se aplican).
- [x] No tocar `tests/conftest.py`: el rojo del Paso 1 (antes de revertir) confirmó que pytest-django añade `testserver` a `ALLOWED_HOSTS` automáticamente vía su entorno de test — no requiere soporte manual.
- [x] Demostrar el rojo: `python "$DEVTOOLS_HOME/bin/tdd.py" red SEC-001 1` → FALLÓ como se esperaba: `assert 'localhost' in ['*', 'testserver']` (default actual inseguro). Evidencia en `evidence/paso-1-red.txt`.

**Verificación real**: `tdd.py red SEC-001 1` termina con código 1 mostrando el fallo real de los asertos (no un error de colección): el default actual `ALLOWED_HOSTS` contiene `*` y no contiene `localhost`.

### Paso 2: Implementar defaults seguros (TDD — verde) ✅ COMPLETADO

**Archivos**: `config/settings.py`, `.env.example`
**Esfuerzo**: S
**Tests**: `tests/test_settings.py` (del Paso 1)

**Acción**:

- [x] En `config/settings.py`:
  - `DEBUG = config("DEBUG", default=False, cast=bool)`
  - `ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=lambda v: [s.strip() for s in v.split(",")])`
- [x] En `.env.example`:
  - `DEBUG=False`
  - `ALLOWED_HOSTS=localhost,127.0.0.1`
  - Conservar `SECRET_KEY=dev-secret-key-change-in-production`
- [x] Demostrar el verde: `python "$DEVTOOLS_HOME/bin/tdd.py" green SEC-001 2` → suite completa pasa (9 passed: 7 originales + 2 nuevos). Evidencia en `evidence/paso-2-green.txt`.
- [x] Verificación manual: `python manage.py check` con los nuevos defaults → `System check identified no issues (0 silenced)`.
- [x] Verificación manual: `docker compose config` sigue resolviendo `DEBUG=True` y `ALLOWED_HOSTS=*` por defecto (dev local intacto) — verificado.

**Nota de diagnóstico**: `tdd.py` fallaba al principio (`Fatal error in launcher`) porque `devtools.yaml` declaraba `pytest -q`, y el `pytest.exe` del venv guarda la ruta absoluta al intérprete en el momento de crearse — el proyecto se movió de `VisioTech\poke-engine` a `arturoguardor\poke-engine`. Se corrigió `devtools.yaml` (y `quality.*`) usando `python -m ...`, que resuelve el módulo por cwd y es portable. El launcher roto volverá a funcionar cuando se regenere el venv.

**Verificación real**:

- `tdd.py green SEC-001 2` → salida del verde con todos los tests pasando.
- `python manage.py check` → `System check identified no issues (0 silenced)`.
- `docker compose config` → muestra `DEBUG: True` y `ALLOWED_HOSTS: '*'` en el bloque `environment` del servicio `web`.

## Reglas del plan

- Cada paso es ejecutable de forma independiente: el Paso 1 solo escribe tests y demuestra el rojo; el Paso 2 implementa y demuestra el verde.
- No más de 5-7 pasos: este plan tiene 2 pasos.
- No se implementa código en la fase de planificación.
