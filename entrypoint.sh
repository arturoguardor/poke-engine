#!/bin/sh
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Cargando fixture de type_effectiveness..."
python manage.py loaddata fixtures/type_effectiveness.json

exec "$@"
