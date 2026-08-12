# Code Review: SEC-001 — Hardening de settings: DEBUG=False y ALLOWED_HOSTS seguros por defecto

## Resumen

Revisión estática del código implementado en los archivos `config/settings.py`, `tests/test_settings.py` y `.env.example` correspondientes al ticket SEC-001. La revisión verifica el cumplimiento de la SPEC, la calidad del código, la seguridad y la mantenibilidad.

**Nota sobre ejecución**: el entorno virtual del proyecto está corrupto — fue creado en la ruta original `VisioTech\poke-engine` y el proyecto se movió a `arturoguardor\poke-engine`. El launcher `python.exe` del venv guarda la ruta absoluta al intérprete en `pyvenv.cfg` (`home = C:\Program Files\Python312`), y los scripts del venv referencian esa ruta. `source .venv/Scripts/activate && python -m pytest` falla con `ModuleNotFoundError: No module named 'django'` porque el venv no tiene paquetes instalados (no existe `pip` en `Scripts/`). Esta situación está documentada en el PLAN (línea 40: "el proyecto se movió de `VisioTech\poke-engine` a `arturoguardor\poke-engine`"). No se pudo ejecutar `flake8` ni `pytest`. La VERIFICATION.md existente reporta 9/9 tests pasados en su momento; este review se basa en análisis estático.

## Hallazgos

### 🔴 Críticos

_Ninguno._

### 🟡 Medios

#### M-1: `test_env_vars_still_enable_dev_mode` — subprocess frágil con riesgo de side effects

- **Archivo**: `tests/test_settings.py`, líneas 20-56
- **Problema**: El test lanza `django.setup()` en un subprocess. Esto:
  1. Depende de que Django esté en el `PYTHONPATH` del proceso padre (heredado por el subprocess). Si el venv no está activo, el test falla con `ModuleNotFoundError`.
  2. `django.setup()` inicializa Django completamente, incluyendo la conexión a BD. Si el CWD contiene un `db.sqlite3`, el subprocess se conecta a él; si no, Django podría intentar crearlo (`sqlite3` lo crea automáticamente al conectarse). Esto es un side effect no declarado.
  3. `decouple` en el subprocess leerá el archivo `.env` del CWD si existe (comportamiento por defecto de `python-decouple`). Si un desarrollador tiene `.env` local con `DEBUG=True`, el valor de `os.environ["DEBUG"]` en el subprocess podría ser sobrescrito por el archivo `.env`. El test configura las variables en `env=entorno`, pero `decouple` consulta el archivo `.env` antes que las variables de entorno en algunos casos (dependiendo de la versión).

  **Justificación del enfoque actual**: El PLAN documenta que la versión anterior usaba `@override_settings(DEBUG=True)`, lo cual solo probaba el decorador de Django, no el comportamiento real de `decouple.config()`. El cambio a subprocess fue deliberado para probar la lectura real de variables de entorno. Esta justificación es correcta y está documentada en el docstring del test (líneas 21-30).

- **Sugerencia**:
  1. Añadir `env_file=None` o equivalente si `decouple` lo soporta, para aislar el subprocess del `.env` local.
  2. Documentar en el docstring que este test requiere Django en el PYTHONPATH.
  3. Considerar mockear `decouple.config` en el proceso principal en lugar del subprocess, aunque esto reduce la fidelidad del test.
  4. Usar `tmp_path` de pytest para ejecutar el subprocess en un directorio temporal sin `.env`.

  **No bloquea** porque la justificación es sólida y el test cumple el criterio de aceptación.

#### M-2: Nombre de la función de test no coincide con el nombre documentado en el PLAN

- **Archivo**: `tests/test_settings.py`, línea 20
- **Problema**: El PLAN (línea 15) documenta el test como `test_settings_can_be_overridden_explicitly`. El archivo real lo nombra `test_env_vars_still_enable_dev_mode`. Aunque ambos nombres son descriptivos, la discrepancia puede causar confusión al buscar referencias cruzadas entre PLAN y código.
- **Sugerencia**: Renombrar a `test_settings_can_be_overridden_explicitly` para mantener trazabilidad con el PLAN, o actualizar el PLAN para reflejar el nombre real.

### 🔵 Informativos

#### I-1: Ausencia de type hints en `config/settings.py`

- **Archivo**: `config/settings.py`
- **Observación**: El archivo no contiene type hints (e.g., `DEBUG: bool`, `ALLOWED_HOSTS: list[str]`). Es una práctica común en archivos `settings.py` de Django no usar type hints explícitos porque los valores se resuelven en runtime y los tipos dependen de la configuración de `decouple`. No se considera un defecto, pero se señala para consistencia con el resto del proyecto si otras partes sí usan type hints.
- **No requiere acción** a menos que el estándar interno del proyecto exija type hints en settings.

