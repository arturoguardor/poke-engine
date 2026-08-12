# Code Review: SEC-001 — Hardening de settings: DEBUG=False y ALLOWED_HOSTS seguros por defecto

## Resumen

Revisión completa del código implementado en `config/settings.py`, `tests/test_settings.py` y `.env.example`. Se reconstruyó el venv (estaba corrupto tras mover el proyecto de `VisioTech\poke-engine` a `arturoguardor\poke-engine`) para ejecutar tests, linting y verificaciones con datos reales.

Todos los criterios de aceptación de la SPEC se verifican con ejecución real, no solo análisis estático.

## Evidencias de ejecución

| Verificación                                                        | Resultado                                                    |
| ------------------------------------------------------------------- | ------------------------------------------------------------ |
| `python -m pytest -q`                                               | **9 passed in 7.43s** (7 de DamageService + 2 de settings)   |
| `python -m black --check config/settings.py tests/test_settings.py` | 2 files would be left unchanged ✅                           |
| `python -m flake8 config/settings.py tests/test_settings.py`        | Exit 0 (sin errores) ✅                                      |
| `python manage.py check`                                            | System check identified no issues (0 silenced) ✅            |
| `docker compose config`                                             | `DEBUG: "True"`, `ALLOWED_HOSTS: '*'` → dev local intacto ✅ |

## Cumplimiento de criterios de aceptación

- [x] `config/settings.py` con `DEBUG = config("DEBUG", default=False, cast=bool)` — ✅ Línea 8.
- [x] `config/settings.py` con `ALLOWED_HOSTS = config(..., default="localhost,127.0.0.1", cast=lambda v: [s.strip() for s in v.split(",")])` — ✅ Líneas 9-13. El cast conserva `strip()` por elemento.
- [x] Test unitario de defaults seguros — ✅ `tests/test_settings.py::test_settings_defaults_are_safe`. Verifica `DEBUG is False`, `localhost` y `127.0.0.1` están en `ALLOWED_HOSTS`, y `*` NO está. Robusto ante `testserver` inyectado por pytest-django.
- [x] Test unitario de override explícito — ✅ `tests/test_settings.py::test_env_vars_still_enable_dev_mode`. Usa subprocess con `DEBUG=True` y `ALLOWED_HOSTS=*` en el entorno; verifica que `decouple` lee las variables reales, no solo el decorador de Django.
- [x] `.env.example` actualizado con `DEBUG=False`, `ALLOWED_HOSTS=localhost,127.0.0.1` — ✅ Líneas 2-3.
- [x] Suite completa pasa: 9 passed sin regresiones — ✅ Verificado con ejecución real.
- [x] `python manage.py check` sin errores — ✅ Verificado.
- [x] `docker compose config` sigue resolviendo `DEBUG=True` y `ALLOWED_HOSTS=*` — ✅ Verificado.

## Hallazgos

### 🔴 Críticos

_Ninguno._

### 🟡 Medios

#### M-1: `test_env_vars_still_enable_dev_mode` — subprocess con dependencias de entorno no declaradas

- **Archivo**: `tests/test_settings.py`, líneas 20-56
- **Problema**: El test lanza `django.setup()` en un subprocess. Esto implica:
  1. Depende de que Django esté en el `PYTHONPATH` del proceso padre (heredado por el subprocess). Si el venv no está activo, el test falla con `ModuleNotFoundError`.
  2. `django.setup()` en el subprocess se conecta a la BD (`db.sqlite3` en el CWD), lo cual es un side effect no declarado.
  3. `decouple` en el subprocess puede leer el archivo `.env` del CWD si existe, potencialmente compitiendo con las variables de entorno pasadas en `env=entorno`.

  **Justificación del enfoque actual**: El PLAN documenta que la versión anterior usaba `@override_settings(DEBUG=True)`, lo cual solo probaba el decorador de Django, no el comportamiento real de `decouple.config()`. El cambio a subprocess es deliberado y está justificado en el docstring del test (líneas 21-30). La justificación es correcta: `override_settings` no habría detectado una regresión en los defaults.

- **Sugerencia**: Documentar en el docstring que el test requiere Django en el PYTHONPATH. Considerar usar `tmp_path` de pytest como CWD del subprocess para aislarlo del `.env` local y del `db.sqlite3`.

  **No bloquea**: el test es correcto en su propósito y pasa consistentemente (9/9 en la suite).

#### M-2: Nombre de la función de test difiere del documentado en el PLAN

