# Plan: SEC-001 — Hardening de settings: DEBUG=False y ALLOWED_HOSTS seguros por defecto

## Pasos

### Paso 1: Tests de defaults seguros (TDD — rojo) ✅ COMPLETADO

**Archivos**: `tests/test_settings.py` (nuevo)
**Esfuerzo**: S
**Tests**: los que se escriben en este paso (usados para demostrar el rojo)

**Acción**:

- [x] Crear `tests/test_settings.py` con:
  - `test_settings_defaults_are_safe` — verifica que `settings.DEBUG is False`, `localhost` y `127.0.0.1` están en `ALLOWED_HOSTS` y el comodín `*` NO está (robusto ante el `testserver` que pytest-django añade automáticamente durante los tests).
  - `test_env_vars_still_enable_dev_mode` — lanza un subproceso con `DEBUG=True` y `ALLOWED_HOSTS=*` en el entorno y verifica que llegan a `settings`, es decir que `config()` sigue leyendo la variable. Corre en un directorio temporal para que un `.env` local no interfiera.

    Sustituye a `test_settings_can_be_overridden_explicitly`, que usaba `override_settings(DEBUG=True)` y luego afirmaba que `DEBUG` era `True`: comprobaba el decorador de Django, no este proyecto, y habría pasado igual con `settings.py` revertido. Ver `SEC-001-CODE-REVIEW.md`.
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

## Respuesta al review

Review aplicado: `SEC-001-CODE-REVIEW.md` (veredicto CHANGES REQUESTED, Reviewer: cline)

| Hallazgo | Decisión | Detalle |
| --- | --- | --- |
| 🟡 M-1 — subproceso frágil: PYTHONPATH, `.env` local y posible creación de BD | Aplicado (variante de la sugerencia 4) | El subproceso corre ahora en `tmp_path` con `PYTHONPATH` a la raíz. Aísla del `.env` del desarrollador, que es el riesgo real: `python-decouple` lo lee del directorio de trabajo y podría ganarle a las variables del test. Descartadas las sugerencias 1 y 3: `decouple` no expone `env_file=None` en la API de `config()`, y mockear `decouple.config` devolvería el test a probar el mock en vez del proyecto — el defecto que esta corrección vino a resolver. |
| 🟡 M-2 — el nombre del test no coincide con el PLAN | Resuelto distinto | El nombre que el PLAN documentaba es el del test tautológico que se retiró: renombrar el nuevo a `test_settings_can_be_overridden_explicitly` restauraría un nombre que describe algo que ya no hace (no usa `override_settings`). Se actualiza el PLAN, que es el documento desactualizado, y se deja constancia de la sustitución. |
| 🔵 I-1 — sin type hints en `settings.py` | Rechazado | El propio hallazgo indica que no aplica a un `settings.py` de Django y que no es un defecto. No se toca. |
| 🔵 I-2 — `SECRET_KEY` con default inseguro | Rechazado | Fuera del alcance declarado en la SPEC: SEC-001 toca `DEBUG` y `ALLOWED_HOSTS`. Corresponde a CONF-002. |
| 🔵 I-3 — verificación parcial de stdout | Aplicado | Aunque el review no pedía acción, el riesgo era real: `"*" in stdout` daba por buena una salida `['*', 'otro']`. El subproceso emite JSON y el test compara `allowed_hosts == ["*"]`. |
| 🔵 I-4 — posible interferencia de `.env` | Aplicado | Resuelto por la misma corrección de M-1. |
| 🔵 I-5 — `devtools.yaml` a `python -m` | Rechazado | No pide acción; confirma la corrección de infraestructura ya documentada. |

### Sobre la nota de ejecución del review

El review dice que no pudo ejecutar `pytest` ni `flake8` porque «el entorno
virtual está corrupto», y marca el checklist a partir de análisis estático.

La premisa no es correcta. El venv funciona invocando el intérprete
directamente, que es justo la corrección que este ticket introdujo en
`devtools.yaml`:

```
.venv/Scripts/python.exe -m pytest -q   → 9 passed
.venv/Scripts/python.exe -m flake8 .    → sin hallazgos
.venv/Scripts/python.exe -m black --check .  → 40 files unchanged
```