#### I-2: `SECRET_KEY` con default inseguro en desarrollo

- **Archivo**: `config/settings.py`, línea 7
- **Observación**: `SECRET_KEY = config("SECRET_KEY", default="dev-secret-key-change-in-production")` tiene un default hardcodeado que es inseguro para producción. La SPEC lo declara explícitamente fuera de alcance (SEC-001 solo toca `DEBUG` y `ALLOWED_HOSTS`; el hardening completo de settings corresponde a CONF-002). El nombre del default (`...change-in-production`) actúa como recordatorio.
- **No requiere acción en este ticket**.

#### I-3: `test_env_vars_still_enable_dev_mode` verifica stdout de forma parcial

- **Archivo**: `tests/test_settings.py`, líneas 54-56
- **Observación**: El test verifica `stdout.startswith("True")` y `"*" in stdout`, pero no parsea la salida completa para verificar que `ALLOWED_HOSTS` sea exactamente `['*']`. Si `stdout` fuera `"True ['*', 'otro']"` el test pasaría igual. Sin embargo, la SPEC solo pide verificar "que los valores se aplican", y el test del subprocess con `DEBUG=True` y `ALLOWED_HOSTS=*` en el entorno cubre el criterio. El riesgo de falsos positivos es mínimo.
- **No requiere acción**.

#### I-4: Posible interferencia de `.env` local en tests

- **Archivo**: `tests/test_settings.py`, líneas 36-53
- **Observación**: El subprocess hereda el CWD del proceso padre. Si existe un archivo `.env` en la raíz del proyecto, `decouple` lo leerá. Aunque `.env` está en `.gitignore` y no se commitea, un desarrollador con `.env` local podría ver comportamientos inesperados en este test si su `.env` declara valores que entran en conflicto con las variables de entorno del subprocess. Relacionado con M-1.
- **No requiere acción inmediata**, pero se recomienda abordarlo junto con M-1.

#### I-5: `devtools.yaml` corregido — cambio de infraestructura documentado

- **Archivo**: `devtools.yaml`, líneas 18-24
- **Observación**: El PLAN documenta que `devtools.yaml` pasó de `pytest -q` a `python -m pytest -q` (y `lint_command`/`format_command` con `python -m ...`) porque el launcher del venv quedó roto tras mover el proyecto. Esto es una corrección de infraestructura legítima que mejora la portabilidad. La VERIFICATION.md lo confirma como no-discrepancia. La sección `quality` (`lint_command: python -m black --check . && python -m flake8 .`) también se actualizó consistentemente.
- **No requiere acción**.

## Checklist

- [x] Sigue PEP 8 y estándares del proyecto — revisión estática; `black` y `flake8` no ejecutables por venv roto, pero el código es limpio y consistente.
- [x] Type hints completos — no aplica en `settings.py` de Django; el test no requiere type hints adicionales.
- [x] Logging adecuado — no hay `print()` ni logging de información sensible.
- [x] Nombres de variables/funciones descriptivos — los nombres son claros. M-2 señala discrepancia menor con el PLAN.
- [x] Sin código muerto, duplicado o comentado — no se encontró.
- [x] Manejo de errores adecuado — el test captura `resultado.returncode` y muestra `stderr` en caso de fallo (línea 54).
- [x] Validación de entrada en APIs/endpoints — no aplica (solo settings).
- [x] Sin secretos hardcodeados — `SECRET_KEY` tiene default inseguro pero es de desarrollo (I-2, fuera de alcance).
- [x] Tests para cada nueva función — 2 tests nuevos para las 2 funciones (defaults seguros + override explícito).
- [x] Tests cubren casos edge y de error — el test de defaults cubre el edge case de `testserver` inyectado por pytest-django; el test de override cubre la activación explícita. El test del subprocess tiene `assert resultado.returncode == 0` que captura errores de inicialización.
- [x] Tests son independientes y repetibles — no comparten estado mutable entre sí. M-1 señala dependencia del entorno (PYTHONPATH, `.env` local).

## Veredicto

**APPROVED**

El código cumple con todos los criterios de aceptación de la SPEC. Los cambios en `config/settings.py` y `.env.example` son mínimos, precisos y seguros. Los tests cubren tanto los defaults seguros como la capacidad de override explícito. Los hallazgos 🟡 señalados (M-1: subprocess frágil, M-2: nombre de test divergente del PLAN) son mejoras deseables pero no bloquean la entrega: la justificación del subprocess está documentada y es correcta, y el nombre del test es descriptivo aunque difiera del PLAN.
