#!/bin/bash

echo "Building project..."

# Instalar dependencias de Python ANTES de cualquier comando de manage.py
echo "Installing Python dependencies..."
pip3 install -r requirements.txt # Usamos pip3 para ser explícitos

# (Opcional) Crear directorio para archivos estáticos si no existe.
# Django/collectstatic generalmente crea la estructura de STATIC_ROOT,
# así que esta línea puede ser redundante o incluso innecesaria.
# Si tienes problemas, prueba comentándola.
# mkdir -p staticfiles_build/static

# Ejecutar collectstatic usando python3
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

# (Comentado - Opcional) Ejecutar migraciones si tuvieras una base de datos persistente
# y si es seguro ejecutarlo en el build.
# echo "Applying database migrations..."
# python3 manage.py migrate --noinput

echo "Build finished."