Lo que falla es `source .venv/Scripts/activate && python -m pytest`, porque el
`activate` deja en el PATH un launcher con la ruta antigua incrustada. Es el
mismo fallo que el ticket documentó y sorteó.

No cambia ningún hallazgo —los dos medios eran válidos y se han atendido—, pero
sí el nivel de evidencia: el review pudo haberse hecho con la suite en verde
delante en vez de por lectura.

### Verificación tras aplicar

- `pytest`: 9/9 en verde.
- El test corregido **sigue pudiendo fallar**: forzando `DEBUG = False` sin leer
  el entorno, `test_env_vars_still_enable_dev_mode` cae. Sin esa comprobación,
  la corrección de un test tautológico podría haber producido otro.
- `black --check .`: 40 ficheros sin cambios. `flake8`: limpio.

## Respuesta al review — ronda 2

Review aplicado: `SEC-001-CODE-REVIEW.md` (veredicto **APPROVED**, Reviewer: cline)

| Hallazgo | Decisión | Detalle |
| --- | --- | --- |
| 🟡 M-1 — subproceso con dependencias de entorno no declaradas | Ya aplicado en la ronda 1 | Su sugerencia («considerar `tmp_path` como CWD para aislarlo del `.env` local») es exactamente lo que se aplicó al cerrar la ronda 1: `test_env_vars_still_enable_dev_mode(tmp_path)`, `cwd=tmp_path` y `PYTHONPATH` explícito. Nada que hacer. |
| 🟡 M-2 — el nombre del test difiere del PLAN | Ya aplicado en la ronda 1 | Dice que «el PLAN (línea 15) documenta `test_settings_can_be_overridden_explicitly`». Esa línea documenta `test_env_vars_still_enable_dev_mode` desde la ronda 1, con la nota de por qué se sustituyó. Nada que hacer. |
| 🔵 I-1 — sin type hints en `settings.py` | Rechazado (sin cambios) | Misma razón que en la ronda 1: el propio hallazgo indica que no aplica. |
| 🔵 I-2 — `SECRET_KEY` con default inseguro | Rechazado (sin cambios) | Fuera del alcance declarado en la SPEC; corresponde a CONF-002. |
| 🔵 I-3 — verificación parcial de stdout | Ya aplicado en la ronda 1 | El subproceso emite JSON y se compara `allowed_hosts == ["*"]`. |
| 🔵 I-4 — posible interferencia de `.env` | Ya aplicado en la ronda 1 | Resuelto por la misma corrección de M-1. |
| 🔵 I-5 — `devtools.yaml` a `python -m` | Rechazado (sin cambios) | No pide acción. |

**No se ha modificado ningún fichero en esta ronda.** No queda nada por aplicar.

### El review de la ronda 2 se hizo sobre la versión anterior del código

Los siete hallazgos son los de la ronda 1, reemitidos contra un artefacto que ya
los había resuelto. Comprobado:

| Lo que afirma la ronda 2 | Lo que hay en el fichero |
| --- | --- |
| «considerar usar `tmp_path` como CWD» | `def test_env_vars_still_enable_dev_mode(tmp_path)` y `cwd=tmp_path` (l. 62) |
| «depende de que Django esté en el PYTHONPATH heredado» | `"PYTHONPATH": str(raiz)` explícito (l. 50) |
| «`decouple` puede leer el `.env` del CWD» | El CWD es un directorio temporal, sin `.env` |
| «el PLAN (línea 15) documenta `test_settings_can_be_overridden_explicitly`» | La línea 15 documenta `test_env_vars_still_enable_dev_mode` |
| «`tests/test_settings.py`, líneas 20-56» | El test llega a la l. 68 de un fichero de 70 |

Lo llamativo es que la tabla de evidencias **sí es nueva**: ejecutó
`pytest` (9 passed), `black`, `flake8`, `manage.py check` y `docker compose
config`, que es justo lo que le faltó a la ronda 1. Corrió el código nuevo y
reportó sobre el texto antiguo.

No cambia el veredicto —APPROVED es correcto y el ticket está listo— pero sí lo
que vale la ronda: una segunda revisión que no lee el diff de la primera no
comprueba si las correcciones funcionaron, que es para lo que existe.

Queda anotado como carencia del método, no de este ticket: nada obliga hoy a que
la ronda N+1 lea la respuesta de la ronda N, aunque `rounds/` la conserve.
