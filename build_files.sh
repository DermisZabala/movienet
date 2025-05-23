#!/bin/bash

echo "Building project..."

# Instalar dependencias si es necesario (Vercel suele hacerlo desde requirements.txt)
# pip install -r requirements.txt # Comentado, Vercel lo hace

# Crear directorio para archivos estáticos si no existe
mkdir -p staticfiles_build/static

# Instalar dependencias de Python
echo "Installing Python dependencies..."
pip3 install -r requirements.txt # O solo pip si python3 es el default en el builder


# Ejecutar collectstatic
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear # <--- CAMBIO PRINCIPAL AQUÍ


# (Opcional) Ejecutar migraciones si tu base de datos lo permite en el build.
# A menudo es mejor ejecutar migraciones como un paso separado o a través de la consola de tu proveedor de DB.
# echo "Applying database migrations..."
# python manage.py migrate --noinput

echo "Build finished."