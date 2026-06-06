#!/bin/bash
set -e

# Fix ownership of volume-mounted directories (runs as root at container start)
chown -R appuser:appuser /app/staticfiles /app/media 2>/dev/null || true

# Drop to appuser and re-execute this script
if [ "$(id -u)" = "0" ]; then
    exec gosu appuser "$0" "$@"
fi

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if not exists..."
DJANGO_SUPERUSER_PASSWORD="${DJANGO_ADMIN_PASSWORD}" \
    python manage.py createsuperuser \
    --noinput \
    --username admin \
    --email admin@example.com 2>/dev/null || echo "Superuser already exists"

if [ -f /app/data/houses.csv ]; then
    echo "Checking if house data needs importing..."
    python manage.py shell -c "
from houses.models import House
if House.objects.count() == 0:
    from django.core.management import call_command
    call_command('import_houses', '/app/data/houses.csv')
    print('House data imported from CSV')
else:
    print('House data already exists, skipping import')
"
else
    echo "No default CSV data found at /app/data/houses.csv, skipping auto-import."
    echo "To import data later: docker compose exec backend python manage.py import_houses <csv_path>"
fi

echo "Checking ML model files..."
python manage.py shell -c "
import os
from django.conf import settings
model_path = os.path.join(settings.ML_MODEL_DIR, 'house_price_model.pkl')
preprocessor_path = os.path.join(settings.ML_MODEL_DIR, 'preprocessor.pkl')
if not os.path.exists(model_path) or not os.path.exists(preprocessor_path):
    print('WARNING: ML model files not found. Prediction API will not work.')
    print('To train: docker compose exec backend python ml/train.py')
else:
    print('ML model files found.')
"

exec "$@"