- **Archivo**: `tests/test_settings.py`, línea 20
- **Problema**: El PLAN (línea 15) documenta `test_settings_can_be_overridden_explicitly`. El archivo real lo nombra `test_env_vars_still_enable_dev_mode`. Ambos nombres son descriptivos, pero la discrepancia rompe la trazabilidad PLAN → código.
- **Sugerencia**: Renombrar a `test_settings_can_be_overridden_explicitly` o actualizar el PLAN para reflejar el nombre real.

### 🔵 Informativos

#### I-1: Ausencia de type hints en `config/settings.py`

- **Archivo**: `config/settings.py`
- **Observación**: No hay type hints explícitos (`DEBUG: bool`, `ALLOWED_HOSTS: list[str]`). Es práctica común en `settings.py` de Django omitirlos porque los tipos dependen de `decouple` en runtime.
- **No requiere acción** a menos que el estándar del proyecto exija type hints en settings.

#### I-2: `SECRET_KEY` con default inseguro

- **Archivo**: `config/settings.py`, línea 7
- **Observación**: `SECRET_KEY = config("SECRET_KEY", default="dev-secret-key-change-in-production")` tiene un default hardcodeado. La SPEC lo declara fuera de alcance (SEC-001 solo toca `DEBUG` y `ALLOWED_HOSTS`; el hardening completo corresponde a CONF-002). El nombre del default actúa como recordatorio.
- **No requiere acción en este ticket**.

#### I-3: Verificación parcial de stdout en el test de subprocess

- **Archivo**: `tests/test_settings.py`, líneas 54-56
- **Observación**: El test verifica `stdout.startswith("True")` y `"*" in stdout`, pero no parsea la salida completa. Si `stdout` fuera `"True ['*', 'otro']"` el test pasaría igual. Riesgo de falso positivo mínimo dado que el subprocess solo imprime `settings.DEBUG` y `settings.ALLOWED_HOSTS`.
- **No requiere acción**.

#### I-4: Posible interferencia de `.env` local en el subprocess

- **Archivo**: `tests/test_settings.py`, líneas 36-53
- **Observación**: El subprocess hereda el CWD; si existe `.env` en la raíz, `decouple` podría leerlo. Relacionado con M-1. El `.env` está en `.gitignore` y no se commitea, pero un desarrollador con `.env` local podría ver interferencia.
- **No requiere acción inmediata**; se recomienda abordar junto con M-1.

#### I-5: `devtools.yaml` corregido — cambio de infraestructura documentado

- **Archivo**: `devtools.yaml`, líneas 18-24, 35-37
- **Observación**: Se cambió `pytest -q` → `python -m pytest -q` (y `lint_command`/`format_command` con `python -m ...`) porque el launcher del venv guardaba rutas absolutas de la ubicación anterior. Es una corrección de portabilidad legítima. La VERIFICATION.md lo confirma como no-discrepancia.
- **No requiere acción**.

## Checklist

- [x] Sigue PEP 8 y estándares del proyecto — `black --check` pasa limpio, `flake8` exit 0.
- [x] Type hints completos — no aplica en `settings.py` de Django; los tests no requieren type hints adicionales.
- [x] Logging adecuado — no hay `print()` ni logging de información sensible.
- [x] Nombres de variables/funciones descriptivos — claros y autoexplicativos. M-2 señala discrepancia menor con el PLAN.
- [x] Sin código muerto, duplicado o comentado — no se encontró.
- [x] Manejo de errores adecuado — el test captura `resultado.returncode` y muestra `stderr` en caso de fallo (línea 54).
- [x] Validación de entrada en APIs/endpoints — no aplica (solo settings).
- [x] Sin secretos hardcodeados — `SECRET_KEY` tiene default inseguro, fuera de alcance (I-2).
- [x] Tests para cada nueva función — 2 tests (defaults seguros + override explícito).
- [x] Tests cubren casos edge y de error — el test de defaults cubre `testserver` de pytest-django; el test de override cubre activación explícita vía entorno real.
- [x] Tests son independientes y repetibles — no comparten estado mutable. M-1 señala dependencia del PYTHONPATH y posible interferencia de `.env` local.
- [x] Suite completa pasa sin regresiones — 9/9 passed en 7.43s (7 de DamageService + 2 de settings).

## Veredicto

**APPROVED**

El código cumple todos los criterios de aceptación de la SPEC con verificación real. Los cambios en `config/settings.py` y `.env.example` son mínimos, precisos y seguros. La suite de tests (9/9) pasa sin regresiones; `black` y `flake8` no reportan issues; `manage.py check` sale limpio; `docker compose config` confirma que el flujo de desarrollo local sigue intacto.

Los dos hallazgos 🟡 (M-1: subprocess con dependencias de entorno, M-2: nombre de test divergente del PLAN) son mejoras deseables pero no bloquean: el subprocess está justificado en el PLAN y en el docstring del test, y la discrepancia de nombre es cosmética.
