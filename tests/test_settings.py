from django.conf import settings


def test_settings_defaults_are_safe():
    """Sin .env ni variables de entorno, los defaults deben ser seguros.

    pytest-django añade 'testserver' a ALLOWED_HOSTS automáticamente durante
    la ejecución de tests (setup_test_environment), así que no se asume una
    lista exacta; se verifican las garantías de seguridad:
    - DEBUG es False
    - localhost y 127.0.0.1 están permitidos
    - el comodín '*' NO está permitido
    """
    assert settings.DEBUG is False
    assert "localhost" in settings.ALLOWED_HOSTS
    assert "127.0.0.1" in settings.ALLOWED_HOSTS
    assert "*" not in settings.ALLOWED_HOSTS


def test_env_vars_still_enable_dev_mode(tmp_path):
    """Una variable de entorno explícita sigue activando el modo desarrollo.

    Endurecer los defaults no puede romper el flujo local ni el de Docker, que
    pasan DEBUG=True por entorno. Se ejercita en un proceso aparte con el
    entorno preparado: es el único modo de probar que `config()` lee de verdad
    la variable.

    La versión anterior usaba @override_settings(DEBUG=True) y despues afirmaba
    que DEBUG era True — comprobaba el decorador de Django, no este proyecto, y
    habría pasado igual con settings.py revertido.

    El subproceso corre en un directorio temporal, no en la raíz del proyecto:
    `python-decouple` lee el `.env` del directorio de trabajo, así que un `.env`
    local del desarrollador podría ganarle a las variables que este test declara
    y hacerlo fallar de forma intermitente. `PYTHONPATH` apunta a la raíz para
    que `config.settings` siga siendo importable desde fuera.
    """
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    entorno = {
        **os.environ,
        "DEBUG": "True",
        "ALLOWED_HOSTS": "*",
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "PYTHONPATH": str(raiz),
    }
    resultado = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, django; django.setup();"
            "from django.conf import settings;"
            "print(json.dumps([settings.DEBUG, settings.ALLOWED_HOSTS]))",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=entorno,
    )
    assert resultado.returncode == 0, resultado.stderr
    # Se compara el valor exacto, no una subcadena: con `"*" in stdout` una
    # salida como ['*', 'otro'] pasaría igual.
    debug, allowed_hosts = json.loads(resultado.stdout)
    assert debug is True
    assert allowed_hosts == ["*"]
