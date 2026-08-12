# Review del PLAN — DOCKERIZE

- **Revisor:** claude-code (Reviewer declarado en `devtools.yaml`)
- **Fecha:** 2026-08-11
- **Solicitado:** 2026-08-06 (`.review-requested`, tipo `plan`)
- **Veredicto:** APPROVED, con dos observaciones no bloqueantes

## Nota sobre el momento de esta revisión

La revisión se pidió el 6 de agosto, antes de ejecutar el plan, y nadie la
atendió: la señal quedó cinco días en `pending` mientras el trabajo se
completaba y se commiteaba. Revisar hoy un plan ya ejecutado no es lo mismo que
revisarlo antes, y conviene decirlo en vez de fingir lo contrario.

Por eso esto no es una revisión del plan sobre el papel, sino **del plan tal y
como se ejecutó**: se han comprobado los artefactos reales contra lo que el
PLAN dice haber hecho.

## Lo comprobado

No se dan por buenas las casillas marcadas; se ha mirado el resultado.

| Afirmación del PLAN | Comprobación |
| --- | --- |
| `.dockerignore` excluye `.venv`, `.git`, `.pytest_cache`, `.coverage`, `db.sqlite3`, `plans/`, `ai-specs/` | ✅ Los siete, más `.env`, `.claude/`, ficheros de IDE y de SO |
| `entrypoint.sh` termina en `exec "$@"` para que `runserver` sea PID 1 | ✅ Presente, y con `set -e` |
| `migrate` idempotente | ✅ `--noinput`, no falla con migraciones ya aplicadas |
| Bind mount `.:/app` y puerto `8000:8000` | ✅ Ambos en `docker-compose.yml` |
| Variables por sustitución, sin depender de que exista `.env` | ✅ `${VAR:-default}` en las tres |
| README con la sección Docker | ✅ Sección «Opción B: Docker» |

Las desviaciones respecto al plan original están **documentadas y
justificadas** en el propio PLAN: el `ENTRYPOINT` diferido del Paso 1 al 2
(apuntar a un script inexistente habría roto el build del paso) y el bind mount
completo en vez de un volumen para `db.sqlite3` (evita el bloqueo de un bind
mount de fichero suelto en Windows). Las dos decisiones son correctas y
explican el porqué, no solo el qué.

La SPEC declara «Fuera de alcance», y lo entregado no se sale: no hay gunicorn,
ni `collectstatic`, ni cambios de `DEBUG` en `settings.py`.

## Observaciones

### 1. `loaddata` se ejecuta en cada arranque, no solo en el primero

`entrypoint.sh` carga `fixtures/type_effectiveness.json` cada vez que arranca el
contenedor. Con datos intactos es inocuo —342 filas con PK fija que se
reescriben iguales—, así que cumple la idempotencia que pedía la SPEC.

El matiz: si alguien ajusta a mano una efectividad en la base de datos local,
el siguiente `docker compose up` la revierte **en silencio**. No es un fallo del
plan (la SPEC pedía exactamente esto), pero merece una línea en el README o una
guarda del tipo «solo si la tabla está vacía».

No bloquea: es dato de referencia, no dato de usuario.

### 2. El compose reintroduce los defaults que SEC-001 acaba de endurecer

```yaml
DEBUG: ${DEBUG:-True}
ALLOWED_HOSTS: ${ALLOWED_HOSTS:-*}
```

SEC-001 cambió esos mismos defaults en `config/settings.py` a `False` y
`localhost,127.0.0.1`. El compose los vuelve a poner permisivos por defecto.

**Es deliberado y está previsto**: la SPEC de SEC-001 lo verificó
explícitamente («docker compose config sigue resolviendo `DEBUG=True` — el
flujo Docker de dev local queda intacto»). El desarrollo local necesita esos
valores.

Lo que falta es que el fichero lo diga **dentro de sí mismo**. Hoy, quien copie
`docker-compose.yml` a un servidor se lleva `DEBUG=True` y `ALLOWED_HOSTS=*` sin
ningún aviso; el único sitio donde consta que esto es solo para desarrollo es el
README y esta SPEC. Dos líneas de comentario en la cabecera del compose cierran
el hueco.

No bloquea el archivado de este ticket: el riesgo lo introduce quien despliegue,
no el plan. Pero conviene anotarlo como mejora en el backlog.

## Veredicto

**APPROVED**

El plan se ejecutó completo, las desviaciones están justificadas, lo entregado
coincide con lo declarado y no se pasa del alcance. Las dos observaciones son
mejoras para el backlog, no correcciones para este ticket.
