# 01 — Fundamentos

> El piso sobre el que se construye todo lo demás: cómo funciona el sistema operativo donde corre tu código, cómo viajan los datos por la red y cuáles son los principios que guían las decisiones técnicas en equipos de software reales.

**Área:** `01-fundamentos` · **Nivel:** Fundamentos → Intermedio · **Prerequisito:** Ninguno

---

> [!IMPORTANT]
> **Al terminar esta área deberías poder:**
> - Navegar un sistema Linux con confianza desde la terminal
> - Entender qué pasa entre que un usuario hace click en “Enviar” y el servidor responde
> - Explicar el modelo HTTP, TCP/IP y DNS sin mirar apuntes
> - Aplicar principios de ingeniería de software (SOLID, DRY, KISS) al revisar código

---

## Sub-áreas

### [Linux y Terminal](./linux-y-terminal/)

El entorno donde vive tu código en producción. Aprenderás a moverte con fluidez, administrar procesos y escribir scripts que automatizan trabajo real.

| Archivo | Contenido |
|---------|----------|
| [01 — Fundamentos Linux](./linux-y-terminal/01-fundamentos-linux.md) | Filesystem, permisos, usuarios, procesos, variables de entorno |
| [02 — Bash y comandos](./linux-y-terminal/02-bash-y-comandos.md) | `grep`, `find`, `ssh`, `curl`, pipes, redirección, scripts |
| [03 — Herramientas de terminal](./linux-y-terminal/03-herramientas-terminal.md) | `tmux`, `vim`, `htop`, `netstat`, `lsof`, debugging de procesos |

---

### [Redes y Protocolos](./redes-y-protocolos/)

Lo que ocurre bajo el nivel de tu aplicación. Indispensable para debuggear problemas reales de producción y diseñar APIs correctamente.

| Archivo | Contenido |
|---------|----------|
| [01 — Fundamentos de redes](./redes-y-protocolos/01-fundamentos-redes.md) | Modelo OSI, TCP/IP, puertos, DNS, routing básico |
| [02 — HTTP y HTTPS](./redes-y-protocolos/02-http-y-https.md) | Métodos, headers, status codes, TLS/SSL, cookies, sessions |
| [03 — REST y diseño de APIs](./redes-y-protocolos/03-rest-y-diseno-apis.md) | Principios REST, JSON, versioning, idempotencia, HATEOAS |
| [04 — Otros protocolos](./redes-y-protocolos/04-otros-protocolos.md) | WebSockets, gRPC, GraphQL intro, SSH |

---

### [Ingeniería de Software](./ingenieria-de-software/)

Los principios que separan el código que funciona del código que escala y se puede mantener.

| Archivo | Contenido |
|---------|----------|
| [01 — Principios](./ingenieria-de-software/01-principios.md) | DRY, YAGNI, KISS, SOLID intro, OWASP Top 10 |
| [02 — Metodologías ágiles](./ingenieria-de-software/02-metodologias-agiles.md) | Agile, Scrum, Kanban, sprints, retrospectivas |
| [03 — Ciclo de vida](./ingenieria-de-software/03-ciclo-de-vida.md) | SDLC, requerimientos, diseño, release, post-mortem |
| [04 — Spec-Driven Development](./ingenieria-de-software/04-spec-driven-development.md) | OpenAPI-first, contract testing, mocks desde spec |

---

## Orden de estudio recomendado

```
linux-y-terminal/ → redes-y-protocolos/ → ingenieria-de-software/
```

Las sub-áreas son independientes entre sí, pero el orden anterior es el más natural: primero dominas el entorno donde vas a trabajar, luego entiendes cómo se comunican los sistemas, luego aprendes los principios de cómo deberían estar construidos.

---

**Navegación**  
[← Volver al inicio](../README.md) · [Linux y Terminal →](./linux-y-terminal/README.md)
