"""
Django settings for web_peliculas_series_anime project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv # Para leer .env localmente
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env (SOLO PARA DESARROLLO LOCAL)
# En Vercel, las variables de entorno se configuran en el dashboard de Vercel.
# Comprueba si estamos en un entorno de Vercel para evitar cargar .env en producción
# VERCEL_ENV es una variable de entorno que Vercel define.
# Puedes usar una variable propia como IS_PRODUCTION si prefieres.
if not os.environ.get('VERCEL_ENV') == 'production':
    load_dotenv(BASE_DIR / '.env')


# Logging (ya lo tienes, está bien para empezar)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} [{name}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'), # Controla el nivel de log con una variable
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO', # Menos verboso para Django en producción
            'propagate': False,
        },
    },
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-gm43%hnrhr46nchk!76u=y^#c*si!tqv-t_mg9wy5^5cn(uv6x') # Fallback para desarrollo

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS_STRING = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(',') if ALLOWED_HOSTS_STRING else []
# En Vercel, también querrás añadir tu dominio de Vercel aquí.
# Vercel suele añadirlo automáticamente, o puedes poner '.vercel.app' si es necesario.


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Para servir estáticos en desarrollo sin `collectstatic` siempre
    'django.contrib.staticfiles',
    'catalogo', # Tu aplicación
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Whitenoise, después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web_peliculas_series_anime.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [BASE_DIR / 'catalogo/templates'], # Django buscará en app/templates/ por defecto si APP_DIRS es True
        'DIRS': [BASE_DIR / 'templates'], # Si tienes una carpeta 'templates' a nivel de proyecto
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'web_peliculas_series_anime.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Para Vercel, necesitarás una DB externa. SQLite no es persistente.
# Ejemplo con dj_database_url para leer DATABASE_URL de las variables de entorno de Vercel
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:

    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600, # Tiempo de vida de la conexión
            ssl_require=True if os.environ.get('VERCEL_ENV') == 'production' else False # SSL para DBs de producción
        )
    }
else: # Fallback a SQLite para desarrollo local si DATABASE_URL no está configurada
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# ... (mantenlos como están)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/' # URL para referenciar archivos estáticos en plantillas
STATICFILES_DIRS = [
    BASE_DIR / "catalogo" / "static", # Si tienes estáticos a nivel de app que quieres que se encuentren
                                      # o una carpeta 'static' global a nivel de proyecto
    # BASE_DIR / "static", # Descomenta si tienes una carpeta 'static' en la raíz del proyecto
]
# Directorio donde `collectstatic` copiará todos los archivos estáticos para producción.
STATIC_ROOT = BASE_DIR / "staticfiles_build" / "static"

# Configuración de Whitenoise para compresión y caché inmutable
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configuración para envío de Email (Reporte de Enlaces) ---
# Lee estas configuraciones desde variables de entorno en producción
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend') # Console para desarrollo
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('DJANGO_EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'webmaster@localhost')

# URLs de los JSON (Mantenidas como variables de entorno o directamente si son fijas)
# Es mejor poner estas en variables de entorno si pueden cambiar o son sensibles.
# Si son públicas y fijas, está bien tenerlas aquí.
JSON_PELICULAS_URL = 'https://raw.githubusercontent.com/DermisZabala/jsonMovieNet/refs/heads/main/peliculas.json'
JSON_SERIES_URL = 'https://raw.githubusercontent.com/DermisZabala/jsonMovieNet/refs/heads/main/series.json'
JSON_ANIME_URL = 'https://raw.githubusercontent.com/DermisZabala/jsonMovieNet/refs/heads/main/anime.json'

# --- Configuraciones de Seguridad para Producción ---
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False').lower() == 'true'

# Para HSTS (solo si estás seguro y tu sitio siempre usará HTTPS)
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', 0)) # Ej: 31536000 para 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_SECURE_HSTS_PRELOAD', 'False').lower() == 'true'

# Si Vercel (o cualquier proxy) maneja HTTPS y reenvía como HTTP
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')