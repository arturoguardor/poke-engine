from django.conf import settings
from django.test import override_settings


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


@override_settings(DEBUG=True, ALLOWED_HOSTS=["*"])
def test_settings_can_be_overridden_explicitly():
    """El modo dev explícito (DEBUG=True, ALLOWED_HOSTS=*) sigue siendo posible."""
    assert settings.DEBUG is True
    assert settings.ALLOWED_HOSTS == ["*"]
