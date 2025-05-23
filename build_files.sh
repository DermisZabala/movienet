#!/bin/bash

echo "Building project..."

# Instalar dependencias si es necesario (Vercel suele hacerlo desde requirements.txt)
# pip install -r requirements.txt # Comentado, Vercel lo hace

# Crear directorio para archivos estáticos si no existe
mkdir -p staticfiles_build/static

# Ejecutar collectstatic
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# (Opcional) Ejecutar migraciones si tu base de datos lo permite en el build.
# A menudo es mejor ejecutar migraciones como un paso separado o a través de la consola de tu proveedor de DB.
# echo "Applying database migrations..."
# python manage.py migrate --noinput

echo "Build finished."