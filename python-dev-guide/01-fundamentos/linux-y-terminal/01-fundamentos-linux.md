# Fundamentos de Linux

> Linux es el sistema operativo que corre el 96% de los servidores del mundo. No importa si desarrollas en Mac o Windows — tu código vive en Linux. Entenderlo no es opcional.

**Área:** `01-fundamentos/linux-y-terminal` · **Nivel:** Fundamentos → Intermedio · **Lectura activa:** ~20 min

---

> [!IMPORTANT]
> **Al terminar este archivo deberías poder:**
> - Navegar el sistema de archivos de Linux sin pensar
> - Gestionar permisos, usuarios y grupos con `chmod`, `chown` y `chgrp`
> - Entender qué es un proceso, cómo verlo y cómo terminarlo
> - Usar variables de entorno para configurar aplicaciones

<details>
<summary>Tabla de contenidos</summary>

- [El sistema de archivos Linux](#el-sistema-de-archivos-linux)
- [Permisos](#permisos)
- [Usuarios y grupos](#usuarios-y-grupos)
- [Procesos](#procesos)
- [Variables de entorno](#variables-de-entorno)
- [Errores comunes](#errores-comunes)
- [Referencias](#referencias)

</details>

---

## El sistema de archivos Linux

> [!TIP]
> **Pausa antes de leer.** En Windows los archivos se organizan por discos (`C:\`, `D:\`). En Linux todo es un árbol que empieza en `/`. ¿Qué consecuencias crees que tiene esa diferencia de diseño?

Linux sigue la filosofía de que **todo es un archivo** — incluyendo dispositivos, procesos y conexiones de red. La estructura estándar es el *Filesystem Hierarchy Standard* (FHS):

```
/
├── bin/        # Binarios esenciales del sistema (ls, cp, mv, bash)
├── etc/        # Archivos de configuración del sistema
├── home/       # Directorios de usuarios (/home/arturo, /home/ubuntu)
├── root/       # Directorio del usuario root
├── var/        # Datos variables: logs, caches, bases de datos
│   └── log/    # Logs del sistema y aplicaciones
├── tmp/        # Archivos temporales (se borran al reiniciar)
├── usr/        # Programas instalados por el usuario
│   ├── bin/    # Binarios de usuario (python3, git, curl)
│   └── lib/    # Librerías compartidas
├── opt/        # Software de terceros (no gestionado por el gestor de paquetes)
├── proc/       # Sistema de archivos virtual — estado del kernel y procesos
├── dev/        # Dispositivos de hardware (discos, terminales)
└── mnt/        # Puntos de montaje para sistemas de archivos externos
```

> [!NOTE]
> **Conexión con Python.** Cuando una aplicación Django escribe logs, los escribe en `/var/log/`. Cuando configuras `DJANGO_SETTINGS_MODULE` como variable de entorno, vive en `/proc/[pid]/environ`. No son conceptos separados — el sistema operativo y tu aplicación conviven aquí.

### Comandos de navegación esenciales

```bash
# Ver dónde estás
pwd

# Listar contenido (l = long format, a = hidden files, h = human-readable sizes)
ls -lah

# Moverse entre directorios
cd /var/log          # ruta absoluta (desde raíz)
cd ../..             # ruta relativa (dos niveles arriba)
cd ~                 # ir al home del usuario actual
cd -                 # volver al directorio anterior

# Ver el árbol de directorios
tree -L 2            # profundidad 2 (instalar con: apt install tree)

# Crear y eliminar
mkdir -p proyectos/api/v1   # crea directorios anidados
rm -rf directorio/           # elimina recursivamente (¡sin confirmación!)
cp -r origen/ destino/       # copiar recursivamente
mv archivo.txt nuevo_nombre.txt  # mover o renombrar
```

> [!WARNING]
> **`rm -rf` no tiene papelera de reciclaje.** En producción, un `rm -rf /` con los permisos correctos borra el sistema completo. Verifica siempre la ruta antes de ejecutar comandos destructivos.

---

## Permisos

> [!TIP]
> **Pausa.** Tienes un archivo Python. ¿Quién debería poder leerlo? ¿Quién debería poder ejecutarlo? ¿Tiene sentido que cualquier usuario del sistema pueda modificarlo? Piénsalo antes de leer la siguiente sección.

Linux usa un sistema de permisos de **tres niveles**: propietario, grupo y otros.

```bash
ls -l archivo.py
# -rwxr-xr-- 1 arturo developers 1234 Apr 16 10:30 archivo.py
#  │││││││││
#  ││││││││└── otros: r-- (solo lectura)
#  │││││└──── grupo: r-x (lectura y ejecución)
#  ││└──────── propietario: rwx (lectura, escritura, ejecución)
#  │└───────── tipo: - archivo, d directorio, l symlink
```

Los permisos se representan en octal:

| Permiso | Símbolo | Valor octal |
|---------|---------|-------------|
| Lectura | `r` | 4 |
| Escritura | `w` | 2 |
| Ejecución | `x` | 1 |
| Ninguno | `-` | 0 |

```bash
# Cambiar permisos con modo octal
chmod 755 script.py    # rwxr-xr-x  (propietario: 7=4+2+1, grupo: 5=4+1, otros: 5=4+1)
chmod 644 config.ini   # rw-r--r--  (propietario: 6=4+2, grupo: 4, otros: 4)
chmod 600 .env         # rw-------  solo el propietario puede leer/escribir

# Cambiar permisos con modo simbólico
chmod u+x script.py    # agregar ejecución al propietario (user)
chmod g-w archivo.txt  # quitar escritura al grupo
chmod o-r secreto.key  # quitar lectura a otros

# Cambiar propietario y grupo
chown arturo archivo.py
chown arturo:developers archivo.py
chgrp developers directorio/

# Aplicar recursivamente a un directorio
chmod -R 755 mi_proyecto/
chown -R www-data:www-data /var/www/html/
```

### Permisos en aplicaciones Python

```python
import os
import stat

# Ver los permisos de un archivo
file_path = "/etc/app/config.json"
mode = os.stat(file_path).st_mode

# Verificar si es legible por el propietario
is_owner_readable = bool(mode & stat.S_IRUSR)
is_owner_writable = bool(mode & stat.S_IWUSR)

print(f"Readable by owner: {is_owner_readable}")
print(f"Writable by owner: {is_owner_writable}")

# Cambiar permisos desde Python
os.chmod("/app/.env", stat.S_IRUSR | stat.S_IWUSR)  # 600
```

> [!NOTE]
> **Analiza esto.** En el ejemplo anterior configuramos `.env` con `600` — solo el propietario puede leer y escribir. ¿Por qué tiene sentido este permiso para un archivo de configuración con secretos? ¿Qué pasaría si fuera `644`?

---

## Usuarios y grupos

Linux es multiusuario. Cada proceso corre bajo la identidad de un usuario con permisos específicos.

```bash
# Ver el usuario actual
whoami
id             # uid=1000(arturo) gid=1000(arturo) groups=1000(arturo),27(sudo),999(docker)

# Ver todos los usuarios del sistema
cat /etc/passwd | cut -d: -f1

# Cambiar de usuario
su - arturo         # login completo como arturo
sudo command        # ejecutar un comando como root

# Gestión de usuarios (requiere sudo)
useradd -m -s /bin/bash nuevo_usuario   # crear usuario con home y shell
passwd nuevo_usuario                    # establecer contraseña
usermod -aG docker arturo               # agregar arturo al grupo docker
userdel -r usuario_a_eliminar           # eliminar usuario y su home
```

### El usuario `www-data`

En servidores web (Nginx, Apache), los procesos corren como el usuario `www-data` (o `nginx`). Entender esto es crítico para configurar permisos en aplicaciones Django/FastAPI:

```bash
# Configuración típica de permisos para una app Django en producción
chown -R www-data:www-data /var/www/mi_proyecto/
chmod -R 755 /var/www/mi_proyecto/
chmod -R 750 /var/www/mi_proyecto/media/    # media files: solo propietario y grupo
chmod 600 /var/www/mi_proyecto/.env         # secretos: solo propietario
```

---

## Procesos

> [!TIP]
> **Pausa.** Cuando ejecutas `python manage.py runserver`, ¿cuántos procesos se crean? ¿Qué pasa si el proceso usa demasiada memoria? ¿Cómo lo matarías sin reiniciar el servidor?

Un proceso es un programa en ejecución con su propio espacio de memoria, identificador (PID) y estado.

```bash
# Ver todos los procesos
ps aux

# Ver procesos en tiempo real (q para salir)
top
htop          # versión mejorada, instalar con: apt install htop

# Filtrar procesos
ps aux | grep python
ps aux | grep gunicorn

# Ver el árbol de procesos
pstree -p

# Encontrar el PID de un proceso por nombre
pgrep -f "manage.py"
pidof nginx
```

### Señales de proceso

Las señales son la forma de comunicarse con procesos en ejecución:

```bash
# Terminar un proceso (le da tiempo para limpiar)
kill -15 1234       # SIGTERM — terminación elegante
kill -TERM 1234     # equivalente

# Forzar terminación inmediata (sin cleanup)
kill -9 1234        # SIGKILL — no se puede ignorar
kill -KILL 1234     # equivalente

# Recargar configuración sin reiniciar (para Nginx, Gunicorn, etc.)
kill -1 $(pidof nginx)    # SIGHUP — recarga configuración
kill -HUP $(pidof nginx)  # equivalente

# Enviar señal a todos los procesos con ese nombre
pkill -f "gunicorn"
killall nginx
```

```mermaid
stateDiagram-v2
    [*] --> Creado: fork() / exec()
    Creado --> Ejecutando: scheduler del kernel
    Ejecutando --> Bloqueado: espera I/O, sleep()
    Bloqueado --> Ejecutando: I/O completado
    Ejecutando --> Zombie: exit() - esperando al padre
    Zombie --> [*]: padre lee el exit code (wait())
    Ejecutando --> [*]: kill -9
```

> [!NOTE]
> **Analiza el diagrama.** Un proceso zombie existe porque el padre no ha "recogido" su exit code. En aplicaciones Django con Gunicorn, ¿quién es el proceso padre? ¿Qué pasa si Gunicorn no gestiona bien sus workers?

### Monitoreo de recursos

```bash
# Uso de CPU y memoria en tiempo real
top -b -n 1 | head -20   # snapshot único (útil en scripts)

# Uso de disco
df -h                    # espacio por filesystem
du -sh /var/log/*        # tamaño de cada directorio en /var/log

# Memoria disponible
free -h

# Procesos que más recursos consumen
ps aux --sort=-%cpu | head -10   # top 10 por CPU
ps aux --sort=-%mem | head -10   # top 10 por memoria

# Ver archivos abiertos por un proceso
lsof -p 1234
lsof -i :8000    # qué proceso está escuchando en el puerto 8000
```

---

## Variables de entorno

Las variables de entorno son la forma estándar de configurar aplicaciones sin hardcodear valores en el código.

```bash
# Ver todas las variables de entorno
env
printenv

# Ver una variable específica
echo $HOME
echo $PATH

# Definir una variable (solo en la sesión actual)
export DATABASE_URL="postgresql://user:pass@localhost/mydb"
export DEBUG=True

# Definir variable solo para un comando
DATABASE_URL="postgresql://..." python manage.py migrate

# Persistir variables para todas las sesiones
echo 'export PYTHONPATH=/home/arturo/projects' >> ~/.bashrc
source ~/.bashrc   # recargar sin reiniciar la terminal
```

### Variables de entorno en Python

```python
import os
from pathlib import Path

# Leer una variable de entorno
db_url = os.environ.get("DATABASE_URL")

# Leer con valor por defecto
debug = os.environ.get("DEBUG", "false").lower() == "true"
port = int(os.environ.get("PORT", "8000"))

# Leer y lanzar error si no existe
secret_key = os.environ["SECRET_KEY"]  # KeyError si no existe

# Ejemplo: configuración de Django cargada desde el entorno
settings = {
    "DATABASE_URL": os.environ["DATABASE_URL"],
    "SECRET_KEY": os.environ["SECRET_KEY"],
    "DEBUG": os.environ.get("DEBUG", "false") == "true",
    "ALLOWED_HOSTS": os.environ.get("ALLOWED_HOSTS", "localhost").split(","),
}
```

### El archivo `.env`

La convención es guardar las variables en un archivo `.env` que nunca se sube al repositorio:

```bash
# .env (nunca en git — agregar al .gitignore)
DATABASE_URL=postgresql://arturo:password123@localhost:5432/mydb
SECRET_KEY=django-insecure-xyz...
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
REDIS_URL=redis://localhost:6379/0
```

```python
# Cargar .env con python-dotenv
from dotenv import load_dotenv

load_dotenv()  # carga .env desde el directorio actual

# Ahora las variables están disponibles en os.environ
import os
print(os.environ["DATABASE_URL"])
```

> [!CAUTION]
> **Nunca incluyas el archivo `.env` en el repositorio.** Agrega `*.env` y `.env*` a tu `.gitignore`. Si accidentalmente subes secretos a GitHub, debes rotarlos inmediatamente — git history es público y permanente.

---

## Errores comunes

- [x] **`Permission denied` al ejecutar un script**: El archivo no tiene permiso de ejecución. Solución: `chmod +x script.py` o ejecutarlo explícitamente con `python script.py`.

- [x] **Proceso que no responde a `kill -15`**: El proceso está capturando SIGTERM. Usa `kill -9` como último recurso, pero el proceso no tendrá oportunidad de cerrar conexiones de base de datos o escribir logs.

- [x] **Variable de entorno que "desaparece"**: Un `export` en la terminal solo aplica a la sesión actual. Si abres una nueva terminal, la variable no existe. Para persistir, agrega el `export` a `~/.bashrc` o `~/.zshrc`.

- [x] **`No such file or directory` con rutas absolutas que existen**: El problema puede ser una diferencia de permisos (el usuario que ejecuta el script no puede leer ese directorio), no que el archivo no exista. Verifica con `ls -la` en el directorio padre.

- [x] **Zona zombie de procesos en producción**: Generalmente indica que el proceso padre (supervisor, systemd, gunicorn master) no está haciendo `wait()` correctamente. Revisar la configuración del supervisor del proceso.

---

## Referencias

### Antes de comenzar — contexto previo
> Lee esto si no tienes experiencia previa con Linux o sistemas Unix.
- [The Linux Command Line](https://linuxcommand.org/tlcl.php) — William Shotts. Capítulos 1–6: navegación, archivos y permisos (~45 min). Disponible gratis online.

### Durante el estudio — referencia activa
> Mantén esto abierto mientras practicas los comandos.
- [GNU Coreutils Manual](https://www.gnu.org/software/coreutils/manual/html_node/index.html#Top) — documentación oficial de `ls`, `chmod`, `chown`, `cp`, `mv`, etc. Busca el comando específico que necesites.
- [Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html) — referencia oficial de Bash. Secciones 3 (Basic Shell Features) y 6 (Bash Features).

### Para profundizar — después de dominar el tema
> Una vez que te muevas con fluidez en la terminal, estos recursos van más allá.
- **The Linux Programming Interface** — Michael Kerrisk (No Starch Press, 2010) — Cap. 9 (Process Credentials) y Cap. 15 (File Attributes). El libro de referencia definitivo del kernel Linux. [pago]
- [Linux Filesystem Hierarchy](https://tldp.org/LDP/Linux-Filesystem-Hierarchy/html/) — The Linux Documentation Project. Lectura completa (~20 min): explica el propósito de cada directorio estándar.
- [cheatsnake/backend-cheats](https://github.com/cheatsnake/backend-cheats) — sección "Linux" con diagramas visuales de permisos y procesos.

---

**Navegación**  
[← Volver a Linux y Terminal](./README.md) · [02 — Bash y comandos →](./02-bash-y-comandos.md)
